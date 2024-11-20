FROM python:3.9-slim

WORKDIR /app

# 安裝依賴
COPY user-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 設置 Python 路徑
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 複製源代碼
COPY user-service/src .

# 執行應用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]