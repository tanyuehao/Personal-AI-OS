"""
Personal AI OS - Knowledge API
知识库接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.knowledge import KnowledgeChunk
from app.models.document import Document
from app.schemas.knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeChunkResponse
)

router = APIRouter(prefix="/knowledge", tags=["知识库"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    语义搜索知识库

    基于用户的问题，从知识库中检索相关内容
    """
    try:
        # 获取 Embedding 服务
        from app.services.embedding import create_embedding
        from app.core.config import settings
        embedding_service = create_embedding(provider=settings.EMBEDDING_PROVIDER)

        # 生成查询向量
        query_embedding = await embedding_service.embed_query(request.query)

        # 向量语义搜索
        from app.services.vector_store import VectorStore
        vector_store = VectorStore(db)

        results = await vector_store.search_similar(
            query_embedding=query_embedding,
            user_id=current_user_id,
            limit=request.limit or 10,
            threshold=0.3
        )

        # 如果向量搜索有结果，返回
        if results:
            items = []
            for chunk, score in results:
                items.append(KnowledgeChunkResponse(
                    chunk_id=str(chunk.chunk_id),
                    content=chunk.content,
                    document_id=str(chunk.document_id),
                    chunk_index=chunk.chunk_index,
                    relevance_score=round(score, 4)
                ))
            return KnowledgeSearchResponse(
                items=items,
                total=len(items),
                query=request.query
            )

        # 降级为文本搜索（转义 ILIKE 通配符）
        safe_query = request.query.replace("%", "\\%").replace("_", "\\_")
        query = select(KnowledgeChunk).join(Document).where(
            Document.user_id == current_user_id,
            KnowledgeChunk.content.ilike(f"%{safe_query}%", escape="\\")
        )

        if request.limit:
            query = query.limit(request.limit)

        result = await db.execute(query)
        chunks = result.scalars().all()

        items = []
        for chunk in chunks:
            items.append(KnowledgeChunkResponse(
                chunk_id=str(chunk.chunk_id),
                content=chunk.content,
                document_id=str(chunk.document_id),
                chunk_index=chunk.chunk_index,
                relevance_score=0.5
            ))

        return KnowledgeSearchResponse(
            items=items,
            total=len(items),
            query=request.query
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="知识库搜索失败"
        )


@router.get("/chunks/{document_id}")
async def get_document_chunks(
    document_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文档的所有知识切片
    """
    # 验证文档属于当前用户
    doc_result = await db.execute(
        select(Document).where(
            Document.document_id == document_id,
            Document.user_id == current_user_id
        )
    )
    document = doc_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 获取切片
    result = await db.execute(
        select(KnowledgeChunk).where(
            KnowledgeChunk.document_id == document_id
        ).order_by(KnowledgeChunk.chunk_index)
    )
    chunks = result.scalars().all()
    
    return [
        KnowledgeChunkResponse(
            chunk_id=str(chunk.chunk_id),
            content=chunk.content,
            document_id=str(chunk.document_id),
            chunk_index=chunk.chunk_index
        )
        for chunk in chunks
    ]
