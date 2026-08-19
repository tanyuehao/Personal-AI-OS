"""
Personal AI OS - Logging Configuration
日志配置
"""
import logging
import json
import time
from datetime import datetime, timezone
from typing import Optional
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# 上下文变量
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 添加请求上下文
        if request_id_var.get():
            log_entry["request_id"] = request_id_var.get()
        if user_id_var.get():
            log_entry["user_id"] = user_id_var.get()
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """配置日志"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 移除默认处理器
    root_logger.handlers.clear()
    
    # 添加控制台处理器
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
    
    # 配置特定日志器
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        import uuid
        
        # 生成请求 ID
        request_id = str(uuid.uuid4())[:8]
        request_id_var.set(request_id)
        
        # 记录请求开始
        start_time = time.time()
        logger = logging.getLogger("api")
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # 记录请求完成
            duration = (time.time() - start_time) * 1000
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration:.0f}ms"
            )
            
            # 添加请求 ID 到响应头
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} duration={duration:.0f}ms"
            )
            raise


class LLMLogger:
    """LLM 调用日志"""
    
    @staticmethod
    def log_call(
        provider: str,
        model: str,
        duration_ms: float,
        tokens: Optional[dict] = None,
        error: Optional[str] = None
    ):
        """记录 LLM 调用"""
        logger = logging.getLogger("llm")
        
        log_entry = {
            "provider": provider,
            "model": model,
            "duration_ms": duration_ms,
        }
        
        if tokens:
            log_entry["tokens"] = tokens
        if error:
            log_entry["error"] = error
        
        if error:
            logger.error(f"LLM call failed: {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            logger.info(f"LLM call completed: {json.dumps(log_entry, ensure_ascii=False)}")
