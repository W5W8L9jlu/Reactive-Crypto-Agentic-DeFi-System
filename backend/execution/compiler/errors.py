from __future__ import annotations

from typing import Any


class ExecutionCompilerError(Exception):
    """Base compiler error with machine-readable context."""

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


class CompilationInputError(ExecutionCompilerError):
    """Raised when compilation input data is invalid."""


class ChainStateError(ExecutionCompilerError):
    """Raised when chain state is stale or inconsistent."""


class ConstraintViolationError(ExecutionCompilerError):
    """Raised when computed constraints violate invariants."""


class TokenPrecisionError(ExecutionCompilerError):
    """Raised when decimal scaling cannot be resolved safely."""


class CompilationConfigError(ExecutionCompilerError):
    """Raised when compiler config is invalid."""
