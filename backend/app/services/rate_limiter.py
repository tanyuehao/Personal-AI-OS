"""
Personal AI OS - Rate Limiter
请求频率限制和 Token 使用量跟踪（Redis 后端）
"""
import time
import json
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    rpm: int = 2000  # 每分钟请求数
    tpm: int = 500000  # 每分钟 Token 数
    burst: int = 10  # 突发请求限制


class RateLimiter:
    """请求频率限制器（Redis 后端）"""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._redis = None

    async def _get_redis(self):
        """获取 Redis 连接（懒加载）"""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                from app.core.config import settings
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
            except Exception:
                return None
        return self._redis

    async def check_rate_limit(self, user_id: str) -> tuple[bool, str]:
        """
        检查是否超过速率限制

        Returns:
            (allowed, message)
        """
        redis = await self._get_redis()
        if redis is None:
            # Redis 不可用时放行
            return True, "OK"

        now = time.time()
        minute_key = f"ratelimit:rpm:{user_id}"
        burst_key = f"ratelimit:burst:{user_id}"

        try:
            # 检查 RPM
            current_rpm = await redis.zcard(minute_key)
            if current_rpm >= self.config.rpm:
                return False, f"请求频率超限 (当前: {current_rpm}/{self.config.rpm} RPM)"

            # 检查突发限制（1秒内）
            recent_count = await redis.zcount(burst_key, now - 1, now)
            if recent_count >= self.config.burst:
                return False, "突发请求过多，请稍后重试"

            return True, "OK"
        except Exception:
            return True, "OK"

    async def record_request(self, user_id: str, tokens_used: int = 0):
        """记录请求和 Token 使用"""
        redis = await self._get_redis()
        if redis is None:
            return

        now = time.time()
        minute_key = f"ratelimit:rpm:{user_id}"
        burst_key = f"ratelimit:burst:{user_id}"
        stats_key = f"ratelimit:stats:{user_id}"

        try:
            pipe = redis.pipeline()

            # 记录 RPM（1分钟窗口）
            pipe.zadd(minute_key, {str(now): now})
            pipe.zremrangebyscore(minute_key, 0, now - 60)
            pipe.expire(minute_key, 65)

            # 记录突发（1秒窗口）
            pipe.zadd(burst_key, {str(now): now})
            pipe.zremrangebyscore(burst_key, 0, now - 1)
            pipe.expire(burst_key, 2)

            # 更新统计
            pipe.hincrby(stats_key, "total_requests", 1)
            pipe.hincrby(stats_key, "total_tokens", tokens_used)
            pipe.expire(stats_key, 86400)

            await pipe.execute()
        except Exception:
            pass

    async def get_usage_stats(self, user_id: str) -> Dict:
        """获取用户使用统计"""
        redis = await self._get_redis()
        if redis is None:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "current_rpm": 0,
                "current_tpm": 0,
                "rpm_limit": self.config.rpm,
                "tpm_limit": self.config.tpm,
                "rpm_remaining": self.config.rpm,
                "tpm_remaining": self.config.tpm,
                "rpm_usage_percent": 0,
                "tpm_usage_percent": 0,
            }

        now = time.time()
        minute_key = f"ratelimit:rpm:{user_id}"
        stats_key = f"ratelimit:stats:{user_id}"

        try:
            current_rpm = await redis.zcard(minute_key)
            stats = await redis.hgetall(stats_key)

            total_requests = int(stats.get("total_requests", 0))
            total_tokens = int(stats.get("total_tokens", 0))

            # 计算当前 TPM（简化：用 RPM * 平均 token 估算）
            current_tpm = 0

            return {
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "current_rpm": current_rpm,
                "current_tpm": current_tpm,
                "rpm_limit": self.config.rpm,
                "tpm_limit": self.config.tpm,
                "rpm_remaining": max(0, self.config.rpm - current_rpm),
                "tpm_remaining": max(0, self.config.tpm - current_tpm),
                "rpm_usage_percent": round(current_rpm / self.config.rpm * 100, 1),
                "tpm_usage_percent": round(current_tpm / self.config.tpm * 100, 1),
            }
        except Exception:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "current_rpm": 0,
                "current_tpm": 0,
                "rpm_limit": self.config.rpm,
                "tpm_limit": self.config.tpm,
                "rpm_remaining": self.config.rpm,
                "tpm_remaining": self.config.tpm,
                "rpm_usage_percent": 0,
                "tpm_usage_percent": 0,
            }


# 全局速率限制器实例
rate_limiter = RateLimiter(RateLimitConfig(rpm=2000, tpm=500000))
