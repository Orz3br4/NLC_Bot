# 建立 builder 階段
FROM python:3.9-slim as builder

# 設置工作目錄
WORKDIR /app

# 安裝編譯相關依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements 文件
COPY requirements.txt .

# 建立虛擬環境並安裝依賴
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# 建立最終映像
FROM python:3.9-slim

# 複製虛擬環境
COPY --from=builder /opt/venv /opt/venv

# 設置環境變數
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 設置工作目錄
WORKDIR /app

# 複製應用程式代碼
COPY ./src .

# 建立非 root 用戶
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 執行應用程式
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
