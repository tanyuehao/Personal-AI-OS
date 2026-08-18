"""
Personal AI OS - Memory Schemas
记忆请求/响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 请求模型 ==========

class MemoryCreateRequest(BaseModel):
    """创建记忆请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="记忆内容")
    memory_type: str = Field(..., description="记忆类型: FACT, EXPERIENCE, OPINION, DECISION, PREFERENCE")
    source: Optional[str] = Field(None, description="来源描述")
    importance: Optional[float] = Field(0.5, ge=0, le=1, description="重要程度 0-1")
    confidence: Optional[float] = Field(0.8, ge=0, le=1, description="可信程度 0-1")


class MemoryUpdateRequest(BaseModel):
    """更新记忆请求"""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    memory_type: Optional[str] = None
    importance: Optional[float] = Field(None, ge=0, le=1)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    is_confirmed: Optional[str] = None


class MemorySearchRequest(BaseModel):
    """搜索记忆请求"""
    query: Optional[str] = Field(None, description="搜索关键词")
    memory_type: Optional[str] = Field(None, description="记忆类型")
    min_importance: Optional[float] = Field(None, ge=0, le=1, description="最小重要程度")
    limit: Optional[int] = Field(20, ge=1, le=100, description="返回数量")


# ========== 响应模型 ==========

class MemoryResponse(BaseModel):
    """记忆响应"""
    memory_id: str
    memory_type: str
    content: str
    source: Optional[str] = None
    importance: float
    confidence: float
    frequency: int
    is_confirmed: str
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    """记忆列表响应"""
    items: List[MemoryResponse]
    total: int
    page: int
    limit: int
