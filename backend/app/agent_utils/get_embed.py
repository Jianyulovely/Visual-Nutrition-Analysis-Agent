import chromadb
# 必须导入这个类型基类
from chromadb.api.types import EmbeddingFunction 
from langchain_community.embeddings import DashScopeEmbeddings
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), verbose=True)

def get_embedding_model():
    """
    创建一个千问旗下的向量嵌入模型
    """
    embedding_model = DashScopeEmbeddings(
        model="text-embedding-v3",
    )

    return embedding_model

class DashScopeEmbeddingAdapter(EmbeddingFunction):
    """将 LangChain 的 DashScope 包装成 Chroma 兼容的格式"""
    def __init__(self):
        self.model = get_embedding_model()

    def __call__(self, input: list[str]) -> list[list[float]]:
        # Chroma 调用时会传入文本列表，返回向量列表
        return self.model.embed_documents(input)