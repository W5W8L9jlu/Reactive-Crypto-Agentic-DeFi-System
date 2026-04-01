class StrategyBoundaryDomainError(Exception):
    """Base domain error for the strategy boundary service."""


class TemplateNotFoundError(StrategyBoundaryDomainError):
    """Raised when a template ID/version cannot be found."""


class IntentLinkError(StrategyBoundaryDomainError):
    """Raised when StrategyIntent and TradeIntent cannot be linked safely."""


class MissingBoundaryRuleError(StrategyBoundaryDomainError):
    """Raised when required boundary rules are missing from template definition."""
