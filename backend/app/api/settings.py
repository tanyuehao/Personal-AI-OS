"""
Personal AI OS - Settings API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.core.config import settings as app_settings
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.settings import UserSettings
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdateRequest

router = APIRouter(prefix="/settings", tags=["Settings"])


def _get_fernet():
    """获取 Fernet 加密实例"""
    from cryptography.fernet import Fernet
    import hashlib
    import base64
    # 基于 SECRET_KEY 生成确定性密钥（Fernet 需要 32 字节 base64 编码）
    raw_key = hashlib.sha256(app_settings.SECRET_KEY.encode()).digest()
    key = base64.urlsafe_b64encode(raw_key)
    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """使用 Fernet 对称加密 API Key"""
    if not api_key:
        return ""
    try:
        f = _get_fernet()
        return f.encrypt(api_key.encode()).decode()
    except Exception:
        return ""


def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key"""
    if not encrypted_key:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception:
        return ""


def build_response(settings):
    return UserSettingsResponse(
        settings_id=str(settings.settings_id),
        user_id=str(settings.user_id),
        ai_provider=settings.ai_provider or "siliconflow",
        siliconflow_api_key=decrypt_api_key(settings.siliconflow_api_key) if settings.siliconflow_api_key else "",
        siliconflow_api_base=settings.siliconflow_api_base or "https://api.siliconflow.cn/v1",
        deepseek_api_key=decrypt_api_key(settings.deepseek_api_key) if settings.deepseek_api_key else "",
        deepseek_api_base=settings.deepseek_api_base or "https://api.deepseek.com",
        llm_model=settings.llm_model or "deepseek-ai/DeepSeek-V3",
        embedding_model=settings.embedding_model or "",
        reranker_enabled=settings.reranker_enabled if settings.reranker_enabled is not None else True,
        reranker_model=settings.reranker_model or "BAAI/bge-reranker-v2-m3",
        image_model_enabled=settings.image_model_enabled if settings.image_model_enabled is not None else True,
        image_model=settings.image_model or "",
        temperature=settings.temperature or "0.7",
        max_tokens=settings.max_tokens or "2000"
    )


@router.get("", response_model=UserSettingsResponse)
async def get_settings(current_user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user_id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=current_user_id)
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
    return build_response(settings)


@router.put("", response_model=UserSettingsResponse)
async def update_settings(request: UserSettingsUpdateRequest, current_user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user_id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=current_user_id)
        db.add(settings)
    
    for field in ['ai_provider', 'siliconflow_api_base', 'deepseek_api_base', 'llm_model', 'embedding_model', 'reranker_model', 'image_model', 'temperature', 'max_tokens']:
        val = getattr(request, field, None)
        if val is not None: setattr(settings, field, val)
    
    for field in ['reranker_enabled', 'image_model_enabled']:
        val = getattr(request, field, None)
        if val is not None: setattr(settings, field, val)
    
    # API Key 更新：如果包含 **** 说明是掩码值，跳过保存
    if request.siliconflow_api_key is not None and "****" not in request.siliconflow_api_key:
        settings.siliconflow_api_key = encrypt_api_key(request.siliconflow_api_key)
    if request.deepseek_api_key is not None and "****" not in request.deepseek_api_key:
        settings.deepseek_api_key = encrypt_api_key(request.deepseek_api_key)
    
    await db.flush()
    await db.refresh(settings)
    return build_response(settings)


@router.get("/models")
async def get_available_models(api_key: str):
    if not api_key:
        raise HTTPException(status_code=400, detail="Please enter API Key first")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{app_settings.SILICONFLOW_API_BASE}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed: {response.text}")
            
            data = response.json()
            models = data.get("data", [])
            result = {"chat": [], "embedding": [], "rerank": [], "image": []}
            
            for model in models:
                model_id = model.get("id", "")
                model_info = {"id": model_id, "name": model.get("name", model_id)}
                
                # 按类别标记
                model_type = model.get("model_type", "")
                
                if model_type == "rerank" or "rerank" in model_id.lower():
                    result["rerank"].append(model_info)
                elif model_type == "embedding" or "embed" in model_id.lower() or ("bge" in model_id.lower() and "rerank" not in model_id.lower()):
                    result["embedding"].append(model_info)
                elif model_type == "image" or any(x in model_id.lower() for x in ["stable-diffusion", "flux", "kolors", "dall-e", "cogview"]):
                    result["image"].append(model_info)
                else:
                    result["chat"].append(model_info)
            
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@router.post("/test-connection")
async def test_connection(current_user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user_id))
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=400, detail="Please configure API Key first")
    
    api_key = decrypt_api_key(settings.siliconflow_api_key) if settings.ai_provider == "siliconflow" else decrypt_api_key(settings.deepseek_api_key)
    if not api_key:
        raise HTTPException(status_code=400, detail="Please configure API Key first")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{app_settings.SILICONFLOW_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": settings.llm_model or "deepseek-ai/DeepSeek-V3", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}
            )
            if response.status_code == 200:
                return {"success": True, "message": "Connection successful"}
            return {"success": False, "message": f"Failed: {response.text}"}
    except Exception as e:
        return {"success": False, "message": f"Failed: {str(e)}"}
