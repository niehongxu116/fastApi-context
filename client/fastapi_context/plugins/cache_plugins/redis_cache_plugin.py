from typing import Union, Literal

from fastapi_context.config import RedisConfig
from fastapi_context.const import CacheBrokerEnum
from fastapi_context.plugins.cache_plugins.base import CacheBroker, CachePluginBase
from fastapi_context.utils.redis_utils import RedisUtils


class RedisCacheBroker(CacheBroker):

    def __init__(self, redis_config: RedisConfig):
        self.async_connection_pool = RedisUtils.init_redis_connection_pool(redis_config=redis_config, is_async=True)
        self.sync_connection_pool = RedisUtils.init_redis_connection_pool(redis_config=redis_config, is_async=False)

    def get_redis(self, is_async: bool = True):
        connection_pool = self.async_connection_pool if is_async else self.sync_connection_pool
        return RedisUtils.get_redis_from_connection_pool(connection_pool, is_async=is_async)

    def set(self, key: str, value: Union[str, bytes], ttl: Union[int, None] = None, nx: bool = True) -> bool:
        client = self.get_redis(is_async=False)
        return bool(client.set(key, value, ex=ttl, nx=nx))

    async def async_set(self, key: str, value: Union[str, bytes], ttl: Union[int, None] = None, nx: bool = True) -> bool:
        client = self.get_redis(is_async=True)
        return bool(await client.set(key, value, ex=ttl, nx=nx))

    def get(self, key: str) -> Union[str, bytes, None]:
        client = self.get_redis(is_async=False)
        return client.get(key)

    async def async_get(self, key: str) -> Union[str, bytes, None]:
        client = self.get_redis(is_async=True)
        return await client.get(key)

    def delete(self, key: str) -> bool:
        client = self.get_redis(is_async=False)
        return bool(client.delete(key))

    async def async_delete(self, key: str) -> bool:
        client = self.get_redis(is_async=True)
        return bool(await client.delete(key))


class RedisCachePlugin(CachePluginBase):
    type: Literal[CacheBrokerEnum.REDIS] = CacheBrokerEnum.REDIS

    def init_cache_broker(self):
        assert self.cache_config.redis_config
        self.broker = RedisCacheBroker(redis_config=self.cache_config.redis_config)


__all__ = ["RedisCachePlugin"]
