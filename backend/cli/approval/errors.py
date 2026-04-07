class ApprovalFlowError(Exception):
    """Base error for approval flow operations."""


class ApprovalExpiredError(ApprovalFlowError):
    """Raised when an expired intent is sent down the approval path."""


class ApprovalBlockedError(ApprovalFlowError):
    """Raised when approval is blocked by structured validation state."""


class MissingMachineTruthError(ApprovalFlowError):
    """Raised when raw approval output is requested without machine truth."""
