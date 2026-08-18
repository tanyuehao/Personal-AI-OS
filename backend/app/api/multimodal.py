"""
Personal AI OS - Multimodal API
多模态接口（图片识别）
"""
import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.core.security import get_current_user_id
from app.services.ai_service import create_ai_service

router = APIRouter(prefix="/multimodal", tags=["多模态"])


class ImageAnalysisRequest(BaseModel):
    """图片分析请求"""
    question: str = "请描述这张图片的内容"
    image_base64: Optional[str] = None


@router.post("/analyze-image")
async def analyze_image(
    request: ImageAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """分析图片内容"""
    try:
        service = create_ai_service()

        # 使用支持视觉的模型
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": request.question},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{request.image_base64}"}}
            ]}
        ]

        # 调用视觉模型
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.SILICONFLOW_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {"role": "user", "content": [
                            {"type": "text", "text": request.question},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{request.image_base64}"}}
                        ]}
                    ],
                    "max_tokens": 1000
                }
            )
            
            data = response.json()
            return {"answer": data["choices"][0]["message"]["content"]}
            
    except Exception:
        raise HTTPException(status_code=500, detail="图片分析失败")


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    question: str = "请描述这张图片的内容",
    current_user_id: str = Depends(get_current_user_id)
):
    """上传图片并分析"""
    # 读取图片并转为 base64
    content = await file.read()
    image_base64 = base64.b64encode(content).decode()
    
    # 调用分析接口
    request = ImageAnalysisRequest(question=question, image_base64=image_base64)
    return await analyze_image(request, current_user_id)
