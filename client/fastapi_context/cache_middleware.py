from typing import Union

from starlette.types import ASGIApp

from client.fastapi_context.config import CacheConfig


class CacheMiddleware:

    def __init__(self, app: ASGIApp, cache_config: CacheConfig):
        self.app = app
        self.cache_config = cache_config
