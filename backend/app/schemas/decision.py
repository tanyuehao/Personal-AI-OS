"""
Personal AI OS - Decision Schemas
决策请求/响应模型
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 请求模型 ==========

class DecisionCreateRequest(BaseModel):
    """创建决策请求"""
    problem: str = Field(..., min_length=1, max_length=5000, description="问题/背景")
    background: Optional[str] = Field(None, description="背景信息")
    options: Optional[List[str]] = Field(None, description="备选方案列表")
    choice: Optional[str] = Field(None, description="选择的方案")
    reasoning: Optional[str] = Field(None, description="判断依据")
    risk: Optional[str] = Field(None, description="风险因素")
    expected_result: Optional[str] = Field(None, description="预期结果")
    actual_result: Optional[str] = Field(None, description="实际结果")
    lesson: Optional[str] = Field(None, description="经验教训")
    category: Optional[str] = Field(None, description="决策类别")
    tags: Optional[List[str]] = Field(None, description="标签")
    decision_date: Optional[datetime] = Field(None, description="决策日期")


class DecisionUpdateRequest(BaseModel):
    """更新决策请求"""
    problem: Optional[str] = None
    background: Optional[str] = None
    options: Optional[List[str]] = None
    choice: Optional[str] = None
    reasoning: Optional[str] = None
    risk: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    lesson: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


# ========== 响应模型 ==========

class DecisionResponse(BaseModel):
    """决策响应"""
    decision_id: str
    problem: str
    background: Optional[str] = None
    options: Optional[List[str]] = None
    choice: Optional[str] = None
    reasoning: Optional[str] = None
    risk: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    lesson: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    decision_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DecisionListResponse(BaseModel):
    """决策列表响应"""
    items: List[DecisionResponse]
    total: int
    page: int
    limit: int
