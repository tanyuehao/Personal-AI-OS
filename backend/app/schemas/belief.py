"""
Personal AI OS - Belief Schemas
观点请求/响应模型
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 请求模型 ==========

class BeliefCreateRequest(BaseModel):
    """创建观点请求"""
    topic: str = Field(..., min_length=1, max_length=255, description="主题")
    content: str = Field(..., min_length=1, max_length=5000, description="观点内容")
    confidence: Optional[float] = Field(0.7, ge=0, le=1, description="可信度 0-1")
    supporting_evidence: Optional[List[str]] = Field(None, description="支持证据")
    opposing_evidence: Optional[List[str]] = Field(None, description="反对证据")


class BeliefUpdateRequest(BaseModel):
    """更新观点请求"""
    topic: Optional[str] = None
    content: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    supporting_evidence: Optional[List[str]] = None
    opposing_evidence: Optional[List[str]] = None
    status: Optional[str] = None
    change_reason: Optional[str] = Field(None, description="变化原因")


# ========== 响应模型 ==========

class BeliefResponse(BaseModel):
    """观点响应"""
    belief_id: str
    topic: str
    content: str
    confidence: float
    supporting_evidence: Optional[List[str]] = None
    opposing_evidence: Optional[List[str]] = None
    evolution_history: Optional[List[dict]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BeliefListResponse(BaseModel):
    """观点列表响应"""
    items: List[BeliefResponse]
    total: int
    page: int
    limit: int


class BeliefHistoryResponse(BaseModel):
    """观点历史响应"""
    history_id: str
    old_content: str
    new_content: str
    change_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
