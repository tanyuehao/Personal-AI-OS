"""
Personal AI OS - Text Chunker
文本切片服务
"""
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TextChunk:
    """文本切片"""
    content: str
    chunk_index: int
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    metadata: Optional[dict] = None


class TextChunker:
    """文本切片器"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        初始化切片器
        
        Args:
            chunk_size: 切片大小（字符数）
            chunk_overlap: 切片重叠大小
            min_chunk_size: 最小切片大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        按句子分割文本
        """
        import re
        
        # 支持中英文标点
        sentence_endings = r'[。！？.!?；;]'
        sentences = re.split(sentence_endings, text)
        
        # 过滤空字符串并保留标点
        result = []
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                # 如果不是最后一个，添加标点回去
                if i < len(sentences) - 1:
                    # 查找原始标点
                    match = re.search(r'[。！？.!?；;]', text[len(''.join(sentences[:i+1])):])
                    if match:
                        sentence += match.group()
                result.append(sentence.strip())
        
        return result
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """
        合并过小的切片
        """
        if not chunks:
            return chunks
        
        merged = []
        current_chunk = chunks[0]
        
        for i in range(1, len(chunks)):
            if len(current_chunk) + len(chunks[i]) <= self.chunk_size:
                current_chunk += " " + chunks[i]
            else:
                if len(current_chunk) >= self.min_chunk_size:
                    merged.append(current_chunk)
                current_chunk = chunks[i]
        
        # 添加最后一个切片
        if len(current_chunk) >= self.min_chunk_size:
            merged.append(current_chunk)
        elif merged:
            # 如果最后一个太小，合并到前一个
            merged[-1] += " " + current_chunk
        
        return merged
    
    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        将文本切片

        Args:
            text: 输入文本

        Returns:
            切片列表
        """
        if not text or not text.strip():
            return []

        # 短文本直接作为单个切片
        if len(text.strip()) < self.min_chunk_size:
            return [TextChunk(
                content=text.strip(),
                chunk_index=0,
                metadata={
                    "chunk_size": len(text.strip()),
                    "total_chunks": 1
                }
            )]

        # 按句子分割
        sentences = self._split_by_sentences(text)

        if not sentences:
            return [TextChunk(
                content=text.strip(),
                chunk_index=0,
                metadata={"chunk_size": len(text.strip()), "total_chunks": 1}
            )]

        # 合并小切片
        chunks_text = self._merge_small_chunks(sentences)

        # 转换为 TextChunk 对象
        chunks = []
        for i, chunk_text in enumerate(chunks_text):
            chunks.append(TextChunk(
                content=chunk_text,
                chunk_index=i,
                metadata={
                    "chunk_size": len(chunk_text),
                    "total_chunks": len(chunks_text)
                }
            ))

        return chunks
    
    def chunk_by_fixed_size(self, text: str) -> List[TextChunk]:
        """
        按固定大小切片（备用方案）
        
        Args:
            text: 输入文本
        
        Returns:
            切片列表
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在句号处断开
            if end < len(text):
                # 查找最近的句号
                for i in range(end, max(start + self.min_chunk_size, end - 100), -1):
                    if i < len(text) and text[i] in '。！？.!?；;\n':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(TextChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    metadata={
                        "chunk_size": len(chunk_text),
                        "start_pos": start,
                        "end_pos": end
                    }
                ))
                chunk_index += 1
            
            # 下一块的起始位置（考虑重叠）
            start = end - self.chunk_overlap
        
        return chunks


def create_chunker(
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    min_chunk_size: int = 100
) -> TextChunker:
    """
    创建文本切片器
    
    Args:
        chunk_size: 切片大小
        chunk_overlap: 重叠大小
        min_chunk_size: 最小切片大小
    
    Returns:
        TextChunker 实例
    """
    return TextChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        min_chunk_size=min_chunk_size
    )
