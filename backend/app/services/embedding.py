"""
Personal AI OS - Embedding Service
Embedding 向量生成服务
"""
from typing import List, Optional
from abc import ABC, abstractmethod


class BaseEmbedding(ABC):
    """Embedding 基类"""
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成文本的 embedding 向量"""
        pass
    
    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """生成查询文本的 embedding 向量"""
        pass


class OpenAIEmbedding(BaseEmbedding):
    """OpenAI Embedding 服务"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        dimension: int = 1536
    ):
        """
        初始化 OpenAI Embedding
        
        Args:
            api_key: OpenAI API Key
            model: Embedding 模型名称
            dimension: 向量维度
        """
        from app.core.config import settings

        self.api_key = api_key or settings.SILICONFLOW_API_KEY or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION

        if not self.api_key:
            raise ValueError("未配置 API Key（需要 SILICONFLOW_API_KEY 或 OPENAI_API_KEY）")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本的 embedding 向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        import httpx
        from app.core.config import settings

        # 使用 SiliconFlow API（OpenAI 兼容）
        base_url = settings.SILICONFLOW_API_BASE or "https://api.siliconflow.cn/v1"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": texts
                }
            )

            data = response.json()

            if "error" in data:
                raise Exception(f"Embedding API 错误: {data['error'].get('message', '未知错误')}")

            if "data" not in data or not data["data"]:
                raise Exception(f"Embedding API 返回空数据: {data}")

            return [item["embedding"] for item in data["data"]]
    
    async def embed_query(self, query: str) -> List[float]:
        """
        生成查询文本的 embedding 向量
        
        Args:
            query: 查询文本
        
        Returns:
            向量
        """
        result = await self.embed([query])
        return result[0]


class LocalEmbedding(BaseEmbedding):
    """本地 Embedding 服务（使用 sentence-transformers）"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化本地 Embedding
        
        Args:
            model_name: 模型名称
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except ImportError:
            raise ImportError("请安装 sentence-transformers: pip install sentence-transformers")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本的 embedding 向量
        
        Args:
            texts: 文本列表
        
        Returns:
            向量列表
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    async def embed_query(self, query: str) -> List[float]:
        """
        生成查询文本的 embedding 向量
        
        Args:
            query: 查询文本
        
        Returns:
            向量
        """
        result = await self.embed([query])
        return result[0]


def create_embedding(
    provider: str = "openai",
    **kwargs
) -> BaseEmbedding:
    """
    创建 Embedding 服务

    Args:
        provider: 提供商（openai, siliconflow, local）
        **kwargs: 额外参数

    Returns:
        Embedding 服务实例
    """
    if provider in ("openai", "siliconflow"):
        # SiliconFlow 使用 OpenAI 兼容接口
        from app.core.config import settings
        kwargs.setdefault("model", settings.EMBEDDING_MODEL)
        kwargs.setdefault("dimension", settings.EMBEDDING_DIMENSION)
        return OpenAIEmbedding(**kwargs)
    elif provider == "local":
        return LocalEmbedding(**kwargs)
    else:
        raise ValueError(f"不支持的 Embedding 提供商: {provider}")
