class ReactiveRuntimeError(ValueError):
    """Base domain error for the reactive runtime adapters."""


class UnknownReactiveIntentError(ReactiveRuntimeError):
    """Raised when a callback arrives for an intent that was not registered by this runtime."""


class CallbackValidationError(ReactiveRuntimeError):
    """Raised when a callback cannot be executed under the current state machine state."""


class MissingReactiveRuntimeSpecError(ReactiveRuntimeError):
    """Raised when the current knowledge/contract files do not define the required behavior."""
