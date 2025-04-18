import threading
from abc import abstractmethod
from typing import Union, Optional, Any, Callable

from jose import jwt
from redis import Redis
from redis.asyncio import BlockingConnectionPool
from redis.asyncio.client import Redis as aioRedis
from starlette._utils import is_async_callable
from starlette.concurrency import run_in_threadpool
from starlette_context.plugins import Plugin
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response
from starlette.types import Message

from fastAPi_context.config import ContextConfig, AuthPluginConfig, JWTAuthPluginConfig, RedisAuthPluginConfig
from fastAPi_context.exceptions import ContextMiddlewareError


class AuthPlugin(Plugin):

    def __init__(self, auth_plugin_config: Union[JWTAuthPluginConfig, RedisAuthPluginConfig]) -> None:
        self.key = auth_plugin_config.key
        self.auth_plugin_config = auth_plugin_config

    @abstractmethod
    async def check_token(self, request: Request):
        """auth token check"""
        ...

    async def check_url_white_list(self, request: Request):
        path = request.url.path
        if path in self.auth_plugin_config.url_white_list:
            return True

    async def enrich_response(self, arg: Union[Response, Message]) -> None:
        """Runs always on response."""
        ...

    async def process_request(
        self, request: Union[Request, HTTPConnection]
    ) -> Optional[Any]:
        """Runs always on request."""
        if await self.check_url_white_list(request=request):
            return None
        user_info = await self.check_token(request=request)
        if not user_info:
            raise ContextMiddlewareError(
                status_code=self.auth_plugin_config.error_status_code,
                error_code=self.auth_plugin_config.code,
                message="user not found",
            )
        return user_info

    async def get_token(self, request: Request) -> str:
        if isinstance(self.auth_plugin_config.get_token, str):
            token = request.headers.get(self.auth_plugin_config.get_token)
        elif isinstance(self.auth_plugin_config.get_token, Callable):
            token = self.auth_plugin_config.get_token(request)
        else:
            raise ContextMiddlewareError(
                status_code=self.auth_plugin_config.error_status_code,
                error_code=self.auth_plugin_config.code,
                message="get_token must be str or callable",
            )
        if not token:
            raise ContextMiddlewareError(
                status_code=self.auth_plugin_config.error_status_code,
                error_code=self.auth_plugin_config.code,
                message="token is required",
            )
        return token


class JwtAuthPlugin(AuthPlugin):

    def __init__(self, auth_plugin_config: JWTAuthPluginConfig):
        super().__init__(auth_plugin_config=auth_plugin_config)

    async def check_token(self, request: Request) -> Any:
        token = await self.get_token(request=request)
        try:
            payload = jwt.decode(
                token, self.auth_plugin_config.jwt_secret, algorithms=self.auth_plugin_config.jwt_algorithms
            )
            # todo format user schema
            return payload["payload"]
        except Exception as error:
            raise ContextMiddlewareError(
                status_code=self.auth_plugin_config.error_status_code,
                error_code=self.auth_plugin_config.code,
                message=f"token is invalid: {error}",
            )


redis_client_init_lock = threading.Lock()


class RedisAuthPlugin(AuthPlugin):

    def __init__(self, auth_plugin_config: RedisAuthPluginConfig):
        if auth_plugin_config.redis_client_function and not callable(auth_plugin_config.redis_client_function):
            raise ContextMiddlewareError(
                status_code=auth_plugin_config.error_status_code,
                error_code=auth_plugin_config.code,
                message="redis client must be callable",
            )
        if not auth_plugin_config.redis_config and not auth_plugin_config.redis_client_function:
            raise ContextMiddlewareError(
                status_code=auth_plugin_config.error_status_code,
                error_code=auth_plugin_config.code,
                message="redis config is required",
            )
        super().__init__(auth_plugin_config=auth_plugin_config)
        if not self.auth_plugin_config.redis_client_function:
            with redis_client_init_lock:
                self.redis_connection_pool = self._init_redis_connection_pool()
                self.auth_plugin_config.redis_client_function = self._redis_client_function

        self.redis_is_async = is_async_callable(self.auth_plugin_config.redis_client_function)

    async def check_token(self, request: Request) -> Any:
        token = await self.get_token(request=request)
        redis_handler = await self._get_redis_handler()
        redis_key = f"{self.auth_plugin_config.redis_token_key_prefix}{token}"
        if self.redis_is_async:
            redis_cache = await redis_handler.get(redis_key)
        else:
            redis_cache = await run_in_threadpool(redis_handler.get, redis_key)
        # todo format user schema
        return redis_cache

    async def _get_redis_handler(self) -> Union[aioRedis, Redis]:
        if self.redis_is_async:
            return await self.auth_plugin_config.redis_client_function()
        else:
            return await run_in_threadpool(self.auth_plugin_config.redis_client_function)

    def _init_redis_connection_pool(self):
        host = self.auth_plugin_config.redis_config.host
        port = self.auth_plugin_config.redis_config.port
        password = self.auth_plugin_config.redis_config.password
        db = self.auth_plugin_config.redis_config.db
        if password and len(password) > 0:
            url = f"redis://default:{password}@{host}:{port}/{db}"
        else:
            url = f"redis://{host}:{port}/{db}"
        return BlockingConnectionPool.from_url(
            url,
            decode_responses=self.auth_plugin_config.redis_config.decode_responses,
            max_connections=self.auth_plugin_config.redis_config.max_connections,
            health_check_interval=self.auth_plugin_config.redis_config.health_check_interval,
            socket_connect_timeout=self.auth_plugin_config.redis_config.socket_connect_timeout,
            socket_timeout=self.auth_plugin_config.redis_config.socket_timeout,
        )

    async def _redis_client_function(self):
        try:
            redis_conn = aioRedis(connection_pool=self.redis_connection_pool)
            await redis_conn.ping()
            return redis_conn
        except Exception as e:
            raise ContextMiddlewareError(
                status_code=self.auth_plugin_config.error_status_code,
                error_code=self.auth_plugin_config.code,
                message=f"redis client is invalid: {e}",
            )
