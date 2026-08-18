"""
Personal AI OS - AI Chat API
AI 聊天接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.rag_service import RAGService, create_rag_service
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse
)
from app.services.ai_service import create_ai_service
from app.models.conversation import Conversation, ConversationMessage

router = APIRouter(prefix="/ai", tags=["AI 聊天"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    AI 聊天接口
    
    基于用户的知识库进行 RAG 问答
    """
    try:
        rag_service = await create_rag_service(db)
        
        response = await rag_service.chat(
            user_id=current_user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            memory_enabled=request.memory_enabled
        )
        
        return ChatResponse(
            answer=response.answer,
            sources=response.sources,
            conversation_id=response.conversation_id,
            memory_used=response.memory_used
        )
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 聊天服务暂时不可用"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话列表
    """
    rag_service = await create_rag_service(db)
    conversations = await rag_service.list_conversations(
        user_id=current_user_id,
        limit=limit
    )
    
    return [ConversationResponse(**conv) for conv in conversations]


@router.get("/conversations/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话消息列表
    """
    rag_service = await create_rag_service(db)
    messages = await rag_service.get_conversation_history(
        conversation_id=conversation_id,
        user_id=current_user_id
    )
    
    return [MessageResponse(**msg) for msg in messages]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除对话及其所有消息"""
    print(f"[DELETE] conversation_id={conversation_id}, user_id={current_user_id}")

    # 验证对话属于当前用户
    result = await db.execute(
        select(Conversation).where(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == current_user_id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        print(f"[DELETE] Conversation not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    print(f"[DELETE] Found conversation, deleting...")

    # 使用同步 SQLite 删除
    import sqlite3
    from app.core.config import settings

    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    print(f"[DELETE] DB path: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversation_messages WHERE conversation_id = ?", (conversation_id,))
    msgs_deleted = cursor.rowcount
    cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
    conv_deleted = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"[DELETE] Deleted {msgs_deleted} messages, {conv_deleted} conversations")


@router.post("/summary")
async def summarize(
    content: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    文档总结接口
    """
    try:
        ai_service = create_ai_service()
        
        system_prompt = """你是一个专业的文档总结助手。
请对用户提供的内容进行总结，提取关键信息。
总结应该：
- 简洁明了
- 包含主要观点
- 保留重要细节
- 使用结构化格式"""
        
        response = await ai_service.chat(
            messages=[{"role": "user", "content": f"请总结以下内容：\n\n{content}"}],
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=1000
        )
        
        return {"summary": response.content}
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文档总结失败"
        )
