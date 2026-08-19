"""
Personal AI OS - Knowledge Graph API
知识图谱建模接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.knowledge_graph_builder import get_knowledge_graph_builder

router = APIRouter(prefix="/knowledge-graph", tags=["知识图谱建模"])


class EntityResponse(BaseModel):
    """实体响应"""
    id: str
    label: str
    type: str
    description: Optional[str] = None
    importance: float
    mention_count: int


class RelationResponse(BaseModel):
    """关系响应"""
    source: str
    target: str
    label: str
    weight: float
    description: Optional[str] = None


class GraphResponse(BaseModel):
    """图谱响应"""
    nodes: List[dict]
    edges: List[dict]
    stats: dict


class BuildRequest(BaseModel):
    """构建请求"""
    limit: int = 50


@router.get("", response_model=GraphResponse)
async def get_knowledge_graph(
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    limit: int = Query(100, ge=1, le=500),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取知识图谱数据

    返回实体和关系，支持按实体类型过滤。
    """
    builder = get_knowledge_graph_builder(db)
    return await builder.get_graph_data(current_user_id, entity_type, limit)


@router.post("/build")
async def build_knowledge_graph(
    request: BuildRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    从文档构建知识图谱

    分析文档内容，提取实体和关系，构建知识图谱。
    """
    builder = get_knowledge_graph_builder(db)
    result = await builder.build_graph_from_documents(current_user_id, request.limit)

    return {
        "message": "知识图谱构建完成",
        "entities_created": result["entities_created"],
        "relations_created": result["relations_created"]
    }


@router.get("/entity/{entity_name}")
async def get_entity_connections(
    entity_name: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    查找实体的所有连接

    返回指定实体的入边和出边关系。
    """
    builder = get_knowledge_graph_builder(db)
    result = await builder.find_entity_connections(current_user_id, entity_name)

    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/types")
async def get_entity_types():
    """获取实体类型定义"""
    from app.services.knowledge_graph_builder import ENTITY_TYPES, RELATION_TYPES
    return {
        "entity_types": ENTITY_TYPES,
        "relation_types": RELATION_TYPES
    }
