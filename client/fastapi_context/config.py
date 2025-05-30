from typing import Optional, Union, Callable, Awaitable, Any, Type

from pydantic import BaseModel, Field
from starlette.responses import Response, JSONResponse, PlainTextResponse
from starlette_context.plugins import Plugin

from fastapi_context.exceptions import ContextMiddlewareError


class JsonResponseConfig(BaseModel):
    code: int = Field(default=0, title="code")
    data: Any = Field(default=None, title="data")
    message: str = Field(default="", title="message")

    @classmethod
    def create_model_by_error(cls, error: ContextMiddlewareError):
        """
        create json data by context error
        """
        return cls(code=error.error_code, data=error.data, message=error.message)


class ContextConfig(BaseModel):
    """
    ContextConfig
    """
    plugins: list[Plugin] = Field(default=[], title="插件")
    error_response: Type[Response] = JSONResponse
    json_data_class: Type[BaseModel] = JsonResponseConfig

    class Config:
        arbitrary_types_allowed = True


class AuthPluginConfig(BaseModel):
    """
    AuthPluginConfig
    """
    url_white_list: list = Field(default=[], title="url white list")
    key: str = Field(default="auth", min_length=1, title="context key")
    user_class: Optional[Any] = Field(default=None, title="user class")
    get_token: Union[str, Callable]
    error_status_code: int = Field(default=200, title="http status code")
    code: int = Field(default=-1, title="error code")


class JWTAuthPluginConfig(AuthPluginConfig):
    """
    jwt auth config
    """
    jwt_secret: str
    jwt_algorithms: Union[str, list] = "HS256"


class RedisConfig(BaseModel):
    host: str
    port: int
    db: int = Field(default=0)
    password: Optional[str] = Field(default=None)
    decode_responses: bool = Field(default=True)
    retry_on_timeout: bool = Field(default=False)
    socket_connect_timeout: float = Field(default=5.0, title="socket connect timeout")
    socket_timeout: float = Field(default=5.0, title="socket timeout")
    max_connections: int = Field(default=20, title="max connections")
    health_check_interval: int = Field(default=10, title="health check interval")


class RedisAuthPluginConfig(AuthPluginConfig):
    redis_token_key_prefix: str = Field(default="")
    redis_client_function: Union[Callable, Awaitable, None] = None
    redis_config: Union[None, RedisConfig] = None

    class Config:
        arbitrary_types_allowed = True
