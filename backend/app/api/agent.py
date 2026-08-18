"""
Personal AI OS - Agent API
Agent 接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.agent import AgentTask
from app.schemas.agent import (
    AgentRunRequest,
    AgentTaskResponse,
    AgentTaskListResponse,
    AgentListResponse
)

router = APIRouter(prefix="/agent", tags=["Agent"])


# Agent 类型定义
AGENT_TYPES = {
    "business": {
        "name": "商业分析",
        "description": "分析商业数据、市场趋势、竞争格局",
        "icon": "💼",
        "system_prompt": """你是一个专业的商业分析助手。你的职责是：
1. 分析商业数据和市场趋势
2. 评估竞争格局和市场机会
3. 提供商业建议和决策支持
4. 生成商业报告和分析文档

请用中文回答，提供专业、客观、有见地的分析。"""
    },
    "investment": {
        "name": "投资分析",
        "description": "分析投资机会、风险评估、投资策略",
        "icon": "📈",
        "system_prompt": """你是一个专业的投资分析助手。你的职责是：
1. 分析投资机会和市场趋势
2. 评估投资风险和收益
3. 提供投资建议和策略
4. 生成投资报告和分析文档

请用中文回答，提供专业、客观、有风险意识的投资分析。"""
    },
    "writing": {
        "name": "写作助手",
        "description": "帮助撰写文章、报告、邮件等各类文档",
        "icon": "✍️",
        "system_prompt": """你是一个专业的写作助手。你的职责是：
1. 帮助用户撰写各类文档
2. 优化文章结构和表达
3. 提供写作建议和改进意见
4. 润色和校对文本内容

请用中文回答，提供专业、清晰、有条理的写作支持。"""
    },
    "review": {
        "name": "复盘助手",
        "description": "帮助复盘项目、总结经验、分析问题",
        "icon": "🔄",
        "system_prompt": """你是一个专业的复盘助手。你的职责是：
1. 帮助用户复盘项目和决策
2. 总结成功经验和失败教训
3. 分析问题根本原因
4. 提供改进建议和行动计划

请用中文回答，提供客观、深入、有建设性的复盘分析。"""
    }
}


@router.get("/list", response_model=AgentListResponse)
async def list_agents():
    """获取可用的 Agent 列表"""
    agents = []
    for agent_type, info in AGENT_TYPES.items():
        agents.append({
            "type": agent_type,
            "name": info["name"],
            "description": info["description"],
            "icon": info["icon"]
        })
    return AgentListResponse(agents=agents)


@router.post("/run", response_model=AgentTaskResponse)
async def run_agent(
    request: AgentRunRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """执行 Agent 任务"""
    # 验证 Agent 类型
    if request.agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")
    
    agent_info = AGENT_TYPES[request.agent_type]
    
    # 创建任务记录
    task = AgentTask(
        user_id=current_user_id,
        agent_type=request.agent_type,
        title=request.title,
        input_text=request.input,
        context=request.context,
        status="running"
    )
    db.add(task)
    await db.flush()
    
    try:
        # 调用 AI 服务
        from app.services.ai_service import create_ai_service

        service = create_ai_service()
        
        messages = [
            {"role": "system", "content": agent_info["system_prompt"]},
            {"role": "user", "content": request.input}
        ]
        
        response = await service.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        # 更新任务状态
        task.status = "completed"
        task.result = response.content
        task.steps = [
            {"step": "接收任务", "status": "done"},
            {"step": "分析输入", "status": "done"},
            {"step": "生成回答", "status": "done"}
        ]
        task.completed_at = datetime.now(timezone.utc)
        
    except Exception as e:
        task.status = "failed"
        task.result = f"执行失败: {str(e)}"
    
    await db.flush()
    await db.refresh(task)
    
    return AgentTaskResponse.model_validate(task)


@router.get("/tasks", response_model=AgentTaskListResponse)
async def list_tasks(
    page: int = 1,
    limit: int = 20,
    agent_type: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取 Agent 任务列表"""
    query = select(AgentTask).where(AgentTask.user_id == current_user_id)
    
    if agent_type:
        query = query.where(AgentTask.agent_type == agent_type)
    
    # 获取总数
    count_query = select(func.count()).select_from(AgentTask).where(AgentTask.user_id == current_user_id)
    if agent_type:
        count_query = count_query.where(AgentTask.agent_type == agent_type)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(AgentTask.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return AgentTaskListResponse(
        items=[AgentTaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/tasks/{task_id}", response_model=AgentTaskResponse)
async def get_task(
    task_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取 Agent 任务详情"""
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.task_id == task_id,
            AgentTask.user_id == current_user_id
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return AgentTaskResponse.model_validate(task)
