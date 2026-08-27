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
from app.models.evidence import MemoryEvidence
from app.schemas.memory import (
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemoryResponse,
    MemoryListResponse,
    MemorySearchRequest
)
from app.schemas.evidence import EvidenceCreateRequest, EvidenceResponse
from app.services.memory_lifecycle import transition_memory, add_evidence_to_memory, remove_evidence_from_memory

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

    # Server-controlled fields
    memory.assertion_kind = "USER_STATED"  # Server-controlled, ignore client
    memory.is_confirmed = "CONFIRMED"  # Manual creation is immediately confirmed

    db.add(memory)
    await db.flush()

    # Atomically create MANUAL evidence
    evidence = MemoryEvidence(
        memory_id=memory.memory_id,
        user_id=current_user_id,
        source_type="MANUAL",
        source_id=None,
        evidence_kind="DIRECT_QUOTE",
        evidence_strength=1.0
    )
    db.add(evidence)
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
        transition_memory(memory, "CONFIRMED")

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
        transition_memory(memory, "REJECTED")

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

    # Idempotent: already CONFIRMED is fine
    if memory.is_confirmed == "CONFIRMED":
        return MemoryResponse.model_validate(memory)

    transition_memory(memory, "CONFIRMED")
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

    transition_memory(memory, "REJECTED")
    await db.flush()
    await db.refresh(memory)

    return MemoryResponse.model_validate(memory)


# ========== Evidence CRUD endpoints ==========

@router.get("/{memory_id}/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    memory_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """列出记忆的所有证据"""
    # Validate memory ownership
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

    evidence_result = await db.execute(
        select(MemoryEvidence).where(
            MemoryEvidence.memory_id == memory_id
        ).order_by(MemoryEvidence.created_at.desc())
    )
    evidence_records = evidence_result.scalars().all()

    return [EvidenceResponse.model_validate(ev) for ev in evidence_records]


@router.post("/{memory_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def add_evidence(
    memory_id: str,
    request: EvidenceCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """为记忆添加证据"""
    # Validate memory ownership
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

    # Validate source ownership if source_id is provided
    if request.source_id and request.source_type in ("CONVERSATION", "DOCUMENT", "DECISION"):
        from app.models.conversation import Conversation
        from app.models.document import Document

        if request.source_type == "CONVERSATION":
            src_result = await db.execute(
                select(Conversation).where(
                    Conversation.conversation_id == request.source_id,
                    Conversation.user_id == current_user_id
                )
            )
            if not src_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="来源对话不存在或不属于当前用户"
                )
        elif request.source_type == "DOCUMENT":
            src_result = await db.execute(
                select(Document).where(
                    Document.document_id == request.source_id,
                    Document.user_id == current_user_id
                )
            )
            if not src_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="来源文档不存在或不属于当前用户"
                )

    evidence = await add_evidence_to_memory(
        memory=memory,
        db=db,
        source_type=request.source_type,
        source_id=request.source_id,
        source_span=request.source_span,
        evidence_kind=request.evidence_kind,
        evidence_strength=request.evidence_strength,
        observed_at=request.observed_at
    )
    await db.flush()
    await db.refresh(evidence)

    return EvidenceResponse.model_validate(evidence)


@router.delete("/{memory_id}/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_evidence(
    memory_id: str,
    evidence_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除记忆的证据"""
    # Validate memory ownership
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

    # Find the evidence
    ev_result = await db.execute(
        select(MemoryEvidence).where(
            MemoryEvidence.evidence_id == evidence_id,
            MemoryEvidence.memory_id == memory_id
        )
    )
    evidence = ev_result.scalar_one_or_none()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="证据不存在"
        )

    await remove_evidence_from_memory(memory, evidence, db)
    await db.flush()
