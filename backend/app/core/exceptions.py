from fastapi import HTTPException, status


class AppError(Exception):
    def __init__(self, message: str, code: str = "app_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class ModerationError(AppError):
    def __init__(self, message: str = "Your request was flagged as inappropriate."):
        super().__init__(message, code="moderation_blocked")


class ServiceUnavailableError(AppError):
    def __init__(self, service: str):
        super().__init__(f"{service} is temporarily unavailable.", code="service_unavailable")


def to_http_exception(exc: AppError) -> HTTPException:
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, ModerationError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ServiceUnavailableError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HTTPException(status_code=status_code, detail={"code": exc.code, "message": exc.message})
