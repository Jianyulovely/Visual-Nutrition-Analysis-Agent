import base64
import mimetypes

# 将图片转换为Base64编码的Data URI
def process_pic(image_path: str) -> str:
    try:
        # 自动识别图片的 MIME 类型 (如 image/jpeg, image/png)
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"  # 默认值
            
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        # 关键：必须拼接 Data URI 前缀。否则大模型无法识别协议
        return f"data:{mime_type};base64,{encoded_string}"
        
    except Exception as e:
        print(f"Error processing image: {e}")
        raise e