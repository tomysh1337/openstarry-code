---
name: feature-flag-patterns
description: >
  Design and review feature flags, kill switches, targeting, rollout, and flag
  cleanup. Use when feature flags, feature toggles, kill switch, gradual
  rollout, percentage rollout, targeting rules, LaunchDarkly, Unleash, Flagsmith,
  OpenFeature, 功能开关, 灰度, 熔断开关, or long-lived flag debt. Complements
  code-quality-standards; does not own log/error copy wording.
---

# Feature Flag Patterns

Feature flags are **runtime control planes** for release safety: ship dark,
roll out gradually, target cohorts, and **kill** bad paths fast. Prefer the
repository’s existing flag SDK and naming scheme; treat every new permanent
branch in code as debt with an owner and removal plan.

## Use When

- Adding, reviewing, or refactoring **feature flags / toggles**, experiments, or
  **kill switches**
- Designing **targeting** (user, tenant, plan, region, percentage, ring)
- Planning **gradual rollout**, canary, or instant disable without redeploy
- Cleaning up stale flags, dead code paths, or “temporary” flags older than a release
- User mentions: feature flag, feature toggle, kill switch, gradual rollout,
  percentage rollout, targeting, multivariate flag, OpenFeature, LaunchDarkly,
  Unleash, Flagsmith, ConfigCat, Split, Flagr, 功能开关, 特性开关, 灰度发布,
  放量, 熔断开关, 远程配置

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| General code reliability, tests, security of the change | `code-quality-standards` |
| Structured operator logs around flag evaluation | `logging-message-style` |
| User-visible errors when a feature is unavailable | `error-message-ux-writing` |
| CI deploy gates / pipeline wiring only | `ci-cd-pipeline-patterns` |
| Observability of rollout impact (metrics/traces) | `observability-metrics-tracing` |

## Repo Config First

Repo and org flag platform config **outrank** this skill’s defaults.

1. **SDK & provider:** OpenFeature + provider, LaunchDarkly, Unleash, Flagsmith,
   homegrown config service, or simple env/config maps already in use
2. **Bootstrap & offline behavior:** local defaults when the flag service is
   down; init timeout; cached evaluations; fail-open vs fail-closed policy per flag type
3. **Naming & project structure:** existing flag key conventions
   (`team.feature.action`), projects/environments (dev/staging/prod)
4. **Context schema:** which attributes are allowed for targeting
   (`userId`, `tenantId`, `plan`, `country`) and which are forbidden (raw PII
   beyond policy, secrets)
5. **Admin & audit:** who can change prod flags; approval; change history;
   dual-control for kill switches on payments/auth
6. **Lifecycle:** ticket/ADR links, expiration dates, “temporary flag” process,
   stale-flag reports
7. **Testing hooks:** test doubles, mandatory flag fixtures in unit/integration
   tests, CI overrides
8. **Related release process:** canary deploys vs flag ramps; do not invent a
   second control plane if deploy rings already cover the need

**Precedence:** Follow repo/org flag governance when it conflicts with examples
below. Surface conflicts that default prod to “on” for unvalidated flags, embed
secrets in targeting rules, or leave flags with no owner/expiry.

## Flag Types (choose deliberately)

| Type | Purpose | Default posture | Cleanup |
| --- | --- | --- | --- |
| **Release toggle** | Hide unfinished work; enable when ready | Off in prod until ready | Remove after full rollout |
| **Experiment / A-B** | Measure variants | Explicit traffic split | Remove after decision; keep analysis notes |
| **Ops / kill switch** | Disable a path under incident | On (feature healthy) or safe mode documented | Keep only if still a real risk; review quarterly |
| **Permission / entitlement** | Plan-gated features | Match billing/auth source of truth | Prefer authZ system long-term; flags are a bridge |
| **Config dynamic** | Tunable numbers/strings | Sensible offline default | Document bounds; validate ranges |

Do **not** use flags as a permanent substitute for proper authorization,
multi-tenant isolation, or configuration management without an explicit design.

## Workflow

1. **Name the decision.** What behavior changes? Who is at risk if it is wrong?
   Is a flag necessary, or is a normal config/env enough?
2. **Pick type and default.** Release vs kill vs experiment; **fail-closed** for
   risky new paths (default off); **fail-open or last-known** only when outage of
   the flag service must not brick core journeys—document per flag.
3. **Check repo platform.** Reuse SDK, context builders, and key naming. Register
   the flag in the provider (or config) for all envs with owners and description.
4. **Define targeting.** Start narrow (internal, single tenant, % canary). Avoid
   targeting on high-cardinality or sensitive attributes without policy review.
5. **Implement a thin evaluation boundary.** One module/wrapper evaluates flags;
   call sites stay readable (`if (flags.isEnabled(CHECKOUT_V2, ctx))`). Avoid
   scattering raw SDK calls and stringly keys.
6. **Instrument the rollout.** Metric dimensions: flag key + variant/result
   (low cardinality); logs on evaluation only when needed (debug/sampled);
   traces may attribute `feature_flag` on relevant spans
   (`observability-metrics-tracing`).
7. **Test both sides.** Unit/integration tests for **on and off** (and variants).
   Avoid untested dark code. Contract-test offline defaults.
8. **Roll out.** Enable in non-prod → limited prod cohort → ramp % → full.
   Watch RED signals and error budgets. Kill switch path rehearsed.
9. **Cleanup.** After stable 100% (or experiment decision), remove flag branches,
   defaults, and provider entries in a follow-up PR; delete dead code.
10. **Verify.** Confirm evaluation context in prod debug tools; confirm kill
    switch latency; confirm no PII leakage in flag analytics events.

## Design Practices

### Evaluation

- Build **evaluation context** once per request/message (user/tenant/app version)
- Cache evaluations per request where the SDK does not; do not re-fetch in a loop
- Keep flag keys **constants** (typed enum or const object), not free-string litter
- Prefer boolean flags unless multivariate is required; document each variant

### Kill switches

- Place at a **safe boundary** (before side effects / payments / outbound storms)
- Default and offline behavior must leave the system in a **known safe** mode
- Pair with runbook: who flips, what to watch, when to re-enable
- Log the disable event at WARN/INFO with `flagKey`, reason/actor if available—
  never log full user payloads (`logging-message-style`)

### Targeting

- Allowed: plan tier, env, tenant id allowlist, percentage sticky bucketing,
  app version, region codes
- Careful: email domain for dogfood (avoid full email in exported analytics)
- Forbidden as labels/export: passwords, tokens, session ids, raw auth headers
- Sticky assignment for experiments (consistent experience) when UX requires it

### Lifecycle & cleanup

- Every release flag has: **owner**, **creation date**, **intended removal**,
  link to ticket/PR
- Track “flag age”; treat >N releases at 100% as defect
- Delete code paths for retired variants; do not leave `if (false)` fossils
- Experiments: record winning variant then hard-code or rehome to config

### Safety

- Flags that skip authZ, validation, or payment checks are **security changes**—
  review as such (`code-quality-standards`)
- Server-side evaluation for security-sensitive toggles; do not trust client-only
  flags for access control
- Separate **ops kill switches** from **marketing experiments** in naming and access

## Good / Bad Examples

### Thin wrapper and typed keys

**Good**

```typescript
// flags.ts — single boundary
export const Flag = {
  CheckoutV2: "checkout.v2",
  PaymentsKill: "payments.charge.kill",
} as const;

export function isOn(key: string, ctx: EvalContext): boolean {
  return client.getBooleanValue(key, false, ctx); // default false for release flags
}

// call site
if (isOn(Flag.CheckoutV2, ctx)) {
  return checkoutV2(req);
}
return checkoutV1(req);
```

**Bad**

```typescript
if (await ld.variation("checkout.v2", user, false)) { /* … */ }
// … 40 files later …
if (await ld.variation("checkout_v2", user, true)) { /* different key + default */ }
```

### Kill switch before side effects

**Good**

```python
if flags.is_enabled("payments.charge.kill", ctx, default=False):
    # feature healthy when flag false; kill when true — document polarity!
    logger.warning("payments_charge_killed", flag="payments.charge.kill")
    raise PaymentUnavailableError(code="PAYMENTS_TEMPORARILY_UNAVAILABLE")

charge_card(...)  # side effect only if not killed
```

**Bad**

```python
charge_card(...)
if flags.is_enabled("payments.kill"):
    pass  # too late; money already moved
```

Polarity note: pick one convention repo-wide (**enabled means feature on** vs
**kill flag true means stop**). Document in the wrapper; never mix silently.

### Targeting and defaults

**Good**

```text
Flag: checkout.v2
Default (offline): false
Prod targeting: tenant allowlist → 5% sticky by userId → 25% → 100%
Owner: payments-team@…  Remove-after: 2026-08-01 or next release after 100%
```

**Bad**

```text
Default true in SDK fallback
Targeting: email == full customer email exported to third-party analytics
No owner, no expiry, still branching two years later
```

### User-facing degradation

**Good** (pairs with `error-message-ux-writing`)

```json
{
  "code": "PAYMENTS_TEMPORARILY_UNAVAILABLE",
  "message": "Payments are temporarily unavailable. Try again later or use another method.",
  "requestId": "req_…"
}
```

**Bad**

```text
message: "Flag payments.charge.kill=true evaluated for user 55a1…"
```

### Testing both paths

**Good**

```text
test CheckoutV2_off_uses_legacy_flow
test CheckoutV2_on_uses_new_flow
test PaymentsKill_on_returns_stable_code_and_skips_stripe
test flag_service_down_uses_default_false_for_release_toggle
```

**Bad**

```text
Only tested with flag on in local .env
Prod default opposite of test default
```

### Cleanup

**Good**

```text
PR1: ramp to 100%, monitor
PR2: remove Flag.CheckoutV2 branches, delete provider flag, update docs
```

**Bad**

```text
if (isOn(Flag.CheckoutV2, ctx) || true) { always new path }
// flag still in UI console forever; dead legacy code remains
```

## Anti-Patterns

- Stringly flag keys duplicated with typos and conflicting defaults
- **Client-only** flags enforcing security or billing entitlements
- Nested flag pyramids (`if a && b && !c`) no one can reason about
- Using flags instead of fixing broken deploy/rollback
- Logging full evaluation context with PII at INFO for every request
- Multivariate flags with undocumented variants
- “Temporary” flags without owner, ticket, or removal date
- Fail-open on a brand-new risky path when the flag service blips (silent enable)
- Entitlement checks only in the flag tool while API remains callable without flag

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Feature flags, kill switches, targeting, rollout, cleanup, 功能开关 | **This skill** | — |
| Implementation quality, authZ mistakes, tests for both paths | `code-quality-standards` | always on production changes |
| Log events for kills/evaluations (structure, levels, redaction) | `logging-message-style` | this skill for when to log |
| User-visible downtime / degraded feature copy + stable codes | `error-message-ux-writing` | this skill for kill/fallback behavior |
| Metrics/traces for ramp health and flag dimensions | `observability-metrics-tracing` | this skill for rollout steps |
| Deploy pipeline canary vs flag ramp wiring | `ci-cd-pipeline-patterns` | this skill for runtime toggles |

Always apply **`code-quality-standards`** when flag branches ship in product code.
Use **`logging-message-style`** for operator events. Use
**`error-message-ux-writing`** when disabled features surface to users.

## Checklist

- [ ] Repo flag SDK/provider, naming, env projects, and offline defaults identified
- [ ] Flag type chosen (release / experiment / kill / entitlement bridge) with clear polarity
- [ ] Key is constant/typed; evaluation goes through a thin shared boundary
- [ ] Defaults safe for offline/timeout; fail-open vs fail-closed documented
- [ ] Targeting uses allowed context attributes; no secret/PII abuse in analytics
- [ ] Both (all) variants tested; CI can force flag state
- [ ] Kill switch sits before irreversible side effects; runbook exists for ops flags
- [ ] Rollout plan: cohort → % → 100% with metrics watched (`observability-metrics-tracing`)
- [ ] User-facing degradation uses stable codes/copy (`error-message-ux-writing`)
- [ ] Logs redacted and structured (`logging-message-style`); not per-request evaluation spam
- [ ] Owner, description, and removal/expiry recorded in provider or docs
- [ ] Cleanup PR planned or completed after full rollout / experiment decision
- [ ] Server-side enforcement for security- or billing-sensitive behavior

## Rules

- A flag is a **loan against complexity**—borrow deliberately, repay with cleanup.
- Prefer one evaluation module and consistent defaults over scattered SDK calls.
- Never rely on client-side flags alone for authorization or payment control.
- Kill switches must be faster and safer than a redeploy; rehearse them.
- Repo governance and provider config win; this skill is the review bar and pattern guide.
