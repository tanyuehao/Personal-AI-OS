"""
Personal AI OS - Main Application
主应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings as app_settings
from app.core.database import init_db, close_db
from app.api import auth, documents, knowledge, chat, memory, belief, decision, usage, agent, multimodal, voice
from app.api import settings as settings_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(f"Starting {app_settings.APP_NAME} v{app_settings.APP_VERSION}")
    await init_db()
    print("Database initialized")
    
    yield
    
    await close_db()
    print("Application closed")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=app_settings.APP_NAME,
        version=app_settings.APP_VERSION,
        description=app_settings.APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(auth.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(documents.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(knowledge.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(chat.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(memory.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(belief.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(decision.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(settings_api.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(usage.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(agent.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(multimodal.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(voice.router, prefix=app_settings.API_V1_PREFIX)
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app": app_settings.APP_NAME,
            "version": app_settings.APP_VERSION
        }
    
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {app_settings.APP_NAME}",
            "version": app_settings.APP_VERSION,
            "docs": "/docs"
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=app_settings.DEBUG
    )
