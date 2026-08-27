"""
Personal AI OS - Memory Evidence Schemas
记忆证据请求/响应模型
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EvidenceCreateRequest(BaseModel):
    """创建记忆证据请求"""
    source_type: str = Field(..., description="CONVERSATION/DOCUMENT/DECISION/MANUAL")
    source_id: Optional[str] = Field(None, description="UUID of source entity (required for DOCUMENT/CONVERSATION/DECISION)")
    source_span: Optional[str] = Field(None, max_length=5000)
    evidence_kind: str = Field("DIRECT_QUOTE", description="DIRECT_QUOTE/PARAPHRASE/OBSERVATION/USER_CORRECTION")
    evidence_strength: float = Field(1.0, ge=0, le=1)
    observed_at: Optional[datetime] = None


class EvidenceResponse(BaseModel):
    """记忆证据响应"""
    evidence_id: str
    memory_id: str
    user_id: str
    source_type: str
    source_id: Optional[str] = None
    source_span: Optional[str] = None
    evidence_kind: str
    evidence_strength: float
    observed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
