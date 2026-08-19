"""
Personal AI OS - Reflection API
离线整理接口
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.reflection import get_reflection_service

router = APIRouter(prefix="/reflection", tags=["离线整理"])


@router.get("/duplicates")
async def find_duplicates(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    查找重复或相似的记忆

    分析用户的所有已确认记忆，找出内容重复或高度相似的记忆。
    """
    service = get_reflection_service(db)
    clusters = await service.find_duplicate_memories(current_user_id)

    return {
        "clusters": [
            {
                "memory_ids": c.memory_ids,
                "representative_content": c.representative_content,
                "suggested_action": c.suggested_action
            }
            for c in clusters
        ],
        "count": len(clusters)
    }


@router.get("/conflicts")
async def detect_conflicts(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    检测观点之间的冲突

    分析用户的所有活跃观点，检测矛盾或不兼容的观点。
    """
    service = get_reflection_service(db)
    conflicts = await service.detect_belief_conflicts(current_user_id)

    return {
        "conflicts": conflicts,
        "count": len(conflicts),
        "has_conflicts": len(conflicts) > 0
    }


@router.get("/weekly-summary")
async def get_weekly_summary(
    days: int = Query(7, ge=1, le=30),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    生成周度认知变化摘要

    统计最近 N 天的认知变化，包括新增记忆、观点变化、决策等。
    """
    service = get_reflection_service(db)
    summary = await service.generate_weekly_summary(current_user_id, days)

    return {
        "period": summary.period,
        "stats": {
            "new_memories": summary.new_memories,
            "confirmed_memories": summary.confirmed_memories,
            "new_beliefs": summary.new_beliefs,
            "belief_changes": summary.belief_changes,
            "new_decisions": summary.new_decisions
        },
        "insights": summary.key_insights,
        "trends": summary.cognitive_trends
    }


@router.post("/consolidate")
async def consolidate_memories(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    整合重复记忆

    根据重复检测结果，合并或删除重复记忆。
    """
    service = get_reflection_service(db)
    clusters = await service.find_duplicate_memories(current_user_id)

    consolidated = 0
    for cluster in clusters:
        if cluster.suggested_action == "keep_one" and len(cluster.memory_ids) > 1:
            # 保留第一个，删除其余
            from app.models.memory import Memory
            for memory_id in cluster.memory_ids[1:]:
                result = await db.execute(
                    select(Memory).where(
                        Memory.memory_id == memory_id,
                        Memory.user_id == current_user_id
                    )
                )
                memory = result.scalar_one_or_none()
                if memory:
                    await db.delete(memory)
                    consolidated += 1

    await db.flush()

    return {
        "consolidated": consolidated,
        "clusters_processed": len(clusters)
    }
