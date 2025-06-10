from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
from app.routes import api
from app.models import Base
from app.database import engine

app = FastAPI(title="User Service API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-in-production")

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發環境設置，生產環境要改為具體的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 設置靜態檔案目錄
app.mount("/assets", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "assets")), name="assets")

app.include_router(api.router)

# 在應用啟動時創建資料表
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)