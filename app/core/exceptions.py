from fastapi import status


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DuplicateResourceException(AppException):
    """Raised when a resource already exists (e.g. duplicate email or tenant)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class NotFoundException(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ValidationException(AppException):
    """Raised for business-level validation errors."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(
            message=message, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
        )


class KeycloakException(AppException):
    """Raised when a Keycloak integration call fails."""

    def __init__(
        self,
        message: str = "Authentication service error",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ):
        super().__init__(message=message, status_code=status_code)


class KeycloakAuthException(KeycloakException):
    """Raised when service-account authentication with Keycloak fails."""

    def __init__(self, message: str = "Authentication service authorization failure"):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)


class KeycloakConflictException(DuplicateResourceException):
    """Raised when Keycloak returns 409 Conflict (e.g. duplicate user)."""

    def __init__(self, message: str = "A user with this email already exists."):
        super().__init__(message=message)


class DatabaseException(AppException):
    """Raised when a database operation fails unexpectedly."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
