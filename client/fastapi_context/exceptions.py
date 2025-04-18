from typing import Any


class ContextMiddlewareError(Exception):
    """Base class for all exceptions raised by the ContextMiddleware."""

    def __init__(
        self,
        status_code: int = 400,
        error_code: int = 200,
        data: Any = None,
        message: str = "Bad Request",
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.data = data
        self.message = message
        super().__init__(message)


class ContextMiddlewareConfigError(ContextMiddlewareError):
    def __init__(self, message: str = "ContextMiddlewareConfig Error"):
        super().__init__(message=message)
