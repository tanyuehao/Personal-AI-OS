"""
Personal AI OS - Memory Evidence Model
记忆证据表 — 一等公民
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, ForeignKeyConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.types import CompatibleUUID as UUID

from app.core.database import Base


class MemoryEvidence(Base):
    """记忆证据表 — 一等公民"""
    __tablename__ = "memory_evidence"

    evidence_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    source_type = Column(String(20), nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=True)
    source_span = Column(Text, nullable=True)
    evidence_kind = Column(String(20), nullable=False, default="DIRECT_QUOTE")
    evidence_strength = Column(Float, nullable=False, default=1.0)
    observed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    memory = relationship("Memory", back_populates="evidence_records")

    __table_args__ = (
        # Composite FK: evidence must reference a memory owned by the same user
        ForeignKeyConstraint(
            ["memory_id", "user_id"],
            ["memories.memory_id", "memories.user_id"],
            name="fk_evidence_memory_user",
            ondelete="CASCADE",
        ),
        Index("ix_evidence_memory", "memory_id"),
        Index("ix_evidence_user", "user_id"),
        Index("ix_evidence_source", "source_type", "source_id"),
        CheckConstraint("source_type IN ('CONVERSATION','DOCUMENT','DECISION','MANUAL','LEGACY_UNKNOWN')", name="chk_evidence_source_type"),
        CheckConstraint("evidence_kind IN ('DIRECT_QUOTE','PARAPHRASE','OBSERVATION','USER_CORRECTION')", name="chk_evidence_kind"),
        CheckConstraint("evidence_strength >= 0.0 AND evidence_strength <= 1.0", name="chk_evidence_strength"),
        # Provenance-shape constraint (errata C)
        CheckConstraint(
            "(source_type IN ('DOCUMENT','CONVERSATION','DECISION') AND source_id IS NOT NULL) "
            "OR (source_type IN ('MANUAL','LEGACY_UNKNOWN') AND source_id IS NULL)",
            name="chk_evidence_provenance_shape",
        ),
    )

    def __repr__(self):
        return f"<MemoryEvidence {self.source_type}: {self.evidence_id}>"
