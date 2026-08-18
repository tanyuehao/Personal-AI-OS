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
        
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 未配置")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本的 embedding 向量
        
        Args:
            texts: 文本列表
        
        Returns:
            向量列表
        """
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        response = await client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimension
        )
        
        return [item.embedding for item in response.data]
    
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
        provider: 提供商（openai 或 local）
        **kwargs: 额外参数
    
    Returns:
        Embedding 服务实例
    """
    if provider == "openai":
        return OpenAIEmbedding(**kwargs)
    elif provider == "local":
        return LocalEmbedding(**kwargs)
    else:
        raise ValueError(f"不支持的 Embedding 提供商: {provider}")
