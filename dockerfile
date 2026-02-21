FROM python:3.11-slim

WORKDIR /app

# 先复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目
COPY . .

# 暴露 80 端口（云托管默认端口）
EXPOSE 80

# 启动命令，注意路径要对应你的 backend 文件夹
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]