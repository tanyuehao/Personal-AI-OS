"""
Personal AI OS - Knowledge Graph API
知识图谱接口
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.document import Document
from app.models.knowledge import KnowledgeChunk
from app.models.memory import Memory
from app.models.belief import Belief
from app.models.decision import Decision

router = APIRouter(prefix="/graph", tags=["知识图谱"])


@router.get("")
async def get_graph_data(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取知识图谱数据（节点 + 关系）"""
    nodes = []
    edges = []
    node_map = {}

    # 1. 文档节点
    result = await db.execute(
        select(Document).where(Document.user_id == current_user_id).limit(50)
    )
    documents = result.scalars().all()
    for doc in documents:
        node_id = f"doc_{doc.document_id}"
        node_map[str(doc.document_id)] = node_id
        nodes.append({
            "id": node_id,
            "label": doc.file_name or "未命名文档",
            "type": "document",
            "group": 1,
            "data": {
                "file_type": doc.file_type,
                "status": doc.status,
                "summary": (doc.summary or "")[:100]
            }
        })

    # 2. 记忆节点
    result = await db.execute(
        select(Memory).where(Memory.user_id == current_user_id).limit(50)
    )
    memories = result.scalars().all()
    memory_type_map = {}
    for mem in memories:
        node_id = f"mem_{mem.memory_id}"
        node_map[str(mem.memory_id)] = node_id
        mem_type = mem.memory_type
        if mem_type not in memory_type_map:
            memory_type_map[mem_type] = []
        memory_type_map[mem_type].append(node_id)
        nodes.append({
            "id": node_id,
            "label": mem.content[:30] + ("..." if len(mem.content) > 30 else ""),
            "type": "memory",
            "group": 2,
            "data": {
                "memory_type": mem_type,
                "importance": mem.importance,
                "content": mem.content[:100]
            }
        })

    # 3. 观点节点
    result = await db.execute(
        select(Belief).where(Belief.user_id == current_user_id).limit(30)
    )
    beliefs = result.scalars().all()
    for belief in beliefs:
        node_id = f"belief_{belief.belief_id}"
        node_map[str(belief.belief_id)] = node_id
        nodes.append({
            "id": node_id,
            "label": belief.topic or "未命名观点",
            "type": "belief",
            "group": 3,
            "data": {
                "content": (belief.content or "")[:100],
                "confidence": belief.confidence
            }
        })

    # 4. 决策节点
    result = await db.execute(
        select(Decision).where(Decision.user_id == current_user_id).limit(30)
    )
    decisions = result.scalars().all()
    for dec in decisions:
        node_id = f"dec_{dec.decision_id}"
        node_map[str(dec.decision_id)] = node_id
        nodes.append({
            "id": node_id,
            "label": (dec.problem or "未命名决策")[:30],
            "type": "decision",
            "group": 4,
            "data": {
                "choice": dec.choice,
                "reasoning": (dec.reasoning or "")[:100]
            }
        })

    # ========== 构建关系 ==========

    # 关系1: 同类型记忆之间（基于关键词匹配）
    for mem_type, node_ids in memory_type_map.items():
        for i in range(len(node_ids)):
            for j in range(i + 1, min(i + 3, len(node_ids))):
                edges.append({
                    "source": node_ids[i],
                    "target": node_ids[j],
                    "label": "同类记忆",
                    "type": "memory_same_type"
                })

    # 关系2: 记忆 → 文档（基于关键词匹配）
    for mem in memories:
        mem_node = f"mem_{mem.memory_id}"
        for doc in documents:
            doc_node = f"doc_{doc.document_id}"
            # 检查记忆内容是否包含文档名关键词
            if doc.file_name and any(
                word in mem.content.lower()
                for word in doc.file_name.lower().split()
                if len(word) > 2
            ):
                edges.append({
                    "source": mem_node,
                    "target": doc_node,
                    "label": "来源",
                    "type": "memory_from_doc"
                })

    # 关系3: 观点 → 记忆（基于主题匹配）
    for belief in beliefs:
        belief_node = f"belief_{belief.belief_id}"
        if belief.topic:
            topic_words = belief.topic.lower().split()
            for mem in memories:
                mem_node = f"mem_{mem.memory_id}"
                if any(word in mem.content.lower() for word in topic_words if len(word) > 1):
                    edges.append({
                        "source": belief_node,
                        "target": mem_node,
                        "label": "相关",
                        "type": "belief_related_memory"
                    })

    # 关系4: 决策 → 观点
    for dec in decisions:
        dec_node = f"dec_{dec.decision_id}"
        for belief in beliefs:
            belief_node = f"belief_{belief.belief_id}"
            if belief.topic and dec.problem and any(
                word in dec.problem.lower()
                for word in belief.topic.lower().split()
                if len(word) > 1
            ):
                edges.append({
                    "source": dec_node,
                    "target": belief_node,
                    "label": "基于",
                    "type": "decision_based_on_belief"
                })

    # 关系5: 文档 → 知识切片
    result = await db.execute(
        select(KnowledgeChunk.document_id).distinct().limit(30)
    )
    doc_ids_with_chunks = [row[0] for row in result.all()]
    for doc_id in doc_ids_with_chunks:
        doc_node = node_map.get(str(doc_id))
        if doc_node:
            # 获取该文档的切片数量
            chunk_result = await db.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id).limit(5)
            )
            chunks = chunk_result.scalars().all()
            for chunk in chunks:
                chunk_node = f"chunk_{chunk.chunk_id}"
                nodes.append({
                    "id": chunk_node,
                    "label": chunk.content[:20] + "...",
                    "type": "chunk",
                    "group": 5,
                    "data": {"content": chunk.content[:100]}
                })
                edges.append({
                    "source": doc_node,
                    "target": chunk_node,
                    "label": "包含",
                    "type": "doc_contains_chunk"
                })

    # 去重边
    unique_edges = []
    seen_edges = set()
    for edge in edges:
        key = (edge["source"], edge["target"], edge["label"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(edge)

    return {
        "nodes": nodes,
        "edges": unique_edges,
        "stats": {
            "documents": len(documents),
            "memories": len(memories),
            "beliefs": len(beliefs),
            "decisions": len(decisions),
            "total_nodes": len(nodes),
            "total_edges": len(unique_edges)
        }
    }
