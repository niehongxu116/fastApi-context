from redis import BlockingConnectionPool
from redis import Redis
from redis.asyncio import BlockingConnectionPool as AsyncBlockingConnectionPool
from redis.asyncio.client import Redis as aioRedis


from fastapi_context.config import RedisConfig


class RedisUtils:

    @classmethod
    def init_redis_connection_pool(cls, redis_config: RedisConfig, is_async: bool = True):
        host = redis_config.host
        port = redis_config.port
        password = redis_config.password
        db = redis_config.db
        if password and len(password) > 0:
            url = f"redis://default:{password}@{host}:{port}/{db}"
        else:
            url = f"redis://{host}:{port}/{db}"
        pool_class = AsyncBlockingConnectionPool if is_async else BlockingConnectionPool
        return pool_class.from_url(
            url,
            decode_responses=redis_config.decode_responses,
            max_connections=redis_config.max_connections,
            health_check_interval=redis_config.health_check_interval,
            socket_connect_timeout=redis_config.socket_connect_timeout,
            socket_timeout=redis_config.socket_timeout,
        )

    @classmethod
    def get_redis_from_connection_pool(cls, connection_pool, is_async: bool = True):
        return aioRedis(connection_pool=connection_pool) if is_async else Redis(connection_pool=connection_pool)
