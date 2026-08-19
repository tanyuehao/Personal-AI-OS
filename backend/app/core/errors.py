"""
Personal AI OS - Error Codes
错误码定义
"""
from enum import Enum
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """错误码"""
    # 认证相关
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_USER_NOT_FOUND = "AUTH_USER_NOT_FOUND"
    AUTH_USER_DISABLED = "AUTH_USER_DISABLED"
    AUTH_CREDENTIALS_INVALID = "AUTH_CREDENTIALS_INVALID"
    
    # 用户相关
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_EMAIL_EXISTS = "USER_EMAIL_EXISTS"
    
    # 文档相关
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    DOCUMENT_PARSE_FAILED = "DOCUMENT_PARSE_FAILED"
    DOCUMENT_EMPTY = "DOCUMENT_EMPTY"
    DOCUMENT_TOO_LARGE = "DOCUMENT_TOO_LARGE"
    DOCUMENT_UNSUPPORTED_TYPE = "DOCUMENT_UNSUPPORTED_TYPE"
    
    # 知识相关
    KNOWLEDGE_NOT_FOUND = "KNOWLEDGE_NOT_FOUND"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    VECTOR_SEARCH_FAILED = "VECTOR_SEARCH_FAILED"
    
    # 记忆相关
    MEMORY_NOT_FOUND = "MEMORY_NOT_FOUND"
    MEMORY_INVALID_TYPE = "MEMORY_INVALID_TYPE"
    
    # 观点相关
    BELIEF_NOT_FOUND = "BELIEF_NOT_FOUND"
    
    # 决策相关
    DECISION_NOT_FOUND = "DECISION_NOT_FOUND"
    
    # Agent 相关
    AGENT_INVALID_TYPE = "AGENT_INVALID_TYPE"
    AGENT_EXECUTION_FAILED = "AGENT_EXECUTION_FAILED"
    
    # 模型相关
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    MODEL_RATE_LIMIT = "MODEL_RATE_LIMIT"
    MODEL_PROVIDER_ERROR = "MODEL_PROVIDER_ERROR"
    MODEL_NOT_CONFIGURED = "MODEL_NOT_CONFIGURED"
    
    # 通用
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppException(HTTPException):
    """应用异常"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Optional[dict] = None
    ):
        self.error_code = error_code
        self.message = message
        self.app_detail = detail
        
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code.value,
                    "message": message,
                    **(detail or {})
                }
            }
        )


def raise_not_found(resource: str, resource_id: str = "") -> None:
    """抛出未找到异常"""
    message = f"{resource}不存在"
    if resource_id:
        message += f": {resource_id}"
    raise AppException(
        error_code=ErrorCode.NOT_FOUND,
        message=message,
        status_code=status.HTTP_404_NOT_FOUND
    )


def raise_validation_error(message: str) -> None:
    """抛出验证错误"""
    raise AppException(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=message,
        status_code=status.HTTP_400_BAD_REQUEST
    )


def raise_auth_error(message: str = "认证失败") -> None:
    """抛出认证错误"""
    raise AppException(
        error_code=ErrorCode.AUTH_REQUIRED,
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED
    )


def raise_forbidden(message: str = "权限不足") -> None:
    """抛出权限错误"""
    raise AppException(
        error_code=ErrorCode.AUTH_INVALID_TOKEN,
        message=message,
        status_code=status.HTTP_403_FORBIDDEN
    )
