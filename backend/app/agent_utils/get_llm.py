from langchain_community.chat_models.tongyi import ChatTongyi
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), verbose=True)

def get_llm():
    """
    创建一个千问语言模型
    """
    llm = ChatTongyi(
        model="qwen-plus", 
        temperature=0
    )
    
    return llm

def get_vision_llm():
    """
    创建一个视觉语言模型
    """
    vision_llm = ChatTongyi(
        model="qwen3-vl-plus", 
        temperature=0.1
    )
    
    return vision_llm