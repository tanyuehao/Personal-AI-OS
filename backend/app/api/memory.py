"""
Personal AI OS - Memory API
记忆管理接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.memory import Memory, MemoryType
from app.schemas.memory import (
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemoryResponse,
    MemoryListResponse,
    MemorySearchRequest
)

router = APIRouter(prefix="/memory", tags=["记忆管理"])


# ========== 固定路径（必须在 {memory_id} 之前） ==========

@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    request: MemoryCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建记忆"""
    try:
        memory_type = MemoryType(request.memory_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的记忆类型: {request.memory_type}"
        )

    memory = Memory(
        user_id=current_user_id,
        memory_type=memory_type.value,
        content=request.content,
        source=request.source,
        importance=request.importance or 0.5,
        confidence=request.confidence or 0.8
    )

    db.add(memory)
    await db.flush()
    await db.refresh(memory)

    return MemoryResponse.model_validate(memory)


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    page: int = 1,
    limit: int = 20,
    memory_type: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取记忆列表"""
    query = select(Memory).where(Memory.user_id == current_user_id)

    if memory_type:
        query = query.where(Memory.memory_type == memory_type)

    count_query = select(func.count()).select_from(Memory).where(Memory.user_id == current_user_id)
    if memory_type:
        count_query = count_query.where(Memory.memory_type == memory_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Memory.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    memories = result.scalars().all()

    return MemoryListResponse(
        items=[MemoryResponse.model_validate(mem) for mem in memories],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/candidates", response_model=MemoryListResponse)
async def get_candidate_memories(
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取待确认的记忆候选"""
    query = select(Memory).where(
        Memory.user_id == current_user_id,
        Memory.is_confirmed == "PENDING"
    ).order_by(Memory.created_at.desc()).limit(limit)

    result = await db.execute(query)
    memories = result.scalars().all()

    count_query = select(func.count()).select_from(Memory).where(
        Memory.user_id == current_user_id,
        Memory.is_confirmed == "PENDING"
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return MemoryListResponse(
        items=[MemoryResponse.model_validate(mem) for mem in memories],
        total=total,
        page=1,
        limit=limit
    )


@router.post("/search", response_model=MemoryListResponse)
async def search_memories(
    request: MemorySearchRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """搜索记忆"""
    query = select(Memory).where(Memory.user_id == current_user_id)

    if request.memory_type:
        query = query.where(Memory.memory_type == request.memory_type)

    if request.query:
        safe_query = request.query.replace("%", "\\%").replace("_", "\\_")
        query = query.where(Memory.content.ilike(f"%{safe_query}%", escape="\\"))

    if request.min_importance:
        query = query.where(Memory.importance >= request.min_importance)

    query = query.order_by(Memory.importance.desc(), Memory.created_at.desc())
    query = query.limit(request.limit or 20)

    result = await db.execute(query)
    memories = result.scalars().all()

    return MemoryListResponse(
        items=[MemoryResponse.model_validate(mem) for mem in memories],
        total=len(memories),
        page=1,
        limit=request.limit or 20
    )


@router.get("/stats/summary")
async def get_memory_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取记忆统计信息"""
    stats = {}
    for memory_type in MemoryType:
        result = await db.execute(
            select(func.count()).select_from(Memory).where(
                Memory.user_id == current_user_id,
                Memory.memory_type == memory_type.value
            )
        )
        stats[memory_type.value] = result.scalar()

    total_result = await db.execute(
        select(func.count()).select_from(Memory).where(
            Memory.user_id == current_user_id
        )
    )
    stats["total"] = total_result.scalar()

    avg_result = await db.execute(
        select(func.avg(Memory.importance)).where(
            Memory.user_id == current_user_id
        )
    )
    avg_importance = avg_result.scalar()
    stats["avg_importance"] = round(float(avg_importance), 2) if avg_importance else 0

    return stats


@router.post("/confirm-all", response_model=dict)
async def confirm_all_memories(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """一键确认所有候选记忆"""
    result = await db.execute(
        select(Memory).where(
            Memory.user_id == current_user_id,
            Memory.is_confirmed == "PENDING"
        )
    )
    memories = result.scalars().all()

    for memory in memories:
        memory.is_confirmed = "CONFIRMED"

    await db.flush()

    return {"confirmed": len(memories)}


@router.post("/reject-all", response_model=dict)
async def reject_all_memories(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """一键拒绝所有候选记忆"""
    result = await db.execute(
        select(Memory).where(
            Memory.user_id == current_user_id,
            Memory.is_confirmed == "PENDING"
        )
    )
    memories = result.scalars().all()

    for memory in memories:
        memory.is_confirmed = "REJECTED"

    await db.flush()

    return {"rejected": len(memories)}


# ========== 动态路径（必须在固定路径之后） ==========

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取记忆详情"""
    result = await db.execute(
        select(Memory).where(
            Memory.memory_id == memory_id,
            Memory.user_id == current_user_id
        )
    )
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )

    return MemoryResponse.model_validate(memory)


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    request: MemoryUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新记忆"""
    result = await db.execute(
        select(Memory).where(
            Memory.memory_id == memory_id,
            Memory.user_id == current_user_id
        )
    )
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )

    if request.content is not None:
        memory.content = request.content
    if request.memory_type is not None:
        memory.memory_type = request.memory_type
    if request.importance is not None:
        memory.importance = request.importance
    if request.confidence is not None:
        memory.confidence = request.confidence
    if request.is_confirmed is not None:
        memory.is_confirmed = request.is_confirmed

    await db.flush()
    await db.refresh(memory)

    return MemoryResponse.model_validate(memory)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除记忆"""
    result = await db.execute(
        select(Memory).where(
            Memory.memory_id == memory_id,
            Memory.user_id == current_user_id
        )
    )
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )

    await db.delete(memory)


@router.post("/{memory_id}/confirm", response_model=MemoryResponse)
async def confirm_memory(
    memory_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """确认记忆候选"""
    result = await db.execute(
        select(Memory).where(
            Memory.memory_id == memory_id,
            Memory.user_id == current_user_id
        )
    )
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )

    memory.is_confirmed = "CONFIRMED"
    await db.flush()
    await db.refresh(memory)

    return MemoryResponse.model_validate(memory)


@router.post("/{memory_id}/reject", response_model=MemoryResponse)
async def reject_memory(
    memory_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """拒绝记忆候选"""
    result = await db.execute(
        select(Memory).where(
            Memory.memory_id == memory_id,
            Memory.user_id == current_user_id
        )
    )
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )

    memory.is_confirmed = "REJECTED"
    await db.flush()
    await db.refresh(memory)

    return MemoryResponse.model_validate(memory)
