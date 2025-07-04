from abc import abstractmethod
from typing import Union

from fastapi_context.const import CacheBrokerEnum


class CacheBroker:

    @abstractmethod
    def set(self, key: str, value: Union[str, bytes], ttl: Union[int, None] = None, nx: bool = False) -> bool:
        """Set a value in the cache."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    async def async_set(self, key: str, value: Union[str, bytes], ttl: Union[int, None] = None, nx: bool = False) -> bool:
        """Asynchronously set a value in the cache."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    def get(self, key: str) -> Union[str, bytes, None]:
        """Get a value from the cache."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    async def async_get(self, key: str) -> Union[str, bytes, None]:
        """Asynchronously get a value from the cache."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    async def async_delete(self, key: str) -> bool:
        """Asynchronously delete a value from the cache."""
        raise NotImplementedError("This method should be implemented by subclasses.")


class CachePluginBase:

    def __init__(self, cache_config, *args, **kwargs):
        self.cache_config = cache_config
        self.broker = None
        self.init_cache_broker()

    @abstractmethod
    def init_cache_broker(self):
        ...


PLUGINS_IMPORT_MAP = {
    CacheBrokerEnum.REDIS: "fastapi_context.plugins.cache_plugins.redis_cache_plugin.RedisCachePlugin",
    CacheBrokerEnum.MEMORY: "fastapi_context.plugins.cache_plugins.memory_cache_plugin.MemoryCachePlugin",
}
