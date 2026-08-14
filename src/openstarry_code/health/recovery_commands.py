from __future__ import annotations

import shlex
from pathlib import Path

CONFIG_AWARE_COMMAND_PREFIXES = (
    "openstarry-code gateway restart",
    "openstarry-code gateway start",
    "openstarry-code gateway status",
    "openstarry-code providers configure",
    "openstarry-code providers status",
    "openstarry-code config ",
    "openstarry-code search status",
    "openstarry-code search configure",
    "openstarry-code diagnostics status",
    "openstarry-code memory status",
    "openstarry-code memory repair list",
    "openstarry-code memory repair run",
    "openstarry-code configure ",
    "openstarry-code onboard",
    "openstarry-code sandbox ",
    "openstarry-code channels add",
    "openstarry-code channels edit",
    "openstarry-code channels enable",
    "openstarry-code channels disable",
    "openstarry-code channels remove",
    "openstarry-code channels list",
    "openstarry-code channels restart",
    "openstarry-code channels status",
)


def supports_config_option(command: str) -> bool:
    return any(command.startswith(prefix) for prefix in CONFIG_AWARE_COMMAND_PREFIXES)


def command_with_config(command: str, config_path: str | Path | None) -> str:
    if not config_path or " --config " in command or not supports_config_option(command):
        return command
    return f"{command} --config {shlex.quote(str(config_path))}"
