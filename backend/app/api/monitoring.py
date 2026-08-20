"""
Personal AI OS - Monitoring API
系统监控接口
"""
import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db, engine
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.memory import Memory
from app.models.document import Document
from app.models.conversation import Conversation

router = APIRouter(prefix="/monitoring", tags=["系统监控"])


@router.get("/health")
async def health_check():
    """系统健康检查"""
    checks = {}

    # 数据库检查
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__('sqlalchemy').text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Redis 检查
    try:
        from app.services.rate_limiter import rate_limiter
        redis = await rate_limiter._get_redis()
        if redis:
            await redis.ping()
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "not connected (using memory fallback)"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"

    # AI 服务检查
    try:
        from app.services.ai_service import create_ai_service
        checks["ai_service"] = "available"
    except Exception as e:
        checks["ai_service"] = f"unavailable: {str(e)}"

    overall = "healthy" if all(v == "healthy" or "fallback" in v for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "checks": checks,
        "timestamp": time.time()
    }


@router.get("/stats")
async def system_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """系统统计信息"""
    # 用户统计
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar() or 0

    # 记忆统计
    memory_count = (await db.execute(
        select(func.count()).select_from(Memory).where(Memory.user_id == current_user_id)
    )).scalar() or 0

    # 文档统计
    doc_count = (await db.execute(
        select(func.count()).select_from(Document).where(Document.user_id == current_user_id)
    )).scalar() or 0

    # 对话统计
    conv_count = (await db.execute(
        select(func.count()).select_from(Conversation).where(Conversation.user_id == current_user_id)
    )).scalar() or 0

    # 知识切片统计
    from app.models.knowledge import KnowledgeChunk
    chunk_count = (await db.execute(
        select(func.count()).select_from(KnowledgeChunk)
    )).scalar() or 0

    return {
        "users": user_count,
        "memories": memory_count,
        "documents": doc_count,
        "conversations": conv_count,
        "knowledge_chunks": chunk_count,
        "timestamp": time.time()
    }


@router.get("/version")
async def version_info():
    """版本信息"""
    from app.core.config import settings
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "python": "3.12",
        "fastapi": "0.115+",
        "database": "PostgreSQL + pgvector" if "postgresql" in settings.DATABASE_URL else "SQLite"
    }
