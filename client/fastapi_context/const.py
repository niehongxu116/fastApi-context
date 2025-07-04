from enum import Enum


class CacheBrokerEnum(str, Enum):
    REDIS = "redis"
    MEMORY = "memory"


class CacheHitEnum(str, Enum):
    HIT = "hit"
    MISS = "miss"
