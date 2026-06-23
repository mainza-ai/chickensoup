import json
import logging
import functools
import hashlib
from typing import Any, Callable, Optional
import redis
from src.config import settings

logger = logging.getLogger("chickensoup.cache")

class RedisCache:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialize()

    def _initialize(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis successfully for caching.")
        except Exception as e:
            logger.warning(f"Redis caching is unavailable (will run without cache): {e}")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            return None
        try:
            val = self.redis_client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self.redis_client:
            return False
        try:
            self.redis_client.set(key, json.dumps(value), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
        return False

    def delete(self, key: str) -> bool:
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
        return False

    def invalidate_by_pattern(self, pattern: str) -> int:
        if not self.redis_client:
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis invalidate_by_pattern error: {e}")
        return 0

    def invalidate_all(self) -> bool:
        if not self.redis_client:
            return False
        try:
            # We invalidate keys with our prefixes
            self.invalidate_by_pattern("cache:neo4j:*")
            self.invalidate_by_pattern("cache:llm:*")
            self.invalidate_by_pattern("cache:mcp:*")
            self.invalidate_by_pattern("cache:test:*")
            return True
        except Exception as e:
            logger.error(f"Redis invalidate_all error: {e}")
        return False

# Single global cache instance
cache_store = RedisCache()

def cache_decorator(prefix: str, ttl: int = 300):
    """
    Decorator to cache function results in Redis.
    Generates a cache key based on the function name and arguments.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate a stable key representation of arguments
            # Avoid self/cls in key generation for methods
            args_to_serialize = args
            if args and hasattr(args[0], '__class__') and func.__name__ in dir(args[0].__class__):
                args_to_serialize = args[1:]
            
            arg_str = f"{args_to_serialize}:{sorted(kwargs.items())}"
            hash_sig = hashlib.md5(arg_str.encode('utf-8')).hexdigest()
            cache_key = f"cache:{prefix}:{func.__name__}:{hash_sig}"
            
            cached_val = cache_store.get(cache_key)
            if cached_val is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_val
            
            result = func(*args, **kwargs)
            cache_store.set(cache_key, result, ttl=ttl)
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            args_to_serialize = args
            if args and hasattr(args[0], '__class__') and func.__name__ in dir(args[0].__class__):
                args_to_serialize = args[1:]
            
            arg_str = f"{args_to_serialize}:{sorted(kwargs.items())}"
            hash_sig = hashlib.md5(arg_str.encode('utf-8')).hexdigest()
            cache_key = f"cache:{prefix}:{func.__name__}:{hash_sig}"
            
            cached_val = cache_store.get(cache_key)
            if cached_val is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_val
            
            result = await func(*args, **kwargs)
            cache_store.set(cache_key, result, ttl=ttl)
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator
