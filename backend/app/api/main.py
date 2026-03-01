from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
import uuid
from app.agents.main_agent import VisionAnalysisAgent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
agent = VisionAnalysisAgent()

# 确保上传目录存在
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             # 允许所有来源（包括你的小程序域名或本地调试）
    allow_credentials=True,
    allow_methods=["*"],             # 允许所有请求方法 (POST, GET 等)
    allow_headers=["*"],             # 允许所有请求头
)

@app.post("/analyze")
async def analyze_nutrition(username: str = Form(...), image: UploadFile = File(...)):
    # 1. 保存上传的文件到临时路径
    file_ext = image.filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{file_ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # 2. 调用你的 VisionAnalysisAgent
    try:
        # thread_id 可用于多轮对话状态保持，此处先给一个随机值
        # 这里run返回是一个AgentState
        full_state = agent.run(username=username, image_path=file_path, thread_id="user_session_001")
        
        # 检查图片是否有效
        error_reason = full_state.get("error_reason")
        if error_reason:
            return {
                "status": "invalid_image",
                "message": error_reason
            }
        
        result = full_state.get("analysis_results", {}).get("final_response")
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}