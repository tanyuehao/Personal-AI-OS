"""
Personal AI OS - Model Gateway
统一模型调用接口
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class GatewayResponse:
    """网关响应"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    duration_ms: float = 0
    cached: bool = False


@dataclass
class GatewayRequest:
    """网关请求"""
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    user_id: Optional[str] = None
    request_id: Optional[str] = None


class ModelProvider(ABC):
    """模型提供商基类"""
    
    @abstractmethod
    async def chat(self, request: GatewayRequest) -> GatewayResponse:
        pass
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        pass


class SiliconFlowProvider(ModelProvider):
    """硅基流动提供商"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1"):
        self.api_key = api_key
        self.base_url = base_url
    
    async def chat(self, request: GatewayRequest) -> GatewayResponse:
        import httpx
        
        start_time = time.time()
        model = request.model or "deepseek-ai/DeepSeek-V3"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": request.messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            data = response.json()
            duration_ms = (time.time() - start_time) * 1000
            
            if "error" in data:
                raise Exception(f"SiliconFlow API 错误: {data['error'].get('message', '未知错误')}")
            
            return GatewayResponse(
                content=data["choices"][0]["message"]["content"],
                model=model,
                provider="siliconflow",
                usage=data.get("usage"),
                duration_ms=duration_ms
            )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "BAAI/bge-m3",
                    "input": texts
                }
            )
            
            data = response.json()
            
            if "error" in data:
                raise Exception(f"Embedding API 错误: {data['error'].get('message', '未知错误')}")
            
            return [item["embedding"] for item in data["data"]]


class DeepSeekProvider(ModelProvider):
    """DeepSeek 提供商"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
    
    async def chat(self, request: GatewayRequest) -> GatewayResponse:
        import httpx
        
        start_time = time.time()
        model = request.model or "deepseek-chat"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": request.messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            data = response.json()
            duration_ms = (time.time() - start_time) * 1000
            
            if "error" in data:
                raise Exception(f"DeepSeek API 错误: {data['error'].get('message', '未知错误')}")
            
            return GatewayResponse(
                content=data["choices"][0]["message"]["content"],
                model=model,
                provider="deepseek",
                usage=data.get("usage"),
                duration_ms=duration_ms
            )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("DeepSeek 不支持 embedding")


class ModelGateway:
    """模型网关"""
    
    def __init__(self):
        self._providers: Dict[str, ModelProvider] = {}
        self._default_provider: Optional[str] = None
    
    def register_provider(self, name: str, provider: ModelProvider, is_default: bool = False):
        """注册提供商"""
        self._providers[name] = provider
        if is_default:
            self._default_provider = name
    
    def get_provider(self, name: Optional[str] = None) -> ModelProvider:
        """获取提供商"""
        provider_name = name or self._default_provider
        if provider_name not in self._providers:
            raise ValueError(f"未找到提供商: {provider_name}")
        return self._providers[provider_name]
    
    async def chat(self, request: GatewayRequest, provider_name: Optional[str] = None) -> GatewayResponse:
        """统一聊天接口"""
        provider = self.get_provider(provider_name)
        
        # 记录日志
        logger.info(
            f"[Gateway] chat request: provider={provider_name or self._default_provider}, "
            f"model={request.model}, user_id={request.user_id}, "
            f"request_id={request.request_id}"
        )
        
        try:
            response = await provider.chat(request)
            
            # 记录成功日志
            logger.info(
                f"[Gateway] chat success: model={response.model}, "
                f"duration={response.duration_ms:.0f}ms, "
                f"tokens={response.usage}"
            )
            
            return response
            
        except Exception as e:
            # 记录错误日志
            logger.error(
                f"[Gateway] chat error: provider={provider_name}, "
                f"error={str(e)}, request_id={request.request_id}"
            )
            raise
    
    async def embed(self, texts: List[str], provider_name: Optional[str] = None) -> List[List[float]]:
        """统一 embedding 接口"""
        provider = self.get_provider(provider_name)
        return await provider.embed(texts)


# 全局网关实例
_gateway: Optional[ModelGateway] = None


def get_gateway() -> ModelGateway:
    """获取全局网关实例"""
    global _gateway
    if _gateway is None:
        from app.core.config import settings
        
        _gateway = ModelGateway()
        
        # 注册硅基流动
        if settings.SILICONFLOW_API_KEY:
            _gateway.register_provider(
                "siliconflow",
                SiliconFlowProvider(
                    api_key=settings.SILICONFLOW_API_KEY,
                    base_url=settings.SILICONFLOW_API_BASE
                ),
                is_default=(settings.AI_PROVIDER == "siliconflow")
            )
        
        # 注册 DeepSeek
        if settings.DEEPSEEK_API_KEY:
            _gateway.register_provider(
                "deepseek",
                DeepSeekProvider(
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url=settings.DEEPSEEK_API_BASE
                ),
                is_default=(settings.AI_PROVIDER == "deepseek")
            )
    
    return _gateway
