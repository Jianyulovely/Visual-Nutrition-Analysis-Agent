import os
import uuid

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from app.agents.main_agent import VisionAnalysisAgent
from models.schemas import ApiResponse

app = FastAPI()
agent = VisionAnalysisAgent()

# 确保上传目录存在
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 允许的图片 MIME 类型与最大文件大小
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze", response_model=ApiResponse)
async def analyze_nutrition(username: str = Form(...), image: UploadFile = File(...)):
    # 1. 安全校验：MIME 类型
    if image.content_type not in ALLOWED_MIME:
        return ApiResponse(status="error", message=f"不支持的文件类型: {image.content_type}")

    # 2. 读取文件内容（异步）并校验大小
    content = await image.read()
    if len(content) > MAX_FILE_SIZE:
        return ApiResponse(status="error", message="文件过大，请上传小于 10MB 的图片")

    # 3. 保存到临时路径
    file_ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "jpg"
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{file_ext}")
    with open(file_path, "wb") as f:
        f.write(content)

    # 4. 调用 Agent，无论成功失败都删除临时文件
    try:
        thread_id = f"{username}_{uuid.uuid4().hex[:8]}"
        full_state = agent.run(username=username, image_path=file_path, thread_id=thread_id)

        error_reason = full_state.get("error_reason")
        if error_reason:
            return ApiResponse(status="invalid_image", message=error_reason)

        report = full_state.get("analysis_results")
        if report is None:
            return ApiResponse(status="error", message="分析流程未返回结果，请重试")
        return ApiResponse(status="success", data=report.model_dump())

    except Exception as e:
        return ApiResponse(status="error", message=str(e))

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
