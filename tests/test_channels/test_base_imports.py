"""Smoke test: every channel adapter must be importable with only base deps.

After 0.1.0's refactor each vendor SDK (lark-oapi / python-telegram-bot /
dingtalk-stream / qq-botpy / cryptography) lives in base ``dependencies``
rather than in an opt-in extra. A bare ``pip install opensquilla`` must
therefore be enough to ``import`` any of the in-tree channel adapters
without raising ``ImportError``.

These tests guard against the regression where someone moves an SDK back
into an extra and silently breaks the "everything works out of the box"
guarantee from the install plan.
"""

from __future__ import annotations

import importlib


def test_feishu_module_importable() -> None:
    importlib.import_module("openstarry_code.channels.feishu")


def test_telegram_module_importable() -> None:
    importlib.import_module("openstarry_code.channels.telegram")


def test_dingtalk_module_importable() -> None:
    importlib.import_module("openstarry_code.channels.dingtalk")


def test_qq_module_importable() -> None:
    importlib.import_module("openstarry_code.channels.qq")


def test_wecom_module_importable() -> None:
    importlib.import_module("openstarry_code.channels.wecom")
