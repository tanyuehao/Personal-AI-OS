"""
Personal AI OS - Main Application
主应用入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings as app_settings
from app.core.database import init_db, close_db
from app.core.logging import setup_logging, RequestLoggingMiddleware
from app.core.errors import AppException, ErrorCode
from app.api import auth, documents, knowledge, chat, memory, belief, decision, usage, agent, multimodal, voice, graph, export, cognitive, reflection, decision_style, knowledge_graph, memory_network, communication_style, proactive, learning, reasoning, prediction, context as context_api, monitoring
from app.api import settings as settings_api

# 配置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"Starting {app_settings.APP_NAME} v{app_settings.APP_VERSION}")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    await close_db()
    logger.info("Application closed")


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
    
    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 全局异常处理
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "data": None,
                "error": {
                    "code": exc.error_code.value,
                    "message": exc.message,
                    **(exc.app_detail or {})
                },
                "request_id": request.headers.get("X-Request-ID")
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "data": None,
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "服务器内部错误"
                },
                "request_id": request.headers.get("X-Request-ID")
            }
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
    app.include_router(graph.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(export.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(cognitive.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(reflection.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(decision_style.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(knowledge_graph.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(memory_network.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(communication_style.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(proactive.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(learning.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(reasoning.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(prediction.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(context_api.router, prefix=app_settings.API_V1_PREFIX)
    app.include_router(monitoring.router, prefix=app_settings.API_V1_PREFIX)
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app": app_settings.APP_NAME,
            "version": app_settings.APP_VERSION
        }
    
    @app.get("/health/live")
    async def health_live():
        return {"status": "alive"}
    
    @app.get("/health/ready")
    async def health_ready():
        # 检查数据库连接
        try:
            from app.core.database import engine
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            return {"status": "ready"}
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "not ready", "error": str(e)}
            )
    
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {app_settings.APP_NAME}",
            "version": app_settings.APP_VERSION,
            "docs": "/docs"
        }

    # WebSocket 路由
    from app.api.websocket import router as ws_router
    app.include_router(ws_router)

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
