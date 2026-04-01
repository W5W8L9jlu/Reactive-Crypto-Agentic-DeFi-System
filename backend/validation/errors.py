class ValidationEngineDomainError(ValueError):
    """Base domain error for validation engine."""


class MissingValidationSpecError(ValidationEngineDomainError):
    """Raised when knowledge/contract files do not define a required behavior."""
