"""
Personal AI OS - Authentication API
用户认证接口 - 带 refresh token rotation
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user_id
)
from app.core.database import get_db
from app.models.user import User, RefreshToken
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse,
    TokenResponse, MessageResponse
)

router = APIRouter(prefix="/auth", tags=["认证"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


async def _create_refresh_token_record(db: AsyncSession, user_id: str, jti: str, token_family: str):
    """创建 refresh token 记录"""
    # 确保 jti 唯一
    if not jti:
        jti = str(uuid.uuid4())

    token_record = RefreshToken(
        user_id=user_id,
        jti=jti,
        token_family=token_family,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(token_record)
    await db.flush()
    return token_record


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 检查用户名
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    # 检查邮箱
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    # 生成 access token
    access_token = create_access_token(data={"sub": str(user.user_id)})

    # 生成 refresh token 并记录到数据库
    refresh_token = create_refresh_token(data={"sub": str(user.user_id)})
    token_payload = decode_token(refresh_token)

    # 使用 JWT 中的 jti 作为 RefreshToken 的 jti（确保一致）
    jti = token_payload.get("jti", "")
    token_family = str(uuid.uuid4())
    await _create_refresh_token_record(
        db, str(user.user_id), jti, token_family
    )

    # 显式提交确保 token 在后续请求中可见
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    刷新访问令牌（带 rotation）
    """
    refresh_token = request.refresh_token

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 refresh_token")

    try:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌类型")

        user_id = payload.get("sub")
        jti = payload.get("jti", "")

        # 查询 refresh token 记录（使用 db session）
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.jti == jti
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌")

        # 检查是否已被撤销
        if token_record.is_revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌已被撤销")

        # 检查是否已被使用（重放攻击）- revoke 整个 token family
        if token_record.is_used:
            family_result = await db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.token_family == token_record.token_family,
                    RefreshToken.is_used == False,
                    RefreshToken.is_revoked == False
                )
            )
            family_tokens = family_result.scalars().all()
            for t in family_tokens:
                t.is_revoked = True
                t.revoked_at = datetime.now(timezone.utc)
            await db.flush()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌已被使用，所有会话已失效")

        # 检查是否已过期
        if token_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌已过期")

        # 标记旧 token 为已使用
        token_record.is_used = True
        token_record.used_at = datetime.now(timezone.utc)
        await db.flush()

        # 验证用户存在
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")

        # 生成新令牌
        new_access_token = create_access_token(data={"sub": str(user.user_id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.user_id)})

        # 记录新 refresh token
        new_payload = decode_token(new_refresh_token)
        await _create_refresh_token_record(
            db, str(user.user_id), new_payload.get("jti", ""), token_record.token_family
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=1800
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_token: str = "",
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出 - 撤销 refresh token
    """
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti", "")
            if jti:
                result = await db.execute(
                    select(RefreshToken).where(
                        RefreshToken.user_id == current_user_id,
                        RefreshToken.jti == jti
                    )
                )
                token_record = result.scalar_one_or_none()
                if token_record:
                    token_record.is_revoked = True
                    token_record.revoked_at = datetime.now(timezone.utc)
                    await db.flush()
        except Exception:
            pass

    return MessageResponse(message="已成功登出")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    result = await db.execute(select(User).where(User.user_id == current_user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return user
