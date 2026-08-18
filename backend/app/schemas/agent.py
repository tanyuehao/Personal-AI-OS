"""
Personal AI OS - Agent Schemas
Agent 请求/响应模型
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 请求模型 ==========

class AgentRunRequest(BaseModel):
    """执行 Agent 任务请求"""
    agent_type: str = Field(..., description="Agent 类型: business, investment, writing, review")
    input: str = Field(..., min_length=1, description="输入内容")
    title: Optional[str] = Field(None, description="任务标题")
    context: Optional[dict] = Field(None, description="上下文信息")


# ========== 响应模型 ==========

class AgentInfo(BaseModel):
    """Agent 信息"""
    type: str
    name: str
    description: str
    icon: str


class AgentListResponse(BaseModel):
    """Agent 列表响应"""
    agents: List[AgentInfo]


class AgentTaskResponse(BaseModel):
    """Agent 任务响应"""
    task_id: str
    user_id: str
    agent_type: str
    title: Optional[str] = None
    input_text: str
    context: Optional[dict] = None
    status: str
    result: Optional[str] = None
    steps: Optional[List[dict]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AgentTaskListResponse(BaseModel):
    """Agent 任务列表响应"""
    items: List[AgentTaskResponse]
    total: int
    page: int
    limit: int
