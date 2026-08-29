"""Pure-PIL render-geometry tests for the computer-use visual overlay."""

from __future__ import annotations

import numpy as np

from openstarry_code.computer_use.cursor_overlay import (
    THEME_DARK,
    _BANNER_SHADOW,
    _GLOW_THICK,
    _banner_width,
    _build_banner,
    _build_glow,
)


def test_banner_width_adaptive_to_screen() -> None:
    # normal screen uses the 40% ratio
    assert _banner_width(1920) == 768
    # ratio floor (360) applies when the screen allows it
    assert _banner_width(800) == 360
    # on every screen size the layer (panel + shadow pad) stays on-screen
    for vw in (1920, 1366, 900, 640, 400, 300, 200):
        assert _banner_width(vw) + 2 * _BANNER_SHADOW <= vw


def test_build_banner_layer_size_matches_panel_plus_shadow() -> None:
    box = (576, 14, 1344, 70)  # x0, y0, x1, y1
    layer = _build_banner(THEME_DARK, (91, 140, 255), None, (0, 0), box, 1.0)
    assert layer.size == (1344 - 576 + 2 * _BANNER_SHADOW, 56 + 2 * _BANNER_SHADOW)


def test_build_banner_corner_mask_is_antialiased() -> None:
    box = (576, 14, 1344, 70)
    layer = _build_banner(THEME_DARK, (91, 140, 255), None, (0, 0), box, 1.0)
    pad = _BANNER_SHADOW
    alpha = np.asarray(layer.getchannel("A"))
    # horizontal profile through the top-left rounded corner of the panel
    profile = alpha[pad + 2, pad : pad + 26].tolist()
    mid = [v for v in profile if 0 < v < 255]
    # a binary (non-supersampled) mask would show at most one mid value here
    assert len(mid) >= 6


def test_build_banner_alpha_fade_scales_whole_layer() -> None:
    box = (576, 14, 1344, 70)
    layer = _build_banner(THEME_DARK, (91, 140, 255), None, (0, 0), box, 0.5)
    assert np.asarray(layer.getchannel("A")).max() <= 128


def test_build_glow_corner_brighter_than_band_run() -> None:
    """Corner overlap must be the UNION of both bands, not their overwrite.

    Sequential painting let one band's falloff overwrite the other inside the
    corner, making every corner a dark square against the adjacent bands.
    """
    glow = _build_glow((400, 300), (91, 140, 255), (240, 166, 200), 1.0)
    alpha = np.asarray(glow.getchannel("A")).astype(int)
    t = _GLOW_THICK
    corner = alpha[0:t, 0:t].mean()          # both bands overlap here
    top_run = alpha[0:t, 100:100 + t].mean()  # top band away from corners
    left_run = alpha[100:100 + t, 0:t].mean()  # left band away from corners
    assert corner > top_run
    assert corner > left_run