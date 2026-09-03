"""
Domain-level exceptions, mapped to consistent HTTP error responses in main.py.
"""


class AppError(Exception):
    """Base class for all handled application errors."""

    status_code: int = 400
    error_code: str = "APP_ERROR"

    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        if error_code:
            self.error_code = error_code
        super().__init__(message)


class BadRequestError(AppError):
    status_code = 400
    error_code = "BAD_REQUEST"


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"


class UnauthorizedError(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    error_code = "FORBIDDEN"


class ValidationAppError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
