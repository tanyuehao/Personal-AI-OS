"""
Personal AI OS - Document Schemas
文档请求/响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


# ========== 响应模型 ==========

class DocumentResponse(BaseModel):
    """文档信息响应"""
    document_id: str
    file_name: str
    file_type: str
    file_size: int
    source: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    status: str
    status_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str
    file_name: str
    status: str
    message: str


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    items: List[DocumentResponse]
    total: int
    page: int
    limit: int
