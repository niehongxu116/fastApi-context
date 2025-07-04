from asyncio import Lock
import time
from typing import Union, Dict, Literal
from threading import RLock

from pydantic import BaseModel

from fastapi_context.const import CacheBrokerEnum
from fastapi_context.plugins.cache_plugins.base import CacheBroker, CachePluginBase


class MemoryCacheModel(BaseModel):
    key: str
    value: Union[str, bytes]
    expire_at: Union[int, None] = None

    class Config:
        arbitrary_types_allowed = True


class MemoryCacheBroker(CacheBroker):

    def __init__(self):
        self.cache: Dict[str, MemoryCacheModel] = {}
        self.threading_lock = RLock()
        self.async_lock = Lock()

    def set(self, *args, **kwargs) -> bool:
        with self.threading_lock:
            return self.__set_inner(*args, **kwargs)

    async def async_set(self, *args, **kwargs) -> bool:
        async with self.async_lock:
            return self.__set_inner(*args, **kwargs)

    def get(self, key: str) -> Union[str, bytes, None]:
        cache = self.cache.get(key)
        if not cache:
            return None
        if cache.expire_at and cache.expire_at <= time.time():
            self.delete(key)
            return None
        return cache.value

    async def async_get(self, key: str) -> Union[str, bytes, None]:
        cache = self.cache.get(key)
        if not cache:
            return None
        if cache.expire_at and cache.expire_at <= time.time():
            await self.async_delete(key)
            return None
        return cache.value

    def delete(self, key: str) -> bool:
        with self.threading_lock:
            return True if self.cache.pop(key, False) else False

    async def async_delete(self, key: str) -> bool:
        async with self.async_lock:
            return True if self.cache.pop(key, False) else False

    def __set_inner(self, key: str, value: Union[str, bytes], ttl: Union[int, None] = None, nx: bool = True):
        cache_item = self.cache.get(key)
        if cache_item and (cache_item.expire_at is None or cache_item.expire_at >= time.time()) and nx:
            return False
        expire_at = round(time.time() + ttl) if ttl else None
        self.cache[key] = MemoryCacheModel(key=key, value=value, expire_at=expire_at)


class MemoryCachePlugin(CachePluginBase):
    type: Literal[CacheBrokerEnum.MEMORY] = CacheBrokerEnum.MEMORY

    def init_cache_broker(self):
        self.broker = MemoryCacheBroker()


__all__ = ["MemoryCachePlugin"]
