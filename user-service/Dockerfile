FROM python:3.9-slim

WORKDIR /app

# 安裝開發所需的套件
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements 文件
COPY user-service/requirements.txt .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 環境變數設置
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 建立非 root 用戶並設置適當的權限
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 創建並授權 migrations 目錄
USER root
RUN mkdir -p /app/src/alembic/versions && chown -R appuser:appuser /app/src/alembic
USER appuser