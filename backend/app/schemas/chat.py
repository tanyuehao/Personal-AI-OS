"""
Personal AI OS - Chat Schemas
聊天请求/响应模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 请求模型 ==========

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话 ID（可选，不传则创建新对话）")
    memory_enabled: bool = Field(True, description="是否启用记忆")


# ========== 响应模型 ==========

class SourceResponse(BaseModel):
    """引用来源"""
    chunk_id: str
    content: str
    document_id: str
    document_name: str
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    sources: List[SourceResponse]
    conversation_id: str
    memory_used: Optional[List[Dict[str, Any]]] = None


class ConversationResponse(BaseModel):
    """对话列表响应"""
    conversation_id: str
    title: Optional[str] = None
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    role: str
    content: str
    sources: Optional[List[SourceResponse]] = None
    created_at: str
