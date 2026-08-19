"""
Personal AI OS - Cache Service
简单内存缓存服务
"""
import time
from typing import Any, Optional
from functools import wraps


class SimpleCache:
    """简单内存缓存"""

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: 默认过期时间（秒）
        """
        self._cache = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            value, expire_at = self._cache[key]
            if expire_at > time.time():
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        ttl = ttl or self._default_ttl
        self._cache[key] = (value, time.time() + ttl)

    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()

    def cleanup(self):
        """清理过期缓存"""
        now = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if exp <= now]
        for k in expired:
            del self._cache[k]


# 全局缓存实例
cache = SimpleCache(default_ttl=300)


def cached(ttl: int = 300, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试获取缓存
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存储缓存
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
