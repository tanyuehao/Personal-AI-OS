"""
Personal AI OS - Document Processing Service
文档处理服务
"""
import os
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document, DocumentStatus
from app.models.knowledge import KnowledgeChunk
from app.services.document_parser import parse_document
from app.services.text_chunker import create_chunker
from app.services.embedding import create_embedding


class DocumentProcessor:
    """文档处理器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunker = create_chunker(
            chunk_size=500,
            chunk_overlap=50,
            min_chunk_size=100
        )
        self.embedding_service = None

    async def _get_embedding_service(self):
        """获取 Embedding 服务"""
        if self.embedding_service is None:
            self.embedding_service = create_embedding(provider=settings.EMBEDDING_PROVIDER)
        return self.embedding_service

    async def process_document(self, document_id: str) -> bool:
        """
        处理文档：解析 → 切片 → 生成向量 → 存储
        """
        result = await self.db.execute(
            select(Document).where(Document.document_id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise Exception(f"文档不存在: {document_id}")

        try:
            # 更新状态为处理中
            document.status = DocumentStatus.PROCESSING.value
            document.status_message = "正在解析文档..."
            await self.db.flush()

            # 1. 解析文档
            text_content = await parse_document(
                document.file_path,
                document.file_type
            )

            if not text_content:
                raise Exception("文档内容为空")

            document.content = text_content
            await self.db.flush()

            # 2. 文本切片
            document.status_message = "正在切分文本..."
            await self.db.flush()

            chunks = self.chunker.chunk_text(text_content)

            if not chunks:
                raise Exception("文本切片失败")

            # 3. 生成 Embedding 并存储
            document.status_message = f"正在生成向量 ({len(chunks)} 个切片)..."
            await self.db.flush()

            embedding_service = await self._get_embedding_service()

            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await embedding_service.embed(chunk_texts)

            # 4. 存储知识切片和向量
            document.status_message = "正在保存知识库..."
            await self.db.flush()

            from app.services.vector_store import VectorStore
            vector_store = VectorStore(self.db)

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                knowledge_chunk = KnowledgeChunk(
                    document_id=document.document_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    topic=None,
                    tags=None,
                    metadata_=chunk.metadata
                )
                self.db.add(knowledge_chunk)
                await self.db.flush()

                # 存储向量到 pgvector
                await vector_store.add_embedding(
                    chunk_id=str(knowledge_chunk.chunk_id),
                    embedding=embedding,
                    content=chunk.content,
                    metadata=chunk.metadata
                )

            # 5. 生成 AI 摘要
            document.status_message = "正在生成 AI 摘要..."
            await self.db.flush()

            try:
                from app.services.ai_service import create_ai_service
                ai_service = create_ai_service()

                # 截取前 2000 字符用于摘要
                summary_input = text_content[:2000] if len(text_content) > 2000 else text_content
                summary_prompt = f"""请为以下文档生成一个简洁的摘要（100-200字），提取核心观点和关键信息：

{summary_input}"""

                response = await ai_service.chat(
                    messages=[{"role": "user", "content": summary_prompt}],
                    system_prompt="你是一个专业的文档摘要助手。请简洁地总结文档的核心内容。",
                    temperature=0.3,
                    max_tokens=300
                )
                document.summary = response.content
            except Exception:
                # AI 摘要失败时，使用截断方式作为备用
                document.summary = text_content[:500] + "..." if len(text_content) > 500 else text_content

            # 更新文档状态
            document.status = DocumentStatus.COMPLETED.value
            document.status_message = f"处理完成，共 {len(chunks)} 个知识切片"
            document.processed_at = datetime.now(timezone.utc)

            await self.db.flush()

            return True

        except Exception as e:
            document.status = DocumentStatus.FAILED.value
            document.status_message = f"处理失败: {str(e)}"
            await self.db.flush()
            raise Exception(f"文档处理失败: {str(e)}")

    async def reprocess_document(self, document_id: str) -> bool:
        """重新处理文档"""
        await self.db.execute(
            delete(KnowledgeChunk).where(
                KnowledgeChunk.document_id == document_id
            )
        )
        return await self.process_document(document_id)


async def process_document_task(document_id: str, db_url: str):
    """异步处理文档的任务"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as db:
        try:
            processor = DocumentProcessor(db)
            await processor.process_document(document_id)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e
        finally:
            await engine.dispose()
