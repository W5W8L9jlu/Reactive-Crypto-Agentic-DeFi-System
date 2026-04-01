class CliSurfaceDomainError(Exception):
    """Base domain error for the CLI surface."""


class MissingCliAdapterError(CliSurfaceDomainError):
    """Raised when a CLI command is routed without an explicit adapter."""


class MissingCliDependencyError(CliSurfaceDomainError):
    """Raised when optional CLI runtime dependencies are not installed."""


class UnresolvedCliRouteError(CliSurfaceDomainError):
    """Raised when a CLI route is not part of the supported command surface."""
