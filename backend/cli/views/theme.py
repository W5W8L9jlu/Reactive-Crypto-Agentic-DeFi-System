from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from ..errors import CLISurfaceError

_THEME_ENV = "REACTIVE_CLI_THEME"
_DEFAULT_THEME_NAME = "default"


@dataclass(frozen=True)
class CLISurfaceTheme:
    name: str
    primary: str
    secondary: str
    success: str
    warning: str
    error: str
    muted: str
    panel_border: str
    error_border: str
    title_style: str


_THEMES: Mapping[str, CLISurfaceTheme] = {
    "default": CLISurfaceTheme(
        name="default",
        primary="#5EF38C",
        secondary="#8A5CF7",
        success="#5EF38C",
        warning="#EFC84A",
        error="#FF5E79",
        muted="#8EA0AE",
        panel_border="#5EF38C",
        error_border="#FF5E79",
        title_style="bold #5EF38C",
    ),
    "light": CLISurfaceTheme(
        name="light",
        primary="blue",
        secondary="magenta",
        success="green",
        warning="yellow",
        error="red",
        muted="bright_black",
        panel_border="blue",
        error_border="red",
        title_style="bold blue",
    ),
    "minimal": CLISurfaceTheme(
        name="minimal",
        primary="white",
        secondary="white",
        success="white",
        warning="white",
        error="red",
        muted="bright_black",
        panel_border="white",
        error_border="red",
        title_style="bold white",
    ),
}


def resolve_cli_theme_from_env(env: Mapping[str, str] | None = None) -> CLISurfaceTheme:
    env_vars = env if env is not None else os.environ
    raw = env_vars.get(_THEME_ENV, _DEFAULT_THEME_NAME)
    theme_name = (raw or _DEFAULT_THEME_NAME).strip().lower()
    theme = _THEMES.get(theme_name)
    if theme is None:
        supported = ", ".join(sorted(_THEMES.keys()))
        raise CLISurfaceError(f"{_THEME_ENV} must be one of: {supported}. received: {raw!r}")
    return theme
