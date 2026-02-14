from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
import uuid
from app.agents.main_agent import VisionAnalysisAgent

app = FastAPI()
agent = VisionAnalysisAgent()

# 确保上传目录存在
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        result = full_state.get("analysis_results", {}).get("final_response")
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}