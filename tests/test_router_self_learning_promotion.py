"""Tests for M3 (promotion gate + active pointer) and M4 (auto-rollback)."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

from openstarry_code.gateway.config import RouterSelfLearningConfig, SquillaRouterConfig
from openstarry_code.squilla_router.self_learning import encode_features, write_sample
from openstarry_code.squilla_router.self_learning.dataset import TrainingDataset
from openstarry_code.squilla_router.self_learning.evaluate import (
    decide_promotion,
    route_metrics,
    session_holdout_splits,
)
from openstarry_code.squilla_router.self_learning.orchestrator import (
    in_process_trainer,
    maybe_run_update_router,
)
from openstarry_code.squilla_router.self_learning.promotion import (
    learned_bundle_dir,
    promote_candidate,
    quarantine_candidate,
    read_active,
    resolve_active_bundle_dir,
    rollback_active,
    should_rollback,
    write_active_atomic,
)
from openstarry_code.squilla_router.self_learning.schema import RouterTrainSample
from openstarry_code.squilla_router.self_learning.state import (
    TrainState,
    load_train_state,
    save_train_state,
)

NOW = datetime(2026, 6, 6, 12, 0, 0, tzinfo=UTC)


def _cfg(**kw) -> RouterSelfLearningConfig:
    base = dict(
        enabled=True,
        train_min_samples=4,
        idle_hours=2.0,
        cooldown_hours=72.0,
        holdout_min_size=4,
        holdout_pct=0.4,
        holdout_repeats=2,
        max_critical_under_routing=0.5,
        cost_tolerance_pct=25.0,
    )
    base.update(kw)
    return RouterSelfLearningConfig(**base)


# --------------------------------------------------------------------------- #
# Active pointer primitives
# --------------------------------------------------------------------------- #


def test_active_pointer_defaults_to_baseline(tmp_path) -> None:
    assert read_active(tmp_path) == "baseline"
    assert resolve_active_bundle_dir(tmp_path) is None


def test_promote_and_resolve(tmp_path) -> None:
    bundle = learned_bundle_dir("v1-x", tmp_path)
    bundle.mkdir(parents=True)
    (bundle / "lgbm_main.bin").write_text("model", encoding="utf-8")
    prev = promote_candidate("v1-x", tmp_path)
    assert prev == "baseline"
    assert read_active(tmp_path) == "learned/v1-x"
    assert resolve_active_bundle_dir(tmp_path) == bundle


def test_resolve_falls_back_when_bundle_incomplete(tmp_path) -> None:
    write_active_atomic("learned/ghost", tmp_path)  # no such bundle on disk
    assert resolve_active_bundle_dir(tmp_path) is None


def test_rollback_reverts_to_baseline(tmp_path) -> None:
    write_active_atomic("learned/v1-x", tmp_path)
    prev = rollback_active(tmp_path)
    assert prev == "learned/v1-x"
    assert read_active(tmp_path) == "baseline"


def test_quarantine_moves_bundle_out(tmp_path) -> None:
    bundle = learned_bundle_dir("v1-x", tmp_path)
    bundle.mkdir(parents=True)
    (bundle / "lgbm_main.bin").write_text("m", encoding="utf-8")
    dest = quarantine_candidate("v1-x", tmp_path)
    assert dest is not None and dest.exists()
    assert not bundle.exists()


def test_should_rollback_rules() -> None:
    cfg = _cfg(min_monitor_samples=10, complaint_regression_delta=0.05)
    # regression beyond delta with enough samples -> rollback
    assert should_rollback(pre_complaint_rate=0.1, post_complaint_rate=0.3, post_n=20, config=cfg)
    # not enough samples yet
    assert not should_rollback(
        pre_complaint_rate=0.1, post_complaint_rate=0.9, post_n=5, config=cfg
    )
    # within delta
    assert not should_rollback(
        pre_complaint_rate=0.1, post_complaint_rate=0.12, post_n=50, config=cfg
    )
    # no baseline recorded
    assert not should_rollback(
        pre_complaint_rate=None, post_complaint_rate=0.9, post_n=50, config=cfg
    )
    # auto_rollback disabled
    off = _cfg(auto_rollback=False)
    assert not should_rollback(
        pre_complaint_rate=0.0, post_complaint_rate=0.9, post_n=99, config=off
    )


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #


def test_route_metrics_basic() -> None:
    pred = np.array([1, 2, 0, 3])
    target = np.array([1, 3, 0, 3])  # under-routes the 2nd (pred 2 < target 3)
    served = np.array([1, 1, 0, 3])
    m = route_metrics(pred, target, served)
    assert m.n == 4
    assert m.agreement == 0.75
    # critical = target>=2 -> indices 1,3; pred<target only at idx1 -> 0.5
    assert m.critical_under_routing_rate == 0.5


def test_holdout_splits_are_session_whole_and_floored(tmp_path) -> None:
    ds = TrainingDataset(
        X=np.zeros((10, 390), np.float32),
        y=np.zeros(10, np.int64),
        w=np.ones(10, np.float32),
        session_keys=[f"s{i % 2}" for i in range(10)],  # 2 sessions
    )
    splits = session_holdout_splits(ds, holdout_pct=0.4, repeats=2, min_size=2)
    assert splits
    for train_idx, hold_idx in splits:
        # no session appears on both sides
        train_sessions = {ds.session_keys[i] for i in train_idx}
        hold_sessions = {ds.session_keys[i] for i in hold_idx}
        assert not (train_sessions & hold_sessions)
    # too few sessions -> no splits
    single = TrainingDataset(
        X=np.zeros((4, 390), np.float32),
        y=np.zeros(4, np.int64),
        w=np.ones(4, np.float32),
        session_keys=["s0"] * 4,
    )
    assert session_holdout_splits(single, holdout_pct=0.4, repeats=2, min_size=2) == []


def test_decide_promotion_paths() -> None:
    cfg = _cfg(holdout_min_size=4, max_critical_under_routing=0.3, cost_tolerance_pct=10.0)
    good_cv = {
        "agreement": 0.9,
        "critical_under_routing_rate": 0.1,
        "mean_pred_idx": 1.0,
        "served_mean_idx": 1.0,
        "n_holdout": 20,
    }
    assert decide_promotion(good_cv, golden=None, baseline_golden=None, config=cfg).promote
    # quality regression
    bad_q = {**good_cv, "critical_under_routing_rate": 0.6}
    d = decide_promotion(bad_q, golden=None, baseline_golden=None, config=cfg)
    assert not d.promote and "quality_regression" in d.reason
    # cost regression (predicts much higher than served)
    bad_c = {**good_cv, "mean_pred_idx": 2.5, "served_mean_idx": 1.0}
    d = decide_promotion(bad_c, golden=None, baseline_golden=None, config=cfg)
    assert not d.promote and "cost_regression" in d.reason
    # insufficient eval (no cv, no golden)
    empty = {"agreement": None, "n_holdout": 0, "served_mean_idx": 0.0}
    assert decide_promotion(empty, golden=None, baseline_golden=None, config=cfg).reason == (
        "insufficient_eval"
    )


# --------------------------------------------------------------------------- #
# Strategy integration (cache)
# --------------------------------------------------------------------------- #


def test_invalidate_strategy_cache(monkeypatch) -> None:
    from openstarry_code.engine.steps import squilla_router as step

    step._strategy = object()
    step._strategy_key = ("x",)
    step.invalidate_strategy_cache()
    assert step._strategy is None and step._strategy_key is None


def test_cache_key_tracks_active_bundle(monkeypatch) -> None:
    from openstarry_code.engine.steps import squilla_router as step

    cfg = SquillaRouterConfig(self_learning=_cfg())
    monkeypatch.setattr(step, "_active_bundle_dir", lambda _c: "learned/v1")
    key1 = step._strategy_cache_key(cfg)
    monkeypatch.setattr(step, "_active_bundle_dir", lambda _c: "learned/v2")
    key2 = step._strategy_cache_key(cfg)
    assert key1 != key2


def test_active_bundle_dir_none_when_disabled() -> None:
    from openstarry_code.engine.steps import squilla_router as step

    cfg = SquillaRouterConfig(self_learning=RouterSelfLearningConfig(enabled=False))
    assert step._active_bundle_dir(cfg) is None


# --------------------------------------------------------------------------- #
# Orchestrator: promote / reject / rollback
# --------------------------------------------------------------------------- #


def _write_separable_store(tmp_path, agent="agp", n=36) -> None:
    """Confidence-gate (high-value) turns with features cleanly separable by
    final class, so CV agreement is high and cost does not regress.

    Across 3 sessions this leaves each whole-session holdout fold ~12 training
    rows (6 per class) — enough for LightGBM to split past ``min_data_in_leaf``.
    """
    rng = np.random.RandomState(1)
    for i in range(n):
        cls = i % 2  # 0 -> R1, 1 -> R2
        fc = "R2" if cls else "R1"
        feats = (rng.randn(390) * 0.1).astype(np.float32)
        feats[0] = 5.0 if cls else -5.0
        write_sample(
            RouterTrainSample(
                session_key=f"s{i % 3}",
                turn_index=i,
                ts=f"2026-06-01T00:00:{i:02d}Z",
                feature_schema_version="v1",
                features_390_b64=encode_features(feats),
                route_class=fc,
                final_route_class=fc,
                routed_tier="c2" if cls else "c1",
                confidence_gate_applied=True,
            ),
            agent,
            home=tmp_path,
        )


def test_orchestrator_promotes_good_candidate(tmp_path) -> None:
    pytest.importorskip("lightgbm")
    base = tmp_path / "base"
    base.mkdir()
    (base / "router.runtime.yaml").write_text("k: v\n", encoding="utf-8")
    _write_separable_store(tmp_path)

    res = maybe_run_update_router(
        "agp",
        router_cfg=SquillaRouterConfig(self_learning=_cfg()),
        home=tmp_path,
        now=NOW,
        trainer=in_process_trainer,
        base_dir=base,
    )
    assert res.ran and res.promoted and res.reason == "promoted", res
    assert read_active(tmp_path) == f"learned/{res.version}"
    state = load_train_state("agp", tmp_path)
    assert state.active_version == res.version
    assert state.promoted_at is not None
    assert list((tmp_path / "router" / ".receipts").glob("agp-*-promoted.json"))


def test_orchestrator_rejects_on_golden_floor(tmp_path) -> None:
    pytest.importorskip("lightgbm")
    base = tmp_path / "base"
    base.mkdir()
    (base / "router.runtime.yaml").write_text("k: v\n", encoding="utf-8")
    _write_separable_store(tmp_path, agent="agr")

    # Golden set whose labels contradict the separable signal -> low agreement.
    rng = np.random.RandomState(2)
    gx = (rng.randn(20, 390) * 0.1).astype(np.float32)
    gy = np.zeros(20, np.int64)
    for i in range(20):
        gx[i, 0] = 5.0 if i % 2 else -5.0
        gy[i] = 0 if i % 2 else 2  # inverted vs training signal
    golden = tmp_path / "golden.npz"
    np.savez(golden, X=gx, y=gy)

    res = maybe_run_update_router(
        "agr",
        router_cfg=SquillaRouterConfig(
            self_learning=_cfg(golden_eval_path=str(golden), min_golden_agreement=0.9)
        ),
        home=tmp_path,
        now=NOW,
        trainer=in_process_trainer,
        base_dir=base,
    )
    assert res.ran and not res.promoted
    assert "golden_below_floor" in res.reason
    assert read_active(tmp_path) == "baseline"  # never swapped
    # candidate quarantined
    assert (tmp_path / "router" / "learned" / ".quarantine" / res.version).exists()


def test_orchestrator_auto_rolls_back_regressed_candidate(tmp_path) -> None:
    # Pre-promoted state with a clean baseline complaint rate.
    bundle = learned_bundle_dir("vBad", tmp_path)
    bundle.mkdir(parents=True)
    (bundle / "lgbm_main.bin").write_text("m", encoding="utf-8")
    write_active_atomic("learned/vBad", tmp_path)
    save_train_state(
        TrainState(
            active_version="vBad",
            promoted_at="2026-06-05T00:00:00Z",
            pre_promotion_complaint_rate=0.0,
        ),
        "agx",
        tmp_path,
    )
    # Post-swap traffic with high complaint rate, recent (so the agent looks
    # active and no training runs after the rollback).
    for i in range(30):
        write_sample(
            RouterTrainSample(
                session_key="s",
                turn_index=i,
                ts=f"2026-06-06T11:5{i % 10}:00Z",
                feature_schema_version="v1",
                features_390_b64=encode_features(np.zeros(390, np.float32)),
                route_class="R1",
                final_route_class="R2",
                complaint_detected=(i < 20),  # 20/30 complaints
            ),
            "agx",
            home=tmp_path,
        )

    res = maybe_run_update_router(
        "agx",
        router_cfg=SquillaRouterConfig(
            self_learning=_cfg(min_monitor_samples=10, complaint_regression_delta=0.05)
        ),
        home=tmp_path,
        now=NOW,
        trainer=in_process_trainer,
        base_dir=tmp_path / "base",
    )
    assert res.rolled_back
    assert read_active(tmp_path) == "baseline"
    state = load_train_state("agx", tmp_path)
    assert state.active_version is None
    assert (tmp_path / "router" / "learned" / ".quarantine" / "vBad").exists()
    assert list((tmp_path / "router" / ".receipts").glob("agx-*-rollback.json"))


# --------------------------------------------------------------------------- #
# Base-upgrade detach guard (verify_active_bundle)
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _reset_verify_memo():
    """The verify memo is process-global; isolate it per test."""
    import openstarry_code.squilla_router.self_learning.promotion as promo

    promo._verify_key = None
    promo._verify_result = None
    promo._fp_cache = None
    yield
    promo._verify_key = None
    promo._verify_result = None
    promo._fp_cache = None


def _make_learned(tmp_path, version: str, *, base_fingerprint: str | None) -> None:
    import json

    bundle = learned_bundle_dir(version, tmp_path)
    bundle.mkdir(parents=True)
    (bundle / "lgbm_main.bin").write_bytes(b"learned-head")
    manifest: dict = {"version": version}
    if base_fingerprint is not None:
        manifest["base_fingerprint"] = base_fingerprint
    (bundle / "learned_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _make_base(tmp_path, content: bytes = b"base-model-v1"):
    base = tmp_path / "base"
    base.mkdir(exist_ok=True)
    (base / "lgbm_main.bin").write_bytes(content)
    return base


def test_verify_detaches_on_base_upgrade(tmp_path) -> None:
    from openstarry_code.squilla_router.self_learning.promotion import verify_active_bundle
    from openstarry_code.squilla_router.self_learning.train import base_bundle_fingerprint

    base = _make_base(tmp_path)
    old_fp = base_bundle_fingerprint(base)
    _make_learned(tmp_path, "v1", base_fingerprint=old_fp)
    write_active_atomic("learned/v1", tmp_path)

    # Same base: nothing happens.
    check = verify_active_bundle(base, tmp_path)
    assert not check.detached and read_active(tmp_path) == "learned/v1"

    # Base replaced (package upgrade): detach + quarantine + baseline.
    (base / "lgbm_main.bin").write_bytes(b"base-model-v2-NEW-WEIGHTS")
    check = verify_active_bundle(base, tmp_path)
    assert check.detached and check.reason == "base_upgraded"
    assert read_active(tmp_path) == "baseline"
    assert (tmp_path / "router" / "learned" / ".quarantine" / "v1").exists()


def test_verify_trusts_legacy_bundle_without_fingerprint(tmp_path) -> None:
    """Pre-fingerprint candidates must not be mass-detached on upgrade."""
    from openstarry_code.squilla_router.self_learning.promotion import verify_active_bundle

    base = _make_base(tmp_path)
    _make_learned(tmp_path, "vLegacy", base_fingerprint=None)
    write_active_atomic("learned/vLegacy", tmp_path)

    check = verify_active_bundle(base, tmp_path)
    assert not check.detached
    assert read_active(tmp_path) == "learned/vLegacy"


def test_verify_memoizes_per_pointer_and_base(tmp_path, monkeypatch) -> None:
    """The 39MB hash must not run on every strategy-cache-key computation."""
    import openstarry_code.squilla_router.self_learning.train as train_mod
    from openstarry_code.squilla_router.self_learning.promotion import verify_active_bundle

    base = _make_base(tmp_path)
    fp = train_mod.base_bundle_fingerprint(base)
    _make_learned(tmp_path, "v1", base_fingerprint=fp)
    write_active_atomic("learned/v1", tmp_path)

    calls = {"n": 0}
    real = train_mod.base_bundle_fingerprint

    def counting(base_dir):
        calls["n"] += 1
        return real(base_dir)

    monkeypatch.setattr(train_mod, "base_bundle_fingerprint", counting)
    import openstarry_code.squilla_router.self_learning.promotion as promo

    promo._fp_cache = None
    verify_active_bundle(base, tmp_path)
    verify_active_bundle(base, tmp_path)
    verify_active_bundle(base, tmp_path)
    # Repeated calls are stable, never detach, and the expensive hash is
    # stat-gated to a single computation (see the dedicated hash-once test).
    assert read_active(tmp_path) == "learned/v1"
    assert calls["n"] == 1
    promo._fp_cache = None


def test_verify_noop_on_baseline_pointer(tmp_path) -> None:
    from openstarry_code.squilla_router.self_learning.promotion import verify_active_bundle

    base = _make_base(tmp_path)
    check = verify_active_bundle(base, tmp_path)
    assert not check.detached
    assert read_active(tmp_path) == "baseline"


def test_orchestrator_reconciles_detached_candidate(tmp_path) -> None:
    """After a base upgrade the offline pass clears promotion-monitor state."""
    from openstarry_code.squilla_router.self_learning.train import base_bundle_fingerprint

    base = _make_base(tmp_path)
    old_fp = base_bundle_fingerprint(base)
    _make_learned(tmp_path, "vOld", base_fingerprint=old_fp)
    write_active_atomic("learned/vOld", tmp_path)
    save_train_state(
        TrainState(
            active_version="vOld",
            promoted_at="2026-06-05T00:00:00Z",
            pre_promotion_complaint_rate=0.10,
        ),
        "agd",
        tmp_path,
    )
    # Upgrade the base.
    (base / "lgbm_main.bin").write_bytes(b"base-model-v2")

    res = maybe_run_update_router(
        "agd",
        router_cfg=SquillaRouterConfig(self_learning=_cfg()),
        home=tmp_path,
        now=NOW,
        trainer=in_process_trainer,
        base_dir=base,
    )
    # No training data -> gates fail, but the detach must have reconciled.
    assert not res.rolled_back  # detach is not a regression rollback
    assert read_active(tmp_path) == "baseline"
    state = load_train_state("agd", tmp_path)
    assert state.active_version is None and state.promoted_at is None
    assert state.pre_promotion_complaint_rate is None
    assert list((tmp_path / "router" / ".receipts").glob("agd-*-detached.json"))
    assert (tmp_path / "router" / "learned" / ".quarantine" / "vOld").exists()


def test_candidate_manifest_records_base_fingerprint(tmp_path) -> None:
    import json

    pytest.importorskip("lightgbm")
    from types import SimpleNamespace

    from openstarry_code.squilla_router.self_learning.train import (
        base_bundle_fingerprint,
        build_candidate_bundle,
        train_booster,
    )

    base = tmp_path / "base"
    base.mkdir()
    booster, _ = train_booster(
        _mini_dataset(), base_model_path=None, config=SimpleNamespace(num_boost_round=8)
    )
    booster.save_model(str(base / "lgbm_main.bin"))
    expected = base_bundle_fingerprint(base)

    info = build_candidate_bundle(
        _mini_dataset(),
        base_dir=base,
        learned_root=tmp_path / "learned",
        config=SimpleNamespace(num_boost_round=4),
    )
    assert info.base_fingerprint == expected
    manifest = json.loads(
        (tmp_path / "learned" / info.version / "learned_manifest.json").read_text()
    )
    assert manifest["base_fingerprint"] == expected


def _mini_dataset() -> TrainingDataset:
    rng = np.random.RandomState(0)
    n = 24
    return TrainingDataset(
        X=rng.rand(n, 390).astype(np.float32),
        y=(np.arange(n) % 3).astype(np.int64),
        w=np.ones(n, dtype=np.float32),
        served=(np.arange(n) % 3).astype(np.int64),
        session_keys=[f"s{i // 4}" for i in range(n)],
        turn_indices=[i % 4 for i in range(n)],
        days=["2026-06-01"] * n,
        reasons=["normal"] * n,
        feature_schema_version="v1",
        n_sessions=6,
    )


# --------------------------------------------------------------------------- #
# Engine fallback chain: learned -> baseline -> heuristic
# --------------------------------------------------------------------------- #


def test_broken_learned_bundle_falls_back_to_baseline(tmp_path, monkeypatch) -> None:
    """A corrupt learned bundle must degrade to the shipped ML baseline, not
    straight to heuristic tiering."""
    from openstarry_code.engine.steps import squilla_router as step

    built = []

    class _FakeStrategy:
        source = "v4_phase3"
        _available = True

        def __init__(self, bundle_dir=None, **_kw):
            built.append(bundle_dir)
            if bundle_dir == "/learned/broken":
                raise RuntimeError("incomplete V4 router artifact bundle")

    import openstarry_code.squilla_router.v4_phase3 as v4mod

    monkeypatch.setattr(v4mod, "V4Phase3Strategy", _FakeStrategy)
    monkeypatch.setattr(step, "_active_bundle_dir", lambda _c: "/learned/broken")
    step.invalidate_strategy_cache()

    cfg = SquillaRouterConfig(self_learning=_cfg())
    strategy = step._get_strategy(cfg)
    # First attempt hit the learned dir, second the baseline (None -> packaged).
    assert built == ["/learned/broken", None]
    assert isinstance(strategy, _FakeStrategy)
    step.invalidate_strategy_cache()


def test_learned_and_baseline_both_broken_degrades_to_heuristic(
    tmp_path, monkeypatch
) -> None:
    from openstarry_code.engine.routing.heuristic import HeuristicRouterStrategy
    from openstarry_code.engine.steps import squilla_router as step

    class _AlwaysBroken:
        source = "v4_phase3"

        def __init__(self, **_kw):
            raise RuntimeError("no runtime")

    import openstarry_code.squilla_router.v4_phase3 as v4mod

    monkeypatch.setattr(v4mod, "V4Phase3Strategy", _AlwaysBroken)
    monkeypatch.setattr(step, "_active_bundle_dir", lambda _c: "/learned/broken")
    monkeypatch.setattr(step, "_router_runtime_warning_emitted", False)
    step.invalidate_strategy_cache()

    cfg = SquillaRouterConfig(self_learning=_cfg())
    strategy = step._get_strategy(cfg)
    assert isinstance(strategy, HeuristicRouterStrategy)
    step.invalidate_strategy_cache()


def test_failed_detach_is_not_memoized_and_retries(tmp_path, monkeypatch) -> None:
    """A transient detach failure must not permanently trust the stale bundle."""
    import openstarry_code.squilla_router.self_learning.promotion as promo
    from openstarry_code.squilla_router.self_learning.promotion import verify_active_bundle
    from openstarry_code.squilla_router.self_learning.train import base_bundle_fingerprint

    base = _make_base(tmp_path)
    old_fp = base_bundle_fingerprint(base)
    _make_learned(tmp_path, "v1", base_fingerprint=old_fp)
    write_active_atomic("learned/v1", tmp_path)
    (base / "lgbm_main.bin").write_bytes(b"base-model-v2-UPGRADED")

    calls = {"n": 0}
    real_rollback = promo.rollback_active

    def flaky_rollback(home=None, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("disk full")
        return real_rollback(home, **kw)

    monkeypatch.setattr(promo, "rollback_active", flaky_rollback)

    first = verify_active_bundle(base, tmp_path)
    assert not first.detached  # fail-open on the transient error
    assert read_active(tmp_path) == "learned/v1"

    second = verify_active_bundle(base, tmp_path)  # must RETRY, not trust memo
    assert second.detached and second.reason == "base_upgraded"
    assert read_active(tmp_path) == "baseline"
    assert calls["n"] == 2


def test_fingerprint_hash_runs_once_per_base_file_change(tmp_path, monkeypatch) -> None:
    """The 39MB sha256 must be stat-gated, not recomputed per call."""
    import openstarry_code.squilla_router.self_learning.promotion as promo
    import openstarry_code.squilla_router.self_learning.train as train_mod
    from openstarry_code.squilla_router.self_learning.promotion import verify_active_bundle

    base = _make_base(tmp_path)
    fp = train_mod.base_bundle_fingerprint(base)
    _make_learned(tmp_path, "v1", base_fingerprint=fp)
    write_active_atomic("learned/v1", tmp_path)
    promo._fp_cache = None

    hashes = {"n": 0}
    real = train_mod.base_bundle_fingerprint

    def counting(base_dir):
        hashes["n"] += 1
        return real(base_dir)

    monkeypatch.setattr(train_mod, "base_bundle_fingerprint", counting)
    for _ in range(5):
        verify_active_bundle(base, tmp_path)
    assert hashes["n"] == 1  # one hash; four stat-gated cache hits

    promo._fp_cache = None


def test_engine_active_bundle_dir_invokes_verify_and_detaches(
    tmp_path, monkeypatch
) -> None:
    """The real engine path must run the base-upgrade guard, not just resolve.

    No monkeypatching of _active_bundle_dir itself: config points v4_bundle_dir
    at a synthetic base, the state home holds a promoted-but-stale candidate,
    and resolving the bundle through the engine must detach it.
    """
    from openstarry_code.engine.steps import squilla_router as step
    from openstarry_code.squilla_router.self_learning.train import base_bundle_fingerprint

    monkeypatch.setenv("OPENSTARRY_CODE_STATE_DIR", str(tmp_path))
    base = _make_base(tmp_path)
    old_fp = base_bundle_fingerprint(base)
    _make_learned(tmp_path, "vStale", base_fingerprint=old_fp)
    write_active_atomic("learned/vStale", tmp_path)
    (base / "lgbm_main.bin").write_bytes(b"base-model-v2-UPGRADED")

    cfg = SquillaRouterConfig(self_learning=_cfg(), v4_bundle_dir=str(base))
    resolved = step._active_bundle_dir(cfg)

    assert resolved is None  # stale candidate detached -> baseline
    assert read_active(tmp_path) == "baseline"
    assert (tmp_path / "router" / "learned" / ".quarantine" / "vStale").exists()
