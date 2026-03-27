"""Domain exceptions for the service layer.

API layer should catch these and translate to appropriate HTTP responses.
"""


class AppError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""
    pass


class ForbiddenError(AppError):
    """Raised when a user does not have permission to perform an action."""
    pass


class ConflictError(AppError):
    """Raised when an action conflicts with existing state (e.g. duplicate)."""
    pass


class ValidationError(AppError):
    """Raised when input data is invalid at the domain level."""
    pass
