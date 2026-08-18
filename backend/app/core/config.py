"""
Personal AI OS - Core Configuration
核心配置模块
"""
import secrets
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "Personal AI OS"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "个人认知操作系统"
    DEBUG: bool = False

    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/personal_ai_os"
    DATABASE_ECHO: bool = False

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT 认证配置（生产环境必须通过 .env 设置 SECRET_KEY）
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==================== 硅基流动 SiliconFlow 配置 ====================
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_API_BASE: str = "https://api.siliconflow.cn/v1"

    # ---------- 语言模型配置 ----------
    # 统一使用 AI_PROVIDER 作为 provider 选择字段
    AI_PROVIDER: str = "siliconflow"  # siliconflow, deepseek, openai, local, auto
    LLM_MODEL: str = "deepseek-ai/DeepSeek-V3"

    # DeepSeek 直连（可选）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # OpenAI（可选）
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ---------- Embedding 模型配置 ----------
    EMBEDDING_PROVIDER: str = "siliconflow"  # siliconflow, openai, local
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024

    # ---------- Reranker 模型配置 ----------
    RERANKER_ENABLED: bool = True
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"

    # ---------- 图片模型配置 ----------
    IMAGE_MODEL_ENABLED: bool = True
    IMAGE_MODEL: str = "Kwai-Kolors/Kolors"

    # ==================== 本地配置 ====================
    LOCAL_MODEL_ENABLED: bool = False
    LOCAL_MODEL_BASE: str = "http://localhost:11434/v1"
    LOCAL_MODEL_NAME: str = "qwen2.5:7b"

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB

    # 向量数据库配置
    VECTOR_DB_TYPE: str = "pgvector"
    QDRANT_URL: str = "http://localhost:6333"

    # 模型优先级（按顺序尝试）
    MODEL_PRIORITY: List[str] = ["siliconflow", "deepseek"]

    def model_post_init(self, __context):
        """启动时检查关键配置"""
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(64)
            if self.DEBUG:
                import warnings
                warnings.warn(
                    "SECRET_KEY 未设置，已自动生成随机密钥。"
                    "生产环境请在 .env 中设置固定的 SECRET_KEY。",
                    stacklevel=2,
                )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（带缓存）"""
    return Settings()


settings = get_settings()
