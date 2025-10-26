"""
FastAPI application configuration and database setup
"""
import os
import secrets
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Authentication configuration
SECRET_KEY = os.environ.get("AIVA_AUTH_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# API Keys and URLs
DEEPSEEK_API_KEY = "sk-eef721b513bc408e9cd14d16e92e5091"  # DeepSeek AI API密钥
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API端点

# 即梦AI配置
JIMENG_ACCESS_KEY_ID = os.environ.get("JIMENG_ACCESS_KEY_ID", "AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU")
JIMENG_SECRET_ACCESS_KEY = os.environ.get("JIMENG_SECRET_ACCESS_KEY", "TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ==")

# FastAPI application initialization
app = FastAPI(
    title="AI视频生成平台API",
    description="完整的AI视频生成服务，支持剧本生成、分镜拆解、图片生成、视频生成等功能",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境应限制具体域名）
    allow_credentials=True,  # 允许携带认证信息
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# Add request/response logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware to log all requests and responses, with detailed error logging"""
    import time
    import json

    start_time = time.time()

    # Log incoming request
    print(f"\n📨 REQUEST: {request.method} {request.url}")
    print(f"   Headers: {dict(request.headers)}")

    # Try to log request body for POST/PUT requests
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                try:
                    json_body = json.loads(body)
                    print(f"   Body: {json.dumps(json_body, indent=2)}")
                except:
                    print(f"   Body: {body.decode('utf-8', errors='ignore')[:500]}...")
        except Exception as e:
            print(f"   Could not read request body: {e}")

    try:
        # Process the request
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log successful response
        print(f"✅ RESPONSE: {response.status_code} in {process_time:.3f}s")

        # Log response body for errors
        if response.status_code >= 400:
            print(f"❌ ERROR RESPONSE: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            try:
                # Try to get response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                if response_body:
                    try:
                        json_response = json.loads(response_body)
                        print(f"   Response Body: {json.dumps(json_response, indent=2)}")
                    except:
                        print(f"   Response Body: {response_body.decode('utf-8', errors='ignore')[:1000]}")

                # Reconstruct response for client
                response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except Exception as e:
                print(f"   Could not read response body: {e}")

        return response

    except Exception as e:
        process_time = time.time() - start_time
        print(f"💥 EXCEPTION: {type(e).__name__}: {e} (after {process_time:.3f}s)")
        import traceback
        traceback.print_exc()
        raise

# Database configuration
DATABASE_URL = "sqlite+aiosqlite:///./prompts.db"  # SQLite数据库连接字符串
engine = create_async_engine(DATABASE_URL, echo=True)  # 创建异步数据库引擎，启用SQL日志
Base = declarative_base()  # 创建ORM基类
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # 创建异步会话工厂
