from enum import Enum


class CacheBrokerEnum(str, Enum):
    REDIS = "redis"
    MEMORY = "memory"
