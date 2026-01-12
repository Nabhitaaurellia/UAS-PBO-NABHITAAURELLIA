class AppError(Exception):
    """Base error for app domain/application errors."""

class AuthError(AppError):
    pass

class ValidationError(AppError):
    pass

class NotFoundError(AppError):
    pass

class ConflictError(AppError):
    pass