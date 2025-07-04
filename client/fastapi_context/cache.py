import asyncio
import importlib
import inspect
import json
import time
from typing import Union, Any, Dict
from functools import wraps

from pydantic import BaseModel, TypeAdapter
from starlette.responses import JSONResponse, PlainTextResponse, HTMLResponse, StreamingResponse, RedirectResponse

from fastapi_context.config import CacheConfig
from fastapi_context.const import CacheHitEnum
from fastapi_context.plugins.cache_plugins.base import PLUGINS_IMPORT_MAP
from fastapi_context.utils.common_utils import JsonEncoder, get_typed_return_annotation


class CacheData(BaseModel):
    timestamp: int
    expire_at: Union[int, None]
    data: Any
    extra: dict


class Cache:

    def __init__(self, cache_config: CacheConfig):
        self.cache_config = cache_config
        plugin_import_path = PLUGINS_IMPORT_MAP.get(cache_config.broker)
        assert plugin_import_path and isinstance(plugin_import_path, str)
        module_path, plugin_class = plugin_import_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        self.plugin = getattr(module, plugin_class)(cache_config=cache_config)

    def cache(self, *, prefix: str = "", key: Union[str, None] = None, ttl: Union[int, None] = None, nx: bool = True):
        """
        Method to access the cache plugin.
        """
        def outer_wrapper(func):
            @wraps(func)
            async def inner_wrapper(*args, **kwargs):
                is_async = asyncio.iscoroutinefunction(func)
                cache_key = key if key else self.gen_key(prefix, func, *args, **kwargs)
                cache_result = await self.get(cache_key, is_async=is_async)
                if cache_result:
                    cache_data = CacheData(**json.loads(cache_result))
                    response_annotation = get_typed_return_annotation(func)
                    resp = self.format_response_from_cache_data(cache_data, response_annotation=response_annotation)
                else:
                    resp = await func(*args, **kwargs) if is_async else await asyncio.to_thread(func, *args, **kwargs)
                    if isinstance(resp, (StreamingResponse, RedirectResponse)):
                        return resp
                    cache_data = self.get_cache_data_from_response(resp, ttl)
                    await self.set(
                        key=cache_key,
                        value=json.dumps(cache_data.model_dump(), cls=JsonEncoder),
                        ttl=ttl,
                        nx=nx,
                        is_async=is_async
                    )
                return resp
            return inner_wrapper
        return outer_wrapper

    async def get(self, key, is_async: bool) -> Union[str, bytes, None]:
        if is_async:
            return await self.plugin.broker.async_get(key)
        else:
            return await asyncio.to_thread(self.plugin.broker.get, key)

    async def set(self, key, value, ttl=None, nx=True, is_async: bool = True) -> bool:
        if is_async:
            return await self.plugin.broker.async_set(key, value, ttl=ttl, nx=nx)
        else:
            return await asyncio.to_thread(self.plugin.broker.set, key, value, ttl=ttl, nx=nx)

    def gen_key(self, prefix, func, *args, **kwargs) -> str:
        sig = inspect.signature(func)
        func_args = sig.bind(*args, **kwargs)
        func_args.apply_defaults()
        args_str = ",".join(f"{arg}={val}" for arg, val in func_args.arguments.items())
        return f"{prefix}{func.__module__}.{func.__name__}({args_str})"

    def get_cache_data_from_response(self, response: Any, ttl: Union[int, None] = None) -> CacheData:
        extra = {}
        if isinstance(response, JSONResponse):
            data = json.loads(response.body.decode('utf-8')) if response.body else None
            extra["headers"] = dict(response.headers)
        elif isinstance(response, (PlainTextResponse, HTMLResponse)):
            data = response.body.decode('utf-8') if response.body else None
            extra["headers"] = dict(response.headers)
        elif isinstance(response, (str, bytes, float, int, dict, list, tuple, set)):
            data = response
        elif isinstance(response, BaseModel):
            data = response.model_dump()
        else:
            if hasattr(response, "__dict__"):
                data = response.__dict__
            else:
                raise ValueError(f"Unsupported response type: {type(response)}")
        timestamp = int(time.time() * 1000)
        expire_at = int(timestamp + ttl * 1000) if ttl else None
        cache_data = CacheData(timestamp=timestamp, expire_at=expire_at, data=data, extra=extra)
        return cache_data

    def format_response_from_cache_data(self, cache_data: CacheData, response_annotation: Any = None) -> Any:
        if response_annotation is None:
            return cache_data.data
        if (inspect.isclass(response_annotation) and
                issubclass(response_annotation, (PlainTextResponse, HTMLResponse, JSONResponse))):
            headers = self.set_hit_headers(cache_data=cache_data)
            return response_annotation(content=cache_data.data, headers=headers)
        try:
            return TypeAdapter(response_annotation).validate_python(cache_data.data)
        except Exception as error:
            # todo
            raise error

    def set_hit_headers(self, cache_data: CacheData) -> Dict[str, str]:
        headers = cache_data.extra.get("headers", {})
        headers["X-Cache-Hit"] = CacheHitEnum.HIT.value
        timestamp = int(time.time() * 1000)
        # 暴露缓存剩余时间最大时间限度为一年
        ttl = (cache_data.expire_at - timestamp) if cache_data.expire_at else 3600 * 24 * 365
        headers["Cache-Control"] = f"public, max-age={max(ttl, 0)}"
        return headers


__all__ = ["Cache", "CacheData"]
