from __future__ import annotations


class ExecutionLayerDomainError(ValueError):
    """Base domain error for runtime execution record assembly."""


class InvalidRuntimeTransitionError(ExecutionLayerDomainError):
    """Raised when runtime result cannot be promoted into an execution record."""


class MissingExecutionReceiptError(ExecutionLayerDomainError):
    """Raised when callback_ref receipt cannot be loaded from chain receipt reader."""


class EmergencyForceCloseInputError(ExecutionLayerDomainError):
    """Raised when emergency force-close input cannot be mapped into contract call shape."""
