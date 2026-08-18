"""
Personal AI OS - Usage API
使用量统计接口
"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id
from app.services.rate_limiter import rate_limiter

router = APIRouter(prefix="/usage", tags=["使用量统计"])


@router.get("/stats")
async def get_usage_stats(current_user_id: str = Depends(get_current_user_id)):
    """获取当前用户的使用统计"""
    stats = await rate_limiter.get_usage_stats(current_user_id)
    return stats


@router.get("/limits")
async def get_rate_limits():
    """获取 API 速率限制配置"""
    return {
        "rpm_limit": rate_limiter.config.rpm,
        "tpm_limit": rate_limiter.config.tpm,
        "burst_limit": rate_limiter.config.burst,
        "description": {
            "rpm": "每分钟请求数限制",
            "tpm": "每分钟 Token 数限制",
            "burst": "1秒内最大并发请求数"
        }
    }
