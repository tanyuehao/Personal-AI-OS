"""
Personal AI OS - Data Export API
数据导出接口
"""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.document import Document
from app.models.knowledge import KnowledgeChunk
from app.models.memory import Memory
from app.models.belief import Belief, BeliefHistory
from app.models.decision import Decision
from app.models.conversation import Conversation, ConversationMessage

router = APIRouter(prefix="/export", tags=["数据导出"])


@router.get("/all")
async def export_all_data(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    导出所有用户数据为 JSON 文件
    """
    # 获取用户信息
    user_result = await db.execute(select(User).where(User.user_id == current_user_id))
    user = user_result.scalar_one_or_none()

    # 获取文档
    docs_result = await db.execute(
        select(Document).where(Document.user_id == current_user_id)
    )
    documents = docs_result.scalars().all()

    # 获取知识切片
    chunks = []
    for doc in documents:
        chunks_result = await db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.document_id)
        )
        for chunk in chunks_result.scalars().all():
            chunks.append({
                "chunk_id": str(chunk.chunk_id),
                "document_id": str(chunk.document_id),
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "created_at": chunk.created_at.isoformat()
            })

    # 获取记忆
    memories_result = await db.execute(
        select(Memory).where(Memory.user_id == current_user_id)
    )
    memories = memories_result.scalars().all()

    # 获取观点
    beliefs_result = await db.execute(
        select(Belief).where(Belief.user_id == current_user_id)
    )
    beliefs = beliefs_result.scalars().all()

    # 获取观点历史
    belief_histories = []
    for belief in beliefs:
        history_result = await db.execute(
            select(BeliefHistory).where(BeliefHistory.belief_id == belief.belief_id)
        )
        for h in history_result.scalars().all():
            belief_histories.append({
                "belief_id": str(h.belief_id),
                "old_content": h.old_content,
                "new_content": h.new_content,
                "change_reason": h.change_reason,
                "created_at": h.created_at.isoformat()
            })

    # 获取决策
    decisions_result = await db.execute(
        select(Decision).where(Decision.user_id == current_user_id)
    )
    decisions = decisions_result.scalars().all()

    # 获取对话
    convs_result = await db.execute(
        select(Conversation).where(Conversation.user_id == current_user_id)
    )
    conversations = convs_result.scalars().all()

    messages = []
    for conv in conversations:
        msgs_result = await db.execute(
            select(ConversationMessage).where(ConversationMessage.conversation_id == conv.conversation_id)
        )
        for msg in msgs_result.scalars().all():
            messages.append({
                "message_id": str(msg.message_id),
                "conversation_id": str(msg.conversation_id),
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            })

    # 构建导出数据
    export_data = {
        "export_info": {
            "project": "Personal AI OS",
            "version": "0.5.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": str(current_user_id)
        },
        "user": {
            "username": user.username if user else "",
            "email": user.email if user else ""
        },
        "documents": [
            {
                "document_id": str(doc.document_id),
                "file_name": doc.file_name,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "summary": doc.summary,
                "created_at": doc.created_at.isoformat()
            }
            for doc in documents
        ],
        "knowledge_chunks": chunks,
        "memories": [
            {
                "memory_id": str(mem.memory_id),
                "memory_type": mem.memory_type,
                "content": mem.content,
                "source": mem.source,
                "importance": mem.importance,
                "confidence": mem.confidence,
                "is_confirmed": mem.is_confirmed,
                "created_at": mem.created_at.isoformat()
            }
            for mem in memories
        ],
        "beliefs": [
            {
                "belief_id": str(b.belief_id),
                "topic": b.topic,
                "content": b.content,
                "confidence": b.confidence,
                "status": b.status,
                "created_at": b.created_at.isoformat()
            }
            for b in beliefs
        ],
        "belief_histories": belief_histories,
        "decisions": [
            {
                "decision_id": str(d.decision_id),
                "problem": d.problem,
                "background": d.background,
                "options": d.options,
                "choice": d.choice,
                "reasoning": d.reasoning,
                "risk": d.risk,
                "expected_result": d.expected_result,
                "actual_result": d.actual_result,
                "lesson": d.lesson,
                "category": d.category,
                "created_at": d.created_at.isoformat()
            }
            for d in decisions
        ],
        "conversations": [
            {
                "conversation_id": str(conv.conversation_id),
                "title": conv.title,
                "created_at": conv.created_at.isoformat()
            }
            for conv in conversations
        ],
        "messages": messages,
        "stats": {
            "documents": len(documents),
            "knowledge_chunks": len(chunks),
            "memories": len(memories),
            "beliefs": len(beliefs),
            "belief_histories": len(belief_histories),
            "decisions": len(decisions),
            "conversations": len(conversations),
            "messages": len(messages)
        }
    }

    # 返回 JSON 文件
    json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"personal_ai_os_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    return StreamingResponse(
        iter([json_content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/stats")
async def get_export_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取导出统计信息（不导出数据，只返回数量）
    """
    # 文档数
    docs_result = await db.execute(
        select(Document).where(Document.user_id == current_user_id)
    )
    doc_count = len(docs_result.scalars().all())

    # 知识切片数
    chunks_count = 0
    for doc in (await db.execute(
        select(Document).where(Document.user_id == current_user_id)
    )).scalars().all():
        chunks_result = await db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.document_id)
        )
        chunks_count += len(chunks_result.scalars().all())

    # 记忆数
    mem_result = await db.execute(
        select(Memory).where(Memory.user_id == current_user_id)
    )
    mem_count = len(mem_result.scalars().all())

    # 观点数
    belief_result = await db.execute(
        select(Belief).where(Belief.user_id == current_user_id)
    )
    belief_count = len(belief_result.scalars().all())

    # 决策数
    dec_result = await db.execute(
        select(Decision).where(Decision.user_id == current_user_id)
    )
    dec_count = len(dec_result.scalars().all())

    # 对话数
    conv_result = await db.execute(
        select(Conversation).where(Conversation.user_id == current_user_id)
    )
    conv_count = len(conv_result.scalars().all())

    return {
        "documents": doc_count,
        "knowledge_chunks": chunks_count,
        "memories": mem_count,
        "beliefs": belief_count,
        "decisions": dec_count,
        "conversations": conv_count
    }
