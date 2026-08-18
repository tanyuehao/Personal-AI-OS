"""
Personal AI OS - Settings Schemas
设置请求/响应模型
"""
from typing import Optional
from pydantic import BaseModel, Field


def mask_api_key(key: str) -> str:
    """掩码 API Key，只显示前4位和后4位"""
    if not key or len(key) <= 8:
        return "****" if key else ""
    return f"{key[:4]}****{key[-4:]}"


# ========== 请求模型 ==========

class UserSettingsUpdateRequest(BaseModel):
    """更新用户设置请求"""
    ai_provider: Optional[str] = Field(None, description="AI 提供商: siliconflow, deepseek")
    siliconflow_api_key: Optional[str] = Field(None, description="硅基流动 API Key")
    siliconflow_api_base: Optional[str] = Field(None, description="硅基流动 API 地址")
    deepseek_api_key: Optional[str] = Field(None, description="DeepSeek API Key")
    deepseek_api_base: Optional[str] = Field(None, description="DeepSeek API 地址")
    llm_model: Optional[str] = Field(None, description="语言模型")
    embedding_model: Optional[str] = Field(None, description="Embedding 模型")
    reranker_enabled: Optional[bool] = Field(None, description="是否启用 Reranker")
    reranker_model: Optional[str] = Field(None, description="Reranker 模型")
    image_model_enabled: Optional[bool] = Field(None, description="是否启用图片生成")
    image_model: Optional[str] = Field(None, description="图片模型")
    temperature: Optional[str] = Field(None, description="温度参数")
    max_tokens: Optional[str] = Field(None, description="最大 Token 数")


# ========== 响应模型 ==========

class UserSettingsResponse(BaseModel):
    """用户设置响应（API Key 掩码显示）"""
    settings_id: str
    user_id: str
    ai_provider: str
    siliconflow_api_key: str  # 掩码显示
    siliconflow_api_base: str
    deepseek_api_key: str  # 掩码显示
    deepseek_api_base: str
    llm_model: str
    embedding_model: str
    reranker_enabled: bool
    reranker_model: str
    image_model_enabled: bool
    image_model: str
    temperature: str
    max_tokens: str

    class Config:
        from_attributes = True
