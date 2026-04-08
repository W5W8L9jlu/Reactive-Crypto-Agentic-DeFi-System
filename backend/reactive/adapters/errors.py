from __future__ import annotations


class ReactiveRuntimeError(Exception):
    """Base domain error for the reactive runtime adapter seam."""


class MissingReactiveRuntimeSpecError(ReactiveRuntimeError):
    """Raised when knowledge/contract docs do not define a required runtime behavior."""


class TriggerBindingError(ReactiveRuntimeError):
    """Raised when a trigger does not belong to the registered investment intent."""


class StateMachineInvariantError(ReactiveRuntimeError):
    """Raised when a trigger is incompatible with the current investment position state."""


class CallbackVerificationError(ReactiveRuntimeError):
    """Raised when callback execution cannot prove the expected state-machine transition."""
