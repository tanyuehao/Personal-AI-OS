"""
Personal AI OS - User Schemas
用户请求/响应模型
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID


# ========== 请求模型 ==========

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    name: Optional[str] = Field(None, max_length=100, description="显示名称")


class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """用户更新请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    avatar: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=1000)


class PasswordChange(BaseModel):
    """密码修改请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


# ========== 响应模型 ==========

class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """用户信息响应"""
    user_id: UUID
    username: str
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """用户详细信息响应"""
    user_id: UUID
    username: str
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """消息响应"""
    message: str
    success: bool = True
