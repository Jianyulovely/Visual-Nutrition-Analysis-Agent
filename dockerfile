FROM python:3.11-slim

WORKDIR /app

# 新增：安装系统依赖 git
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/backend

EXPOSE 80

CMD ["uvicorn", "backend.app.api.main:app", "--host", "0.0.0.0", "--port", "80"]