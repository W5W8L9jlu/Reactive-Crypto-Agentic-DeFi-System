from __future__ import annotations


class CLISurfaceError(Exception):
    """Base error for CLI surface routing and rendering failures."""


class RouteBindingMissingError(CLISurfaceError):
    """Raised when a CLI command route is not bound to a concrete service adapter."""


class CLISurfaceInputError(CLISurfaceError):
    """Raised when CLI input is incomplete for the selected command mode."""

