"""
Personal AI OS - Memory Network API
记忆网络接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.memory_network import get_memory_network, ASSOCIATION_TYPES

router = APIRouter(prefix="/memory-network", tags=["记忆网络"])


class AssociationCreateRequest(BaseModel):
    """创建关联请求"""
    source_memory_id: str
    target_memory_id: str
    association_type: str = "semantic"
    strength: float = 1.0
    context: str = ""


class ClusterResponse(BaseModel):
    """聚类响应"""
    name: str
    type: str
    description: str
    memory_count: int


@router.get("/stats")
async def get_network_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取记忆网络统计

    返回记忆数量、关联数量、聚类数量、平均强度等。
    """
    network = get_memory_network(db)
    return await network.get_network_stats(current_user_id)


@router.post("/reinforce/{memory_id}")
async def reinforce_memory(
    memory_id: str,
    reinforcement: float = Query(0.1, ge=0, le=0.5),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    强化记忆（复习后调用）

    增加记忆的强度，减缓遗忘速度。
    """
    network = get_memory_network(db)
    await network.reinforce_memory(current_user_id, memory_id, reinforcement)
    return {"message": "记忆已强化", "memory_id": memory_id}


@router.post("/batch-reinforce")
async def batch_reinforce(
    memory_ids: List[str],
    reinforcement: float = Query(0.1, ge=0, le=0.5),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    批量强化记忆
    """
    network = get_memory_network(db)
    await network.batch_reinforce_memories(current_user_id, memory_ids, reinforcement)
    return {"message": f"已强化 {len(memory_ids)} 条记忆"}


@router.post("/association")
async def create_association(
    request: AssociationCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    创建记忆关联
    """
    network = get_memory_network(db)
    association = await network.create_association(
        user_id=current_user_id,
        source_memory_id=request.source_memory_id,
        target_memory_id=request.target_memory_id,
        association_type=request.association_type,
        strength=request.strength,
        context=request.context
    )
    return {"message": "关联已创建", "association_id": str(association.association_id)}


@router.get("/recall/{memory_id}")
async def recall_associations(
    memory_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    联想召回 - 基于一个记忆召回相关记忆
    """
    network = get_memory_network(db)
    associations = await network.recall_associations(current_user_id, memory_id, limit)
    return {"associations": associations, "count": len(associations)}


@router.post("/cluster")
async def cluster_memories(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    记忆聚类 - 将相似记忆分组
    """
    network = get_memory_network(db)
    clusters = await network.cluster_memories(current_user_id)
    return {"clusters": clusters, "count": len(clusters)}


@router.get("/strengths")
async def get_memory_strengths(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有记忆的强度信息
    """
    network = get_memory_network(db)

    # 先更新所有强度
    await network.update_memory_strengths(current_user_id)

    # 获取强度记录
    from app.models.memory_network import MemoryStrength
    from sqlalchemy import select

    result = await db.execute(
        select(MemoryStrength).where(
            MemoryStrength.user_id == current_user_id
        ).order_by(MemoryStrength.current_strength.desc())
    )
    strengths = result.scalars().all()

    return {
        "strengths": [
            {
                "memory_id": str(s.memory_id),
                "base_strength": s.base_strength,
                "current_strength": s.current_strength,
                "decay_rate": s.decay_rate,
                "review_count": int(s.review_count),
                "last_reviewed": s.last_reviewed.isoformat() if s.last_reviewed else None
            }
            for s in strengths
        ]
    }


@router.get("/types")
async def get_association_types():
    """获取关联类型定义"""
    return {"types": ASSOCIATION_TYPES}
