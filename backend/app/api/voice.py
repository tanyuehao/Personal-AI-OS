"""
Personal AI OS - Voice API
语音输入接口（语音转文字）
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.core.security import get_current_user_id

router = APIRouter(prefix="/voice", tags=["语音输入"])


class VoiceTranscriptionResponse(BaseModel):
    """语音转写响应"""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None


@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_voice(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    语音转文字
    
    使用 SiliconFlow 的 Whisper 模型进行语音识别
    """
    try:
        import httpx

        # 读取音频文件
        content = await file.read()

        # 调用 SiliconFlow 的 Whisper API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.SILICONFLOW_API_BASE}/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}"
                },
                files={
                    "file": (file.filename, content, file.content_type)
                },
                data={
                    "model": "FunAudioLLM/SenseVoiceSmall"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"转写失败: {response.text}")
            
            data = response.json()
            return VoiceTranscriptionResponse(
                text=data.get("text", ""),
                language=data.get("language"),
                duration=data.get("duration")
            )
            
    except Exception:
        raise HTTPException(status_code=500, detail="语音转写失败")


@router.get("/models")
async def list_voice_models():
    """获取可用的语音模型列表"""
    return {
        "models": [
            {"id": "FunAudioLLM/SenseVoiceSmall", "name": "SenseVoice Small", "description": "快速语音识别"},
            {"id": "FunAudioLLM/SenseVoiceLarge", "name": "SenseVoice Large", "description": "高精度语音识别"}
        ]
    }
