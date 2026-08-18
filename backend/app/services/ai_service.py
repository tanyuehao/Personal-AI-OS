"""
Personal AI OS - AI Service
AI 服务模块 - 支持多种模型提供商
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class AIResponse:
    """AI 响应"""
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None


class BaseAIService(ABC):
    """AI 服务基类"""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """聊天接口"""
        pass
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成 embedding"""
        pass


class DeepSeekService(BaseAIService):
    """DeepSeek 服务 - 便宜好用，推荐使用"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        from app.core.config import settings
        self.api_key = api_key
        self.model = model
        self.base_url = settings.DEEPSEEK_API_BASE
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """调用 DeepSeek 聊天接口"""
        import httpx
        
        api_messages = []
        
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        api_messages.extend(messages)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            data = response.json()
            
            if "error" in data:
                raise Exception(f"DeepSeek API 错误: {data['error'].get('message', '未知错误')}")
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                usage=data.get("usage"),
                model=self.model
            )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """DeepSeek 暂不支持 embedding，使用 OpenAI 兼容接口"""
        # DeepSeek 目前不提供 embedding 服务
        # 可以使用 SiliconFlow 的免费 embedding
        raise NotImplementedError("DeepSeek 不支持 embedding，请使用其他提供商")


class MiMoService(BaseAIService):
    """小米 MiMo 服务 - 通过 SiliconFlow 提供"""

    def __init__(self, api_key: str, model: str = "XiaomiMiMo-7B-RL"):
        from app.core.config import settings
        self.api_key = api_key
        self.model = model
        self.base_url = settings.SILICONFLOW_API_BASE
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """调用 MiMo 聊天接口"""
        import httpx
        
        api_messages = []
        
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        api_messages.extend(messages)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            data = response.json()
            
            if "error" in data:
                raise Exception(f"MiMo API 错误: {data['error'].get('message', '未知错误')}")
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                usage=data.get("usage"),
                model=self.model
            )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """通过 SiliconFlow 调用 embedding"""
        import httpx
        from app.core.config import settings

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.EMBEDDING_MODEL,
                    "input": texts
                }
            )
            
            data = response.json()
            
            if "error" in data:
                raise Exception(f"Embedding API 错误: {data['error'].get('message', '未知错误')}")
            
            return [item["embedding"] for item in data["data"]]


class OpenAIService(BaseAIService):
    """OpenAI 服务"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from app.core.config import settings
        self.api_key = api_key
        self.model = model
        self.base_url = settings.OPENAI_API_BASE
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """调用 OpenAI 聊天接口"""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # 构建消息列表
        api_messages = []
        
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        api_messages.extend(messages)
        
        # 调用 API
        response = await client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return AIResponse(
            content=response.choices[0].message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None,
            model=self.model
        )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成 embedding"""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        
        return [item.embedding for item in response.data]


class LocalModelService(BaseAIService):
    """本地模型服务（Ollama）"""
    
    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "qwen2.5:7b"):
        self.base_url = base_url
        self.model = model
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """调用本地模型聊天接口"""
        import httpx
        
        api_messages = []
        
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        api_messages.extend(messages)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            data = response.json()
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                usage=data.get("usage"),
                model=self.model
            )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成 embedding（使用本地模型）"""
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            embeddings = []
            for text in texts:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "input": text
                    }
                )
                data = response.json()
                embeddings.append(data["data"][0]["embedding"])
            
            return embeddings


class FallbackAIService(BaseAIService):
    """带降级的 AI 服务 - 自动尝试多个提供商"""
    
    def __init__(self, services: List[BaseAIService]):
        self.services = services
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """带降级的聊天接口"""
        last_error = None
        
        for service in self.services:
            try:
                return await service.chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as e:
                last_error = e
                continue
        
        raise Exception(f"所有 AI 服务都失败了: {str(last_error)}")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """带降级的 embedding 接口"""
        last_error = None
        
        for service in self.services:
            try:
                return await service.embed(texts)
            except Exception:
                last_error = Exception("不支持 embedding")
                continue
        
        raise Exception(f"所有 Embedding 服务都失败了: {str(last_error)}")


def create_ai_service(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> BaseAIService:
    """
    创建 AI 服务

    Args:
        provider: 提供商（siliconflow, deepseek, openai, local, auto）
        api_key: API 密钥
        model: 模型名称

    Returns:
        AI 服务实例
    """
    from app.core.config import settings

    if provider is None:
        provider = settings.AI_PROVIDER

    # 如果是自动模式，创建带降级的服务
    if provider == "auto":
        services = []
        for p in settings.MODEL_PRIORITY:
            try:
                service = _create_service(p)
                if service:
                    services.append(service)
            except Exception:
                continue

        if not services:
            raise ValueError("没有可用的 AI 服务，请配置 API 密钥")

        return FallbackAIService(services)

    return _create_service(provider, api_key, model)


def _create_service(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[BaseAIService]:
    """创建单个服务"""
    from app.core.config import settings

    # siliconflow 和 mimo 使用同一个 SiliconFlow API
    if provider in ("siliconflow", "mimo"):
        api_key = api_key or settings.SILICONFLOW_API_KEY
        if not api_key:
            return None
        return MiMoService(
            api_key=api_key,
            model=model or settings.LLM_MODEL
        )

    elif provider == "deepseek":
        api_key = api_key or settings.DEEPSEEK_API_KEY
        if not api_key:
            return None
        return DeepSeekService(
            api_key=api_key,
            model=model or settings.DEEPSEEK_MODEL
        )

    elif provider == "openai":
        api_key = api_key or settings.OPENAI_API_KEY
        if not api_key:
            return None
        return OpenAIService(
            api_key=api_key,
            model=model or settings.OPENAI_MODEL
        )

    elif provider == "local":
        if not settings.LOCAL_MODEL_ENABLED:
            return None
        return LocalModelService(
            base_url=settings.LOCAL_MODEL_BASE,
            model=model or settings.LOCAL_MODEL_NAME
        )

    else:
        raise ValueError(f"不支持的 AI 提供商: {provider}")


def get_embedding_service(
    provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> BaseAIService:
    """
    获取 Embedding 服务

    Args:
        provider: 提供商
        api_key: API 密钥

    Returns:
        AI 服务实例（支持 embed 方法）
    """
    from app.core.config import settings

    if provider is None:
        provider = settings.EMBEDDING_PROVIDER

    # Embedding 服务优先级：siliconflow > openai > local
    if provider in ("siliconflow", "mimo"):
        api_key = api_key or settings.SILICONFLOW_API_KEY
        if api_key:
            return MiMoService(api_key=api_key)

    if provider == "openai":
        api_key = api_key or settings.OPENAI_API_KEY
        if api_key:
            return OpenAIService(api_key=api_key)

    if provider == "local":
        return LocalModelService()

    # 默认尝试 siliconflow
    if settings.SILICONFLOW_API_KEY:
        return MiMoService(api_key=settings.SILICONFLOW_API_KEY)

    # 尝试 OpenAI
    if settings.OPENAI_API_KEY:
        return OpenAIService(api_key=settings.OPENAI_API_KEY)

    raise ValueError("没有可用的 Embedding 服务，请配置 API 密钥")
