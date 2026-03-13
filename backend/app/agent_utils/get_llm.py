import os

from langchain_community.chat_models.tongyi import ChatTongyi
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("环境变量 DASHSCOPE_API_KEY 未设置，请检查 .env 文件")

_llm_instance = None
_vision_llm_instance = None


def get_llm():
    """
    返回千问语言模型单例
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatTongyi(model="qwen-plus", temperature=0)
    return _llm_instance


def get_vision_llm():
    """
    返回视觉语言模型单例
    """
    global _vision_llm_instance
    if _vision_llm_instance is None:
        _vision_llm_instance = ChatTongyi(model="qwen3-vl-plus", temperature=0.1)
    return _vision_llm_instance