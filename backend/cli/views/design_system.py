from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CLIDesignPalette:
    primary: str
    secondary: str
    success: str
    warning: str
    error: str
    muted: str


ASCII_REACTIVE_AGENTS = r"""
  ____                 _   _               _                _
 |  _ \ ___  __ _  ___| |_(_)_   _____    / \   __ _  ___ _ __ | |_ ___
 | |_) / _ \/ _` |/ __| __| \ \ / / _ \  / _ \ / _` |/ _ \ '_ \| __/ __|
 |  _ <  __/ (_| | (__| |_| |\ V /  __/ / ___ \ (_| |  __/ | | | |_\__ \
 |_| \_\___|\__,_|\___|\__|_| \_/ \___|/_/   \_\__, |\___|_| |_|\__|___/
                                                |___/
"""


WORKFLOW_MODULES = (
    "strategy",
    "decision",
    "approval",
    "execution",
    "export",
    "monitor",
)


STATUS_COMPLETED = "completed"
STATUS_IN_PROGRESS = "in_progress"
STATUS_PENDING = "pending"


def build_module_statuses(*, route: str) -> Mapping[str, str]:
    module = route.split(".", maxsplit=1)[0].strip().lower()
    statuses: dict[str, str] = {}
    reached_active = False
    for name in WORKFLOW_MODULES:
        if name == module:
            statuses[name] = STATUS_IN_PROGRESS
            reached_active = True
            continue
        statuses[name] = STATUS_COMPLETED if not reached_active else STATUS_PENDING
    if module not in statuses:
        for name in WORKFLOW_MODULES:
            statuses[name] = STATUS_PENDING
    return statuses

