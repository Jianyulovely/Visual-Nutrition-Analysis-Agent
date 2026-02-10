import os
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from get_embed import get_embedding_model

def parse_pdf_to_vectorstore(pdf_path: str, store_dir: str, embeddings):
    """
    解析 PDF 文件并创建向量数据库，保存到本地。
    
    :param pdf_path: PDF 文件路径
    :param store_dir: 向量数据库保存目录
    :param embeddings: 嵌入模型
    :return: 创建的向量数据库
    """
    print(f"正在解析 PDF: {pdf_path} ...")
    # 1. 加载并切分
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    
    # 2. 创建并保存
    vectorstore = FAISS.from_documents(splits, embeddings)
    vectorstore.save_local(store_dir)
    print(f"知识库已成功保存至: {store_dir}")

    return vectorstore


def load_pdf_vectorstore(store_dir: str, embeddings):
    """
    从本地加载已保存的 PDF 向量数据库。
    
    :param store_dir: 向量数据库保存目录
    :param embeddings: 嵌入模型
    :return: 加载的向量数据库
    """
    print(f"正在从 {store_dir} 加载知识库...")
    # 注意：加载时需要开启 allow_dangerous_deserialization
    return FAISS.load_local(store_dir, embeddings, allow_dangerous_deserialization=True)


if __name__ == "__main__":
    # 示例使用
    pdf_path = "/data3/yjy/envs/agent/agent_codes/Nutrition_agent/Nutritional Guidelines.pdf"
    store_dir = "/data3/yjy/envs/agent/agent_codes/Nutrition_agent/nutrition_knowledge"
    
    # 初始化嵌入模型
    embeddings = get_embedding_model()
    
    # 创建或加载向量数据库
    vectorstore = parse_pdf_to_vectorstore(pdf_path, store_dir, embeddings)