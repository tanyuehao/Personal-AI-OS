"""Memory lifecycle state machine and evidence domain operations."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.memory import Memory
from app.models.evidence import MemoryEvidence


# Valid status transitions
VALID_TRANSITIONS = {
    None: {"PENDING"},  # new memory
    "PENDING": {"CONFIRMED", "REJECTED", "ARCHIVED"},
    "CONFIRMED": {"ARCHIVED"},
    "REJECTED": set(),  # terminal
    "ARCHIVED": {"PENDING"},
    "SUPERSEDED": set(),  # Phase 1A: no transitions
}


def validate_transition(current_status: str, new_status: str) -> bool:
    """Check if status transition is legal."""
    allowed = VALID_TRANSITIONS.get(current_status, set())
    return new_status in allowed


def transition_memory(memory: Memory, new_status: str):
    """Apply a validated status transition."""
    if not validate_transition(memory.is_confirmed, new_status):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition: {memory.is_confirmed} -> {new_status}"
        )
    if new_status == "SUPERSEDED":
        raise HTTPException(status_code=400, detail="SUPERSEDED not available in Phase 1A")
    memory.is_confirmed = new_status


async def on_source_deleted(source_type: str, source_id: UUID, db: AsyncSession):
    """Domain operation: called within existing transaction on source entity deletion."""
    result = await db.execute(
        select(MemoryEvidence).where(
            MemoryEvidence.source_type == source_type,
            MemoryEvidence.source_id == source_id
        )
    )
    evidence_records = result.scalars().all()
    for ev in evidence_records:
        await db.delete(ev)
    # Re-evaluate affected memories
    affected = {ev.memory_id for ev in evidence_records}
    for mid in affected:
        remaining = await db.execute(
            select(func.count()).select_from(MemoryEvidence).where(MemoryEvidence.memory_id == mid)
        )
        if remaining.scalar() == 0:
            mem_result = await db.execute(select(Memory).where(Memory.memory_id == mid))
            mem = mem_result.scalar_one_or_none()
            if mem and mem.is_confirmed in ("CONFIRMED", "PENDING"):
                mem.is_confirmed = "ARCHIVED"


async def on_sources_deleted(source_type: str, source_ids: List[UUID], db: AsyncSession):
    """Batch domain operation: delete evidence for multiple source entities."""
    if not source_ids:
        return
    result = await db.execute(
        select(MemoryEvidence).where(
            MemoryEvidence.source_type == source_type,
            MemoryEvidence.source_id.in_(source_ids)
        )
    )
    evidence_records = result.scalars().all()
    for ev in evidence_records:
        await db.delete(ev)
    affected = {ev.memory_id for ev in evidence_records}
    for mid in affected:
        remaining = await db.execute(
            select(func.count()).select_from(MemoryEvidence).where(MemoryEvidence.memory_id == mid)
        )
        if remaining.scalar() == 0:
            mem_result = await db.execute(select(Memory).where(Memory.memory_id == mid))
            mem = mem_result.scalar_one_or_none()
            if mem and mem.is_confirmed in ("CONFIRMED", "PENDING"):
                mem.is_confirmed = "ARCHIVED"


async def add_evidence_to_memory(memory: Memory, db: AsyncSession, **kwargs):
    """Add evidence to a memory with lifecycle validation."""
    if memory.is_confirmed == "REJECTED":
        raise HTTPException(status_code=409, detail="Cannot add evidence to REJECTED memory. Create a new memory instead.")
    if memory.is_confirmed == "SUPERSEDED":
        raise HTTPException(status_code=400, detail="SUPERSEDED memory cannot accept evidence in Phase 1A")
    if memory.is_confirmed == "ARCHIVED":
        memory.is_confirmed = "PENDING"
    evidence = MemoryEvidence(memory_id=memory.memory_id, user_id=memory.user_id, **kwargs)
    db.add(evidence)
    return evidence


async def remove_evidence_from_memory(memory: Memory, evidence: MemoryEvidence, db: AsyncSession):
    """Remove evidence from a memory with lifecycle validation."""
    await db.delete(evidence)
    # Count remaining
    remaining = await db.execute(
        select(func.count()).select_from(MemoryEvidence).where(MemoryEvidence.memory_id == memory.memory_id)
    )
    # -1 because the evidence we just deleted hasn't been flushed yet
    if remaining.scalar() <= 1:
        if memory.is_confirmed in ("CONFIRMED", "PENDING"):
            memory.is_confirmed = "ARCHIVED"
