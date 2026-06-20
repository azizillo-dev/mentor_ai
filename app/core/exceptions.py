"""
Custom HTTP exceptions for centralized error handling.
"""

from fastapi import HTTPException, status


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InternalServerException(HTTPException):
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


# ─── Domain-Specific Exceptions ───────────────────────────────────────────────
class InvalidCredentialsException(UnauthorizedException):
    def __init__(self):
        super().__init__(detail="Invalid email or password")


class EmailAlreadyExistsException(ConflictException):
    def __init__(self):
        super().__init__(detail="An account with this email already exists")


class UserNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(detail="User not found")


class InvalidTokenException(UnauthorizedException):
    def __init__(self):
        super().__init__(detail="Invalid or expired token")
