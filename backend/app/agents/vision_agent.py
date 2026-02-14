from app.agent_utils.get_llm import get_vision_llm
from app.agent_utils.process_pic import process_pic
from app.agent_utils.agent_prompt import VISION_NODE_PROMPT

from pydantic import BaseModel, Field


# 定义结构化输出模型
class VisionResponse(BaseModel):
    is_valid: bool = Field(description="图片是否清晰且包含食物")
    reason: str = Field(description="如果不合法，说明原因（如：图片模糊、非食物、无图片）")
    report: str = Field(description="识别到的食材详细报告，若不合法则为空")


class VisionAgent:
    def __init__(self):
        self.system_prompt = VISION_NODE_PROMPT

        # 1. 获取vl模型
        self.model = get_vision_llm().with_structured_output(VisionResponse)
    
    def analyze_image(self, image_path: str) -> str:
        """
        将输入图片转换为base64编码，然后调用vision_llm分析图片中的食物并返回营养信息
        """
        img_base64 = process_pic(image_path)
        message = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "分析图中菜品信息"},
                    {
                        "type": "image",
                        "image": img_base64  # dashscope要求image字段，而且对应内容为一个字符串
                    }
                ]
            }
        ]
        # 3. 调用 invoke 后，从结果的 structured_response 键中获取对象   
        result = self.model.invoke(message)
                
        return result


if __name__ == "__main__":
    vision_agent = VisionAgent()
    response = vision_agent.analyze_image("food_pic/西红柿炒鸡蛋.jpg")
    print(response)
