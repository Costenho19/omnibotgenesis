class OmnixError(Exception):
    """Base exception for all OMNIX SDK errors."""
    pass


class OmnixAuthError(OmnixError):
    """Invalid or missing API key."""
    pass


class OmnixValidationError(OmnixError):
    """Request payload failed validation."""
    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []


class OmnixGovernanceBlock(OmnixError):
    """
    The decision was evaluated and explicitly BLOCKED by OMNIX governance.
    This is not an error — it is a governance verdict.
    Inspect .receipt for the full signed receipt with the veto chain.
    """
    def __init__(self, receipt: dict):
        self.receipt = receipt
        blocked_by = receipt.get('veto_chain', [])
        super().__init__(
            f"Decision BLOCKED by OMNIX governance. "
            f"Veto chain: {blocked_by}. "
            f"Receipt: {receipt.get('receipt_id')}"
        )


class OmnixRateLimitError(OmnixError):
    """Too many requests. Retry after the specified interval."""
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s.")


class OmnixServerError(OmnixError):
    """Unexpected server-side error. Contact support if it persists."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Server error {status_code}: {message}")


class OmnixNetworkError(OmnixError):
    """Network connectivity issue."""
    pass
