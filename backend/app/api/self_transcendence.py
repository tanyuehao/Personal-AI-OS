"""
Personal AI OS - Self-Transcendence API
自我超越闭环接口
"""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.self_transcendence import get_self_transcendence_engine

router = APIRouter(prefix="/self-transcendence", tags=["自我超越闭环"])


class CycleResponse(BaseModel):
    cycle_id: str
    cycle_type: str
    phase_results: dict
    insights: List[str]
    improvements: List[str]
    next_actions: List[str]
    confidence: float
    timestamp: str


@router.post("/run", response_model=CycleResponse)
async def run_cycle(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    运行完整的自我超越循环

    串联所有模块：感知 → 理解 → 预测 → 规划 → 行动 → 学习 → 改进
    """
    engine = get_self_transcendence_engine(db)
    result = await engine.run_full_cycle(current_user_id)

    return CycleResponse(
        cycle_id=result.cycle_id,
        cycle_type=result.cycle_type,
        phase_results=result.phase_results,
        insights=result.insights,
        improvements=result.improvements,
        next_actions=result.next_actions,
        confidence=result.confidence,
        timestamp=result.timestamp
    )


@router.get("/health")
async def get_system_health(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取系统健康状态"""
    engine = get_self_transcendence_engine(db)
    return await engine.get_system_health(current_user_id)
