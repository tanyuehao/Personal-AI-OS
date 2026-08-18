"""
Personal AI OS - Knowledge Schemas
知识库请求/响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field


# ========== 请求模型 ==========

class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., description="搜索查询内容")
    limit: Optional[int] = Field(10, ge=1, le=50, description="返回结果数量")
    document_id: Optional[str] = Field(None, description="限定在某个文档中搜索")


# ========== 响应模型 ==========

class KnowledgeChunkResponse(BaseModel):
    """知识切片响应"""
    chunk_id: str
    content: str
    document_id: str
    chunk_index: int
    relevance_score: Optional[float] = None
    topic: Optional[str] = None
    tags: Optional[List[str]] = None


class KnowledgeSearchResponse(BaseModel):
    """知识库搜索响应"""
    items: List[KnowledgeChunkResponse]
    total: int
    query: str
