"""
Personal AI OS - Document API
文档管理接口
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse
)

router = APIRouter(prefix="/documents", tags=["文档管理"])


async def save_upload_file(file: UploadFile, user_id: str, content: bytes = None) -> tuple[str, str]:
    """
    保存上传的文件

    Returns:
        tuple: (file_path, file_name)
    """
    # 创建用户上传目录
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(user_dir, file_name)

    # 保存文件
    if content is None:
        content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, file.filename or file_name


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="上传的文件"),
    category: Optional[str] = Form(None, description="文件分类"),
    source: Optional[str] = Form(None, description="数据来源"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    上传文档

    支持格式：PDF, Word, Markdown, TXT, Excel
    """
    import traceback
    try:
        return await _do_upload(file, category, source, current_user_id, db)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="文档上传失败")


async def _do_upload(file, category, source, current_user_id, db):
    # 检查文件类型
    allowed_types = {
        '.pdf', '.doc', '.docx', '.md', '.markdown',
        '.txt', '.text', '.csv', '.xlsx', '.xls'
    }

    # 清洗文件名，防止路径遍历
    import re
    safe_name = re.sub(r'[^\w\-_\. ]', '_', file.filename or "unknown")
    file_ext = os.path.splitext(safe_name)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_ext}"
        )

    # 流式检查文件大小（避免 OOM）
    file_size = 0
    chunks = []
    while True:
        chunk = await file.read(8192)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超过限制: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        chunks.append(chunk)

    content = b"".join(chunks)

    # 保存文件
    file_path, original_name = await save_upload_file(file, current_user_id, content=content)
    
    # 创建文档记录
    document = Document(
        user_id=current_user_id,
        file_name=original_name,
        file_type=file_ext,
        file_path=file_path,
        file_size=len(content),
        source=source,
        category=category,
        status=DocumentStatus.UPLOADING.value
    )
    
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # 同步处理文档（确保处理完成）
    try:
        from app.services.document_processor import DocumentProcessor
        processor = DocumentProcessor(db)
        await processor.process_document(str(document.document_id))
    except Exception as e:
        # 处理失败，更新状态
        document.status = DocumentStatus.FAILED.value
        document.status_message = f"处理失败: {str(e)}"
        await db.flush()

    return {
        "document_id": str(document.document_id),
        "file_name": original_name or "unknown",
        "status": document.status,
        "message": document.status_message or "处理完成"
    }


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文档列表
    """
    # 构建查询
    query = select(Document).where(Document.user_id == current_user_id)
    
    if category:
        query = query.where(Document.category == category)
    
    # 获取总数
    count_query = select(func.count()).select_from(Document).where(Document.user_id == current_user_id)
    if category:
        count_query = count_query.where(Document.category == category)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文档详情
    """
    result = await db.execute(
        select(Document).where(
            Document.document_id == document_id,
            Document.user_id == current_user_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    删除文档
    """
    result = await db.execute(
        select(Document).where(
            Document.document_id == document_id,
            Document.user_id == current_user_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 删除文件
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # 先删除关联的知识切片
    from app.models.knowledge import KnowledgeChunk
    from sqlalchemy import delete as sql_delete
    await db.execute(
        sql_delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
    )

    # 删除数据库记录
    await db.delete(document)
    
    return None


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    下载文档
    """
    result = await db.execute(
        select(Document).where(
            Document.document_id == document_id,
            Document.user_id == current_user_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
        media_type="application/octet-stream"
    )
