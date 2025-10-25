"""
AI视频生成平台 - 后端API服务
================================

本文件实现了完整的AI视频生成流程，包括：
1. 剧本生成 (DeepSeek AI)
2. 分镜拆解 (DeepSeek AI)
3. 对话提取 (DeepSeek AI)
4. 人物识别 (DeepSeek AI)
5. 人物图片生成 (火山引擎即梦AI)
6. 分镜图片生成 (火山引擎即梦AI)
7. 视频生成 (字节跳动即梦AI)
8. 音频生成 (海螺AI)
9. 视频合并 (FFmpeg)

作者: AI Assistant
版本: 1.0
"""

# ==================== 导入依赖包 ====================
import httpx  # 异步HTTP客户端
import os
from fastapi import FastAPI  # Web框架
from fastapi.middleware.cors import CORSMiddleware  # CORS中间件
from pydantic import BaseModel  # 数据验证
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  # 异步数据库
from sqlalchemy.orm import sessionmaker, declarative_base  # ORM
from sqlalchemy import Column, Integer, String, DateTime  # 数据库字段类型
from sqlalchemy import Boolean
import asyncio  # 异步编程
from sqlalchemy.future import select  # 异步查询
from fastapi import Body
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
import json  # JSON处理
import re  # 正则表达式
from datetime import datetime  # 时间处理
from datetime import timedelta
import aiofiles  # 异步文件操作
import tempfile  # 临时文件
import requests  # HTTP请求
from pathlib import Path  # 路径处理
import hashlib  # 哈希算法
import hmac  # HMAC签名
import base64  # Base64编码
from urllib.parse import quote  # URL编码
import time  # 时间处理
import subprocess  # 用于执行外部命令
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

# 认证配置
SECRET_KEY = os.environ.get("AIVA_AUTH_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ==================== FastAPI应用初始化 ====================
app = FastAPI(
    title="AI视频生成平台API",
    description="完整的AI视频生成服务，支持剧本生成、分镜拆解、图片生成、视频生成等功能",
    version="1.0.0"
)

# 配置CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境应限制具体域名）
    allow_credentials=True,  # 允许携带认证信息
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# ==================== 数据库配置 ====================
DATABASE_URL = "sqlite+aiosqlite:///./prompts.db"  # SQLite数据库连接字符串
engine = create_async_engine(DATABASE_URL, echo=True)  # 创建异步数据库引擎，启用SQL日志
Base = declarative_base()  # 创建ORM基类
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # 创建异步会话工厂

# ==================== 用户与认证模型 ====================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, nullable=False)

# 密码与令牌工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire_ts = int(time.time()) + expires_minutes * 60
    to_encode.update({"exp": expire_ts})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ==================== 数据库模型定义 ====================

class Prompt(Base):
    """用户提示词表 - 存储用户输入的原始提示词"""
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String, nullable=False)  # 用户输入的提示词
    style = Column(String, nullable=False)  # 视频风格（如：Realistic, Cartoon等）
    aspect_ratio = Column(String, nullable=False)  # 视频比例（如：16:9, 9:16等）

class Step1Request(BaseModel):
    """步骤1请求模型 - 用于接收用户输入的提示词"""
    prompt: str  # 用户提示词
    style: str  # 视频风格
    aspect_ratio: str  # 视频比例

class AIScript(Base):
    """AI生成的剧本表 - 存储DeepSeek生成的完整剧本"""
    __tablename__ = "ai_scripts"
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer)  # 关联到Prompt表的ID
    prompt = Column(String, nullable=False)  # 原始提示词
    style = Column(String, nullable=False)  # 视频风格
    aspect_ratio = Column(String, nullable=False)  # 视频比例
    script = Column(String, nullable=False)  # AI生成的完整剧本内容

class ShotBreakdown(Base):
    """分镜拆解表 - 存储将剧本拆解成的分镜列表"""
    __tablename__ = "shot_breakdowns"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)  # 原始剧本内容
    shots = Column(String, nullable=False)   # 分镜列表，以JSON字符串格式存储

class DialogueExtract(Base):
    """对话提取表 - 存储从剧本中提取的对话内容"""
    __tablename__ = "dialogue_extracts"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)  # 原始剧本内容
    dialogues = Column(String, nullable=False)  # 提取的对话，以JSON字符串格式存储

class CharacterExtract(Base):
    """人物识别表 - 存储从剧本中识别出的人物信息"""
    __tablename__ = "character_extracts"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)  # 原始剧本内容
    characters = Column(String, nullable=False)  # 识别的人物信息，以JSON字符串格式存储

class CharacterImage(Base):
    """人物图片表 - 存储为每个人物生成的图片"""
    __tablename__ = "character_images"
    id = Column(Integer, primary_key=True, index=True)
    character_name = Column(String, nullable=False)  # 人物姓名
    character_info = Column(String, nullable=False)  # 人物详细信息，JSON格式
    image_url = Column(String, nullable=False)  # 生成的图片URL
    task_id = Column(String, nullable=False)  # 火山引擎任务ID
    status = Column(String, nullable=False)  # 生成状态：success/failed
    error_message = Column(String)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

class ShotImage(Base):
    """分镜图片表 - 存储为每个分镜生成的第一帧图片"""
    __tablename__ = "shot_images"
    id = Column(Integer, primary_key=True, index=True)
    shot_number = Column(Integer, nullable=False)  # 分镜编号
    shot_content = Column(String, nullable=False)  # 分镜内容描述
    style = Column(String, nullable=False)  # 使用的风格
    aspect_ratio = Column(String, nullable=False)  # 使用的比例
    image_url = Column(String, nullable=False)  # 生成的图片URL
    task_id = Column(String, nullable=False)  # 火山引擎任务ID
    status = Column(String, nullable=False)  # 生成状态：success/failed
    error_message = Column(String)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

class GeneratedVideo(Base):
    """生成的视频表 - 存储每个分镜生成的视频"""
    __tablename__ = "generated_videos"
    id = Column(Integer, primary_key=True, index=True)
    shot_number = Column(Integer, nullable=False)  # 分镜编号
    shot_content = Column(String, nullable=False)  # 分镜内容
    style = Column(String, nullable=False)  # 使用的风格
    aspect_ratio = Column(String, nullable=False)  # 使用的比例
    task_id = Column(String, nullable=False)  # 字节跳动任务ID
    video_url = Column(String, nullable=False)  # 生成的视频URL
    status = Column(String, nullable=False)  # 生成状态：success/failed
    error_message = Column(String)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 添加启动事件处理
# ==================== 应用生命周期事件 ====================
@app.on_event("startup")
async def on_startup():
    """应用启动时创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def on_shutdown():
    """应用关闭时的清理工作"""
    pass

# ==================== 认证API ====================
class SendCodeRequest(BaseModel):
    email: str

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    code: str

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

@app.post("/api/auth/send-code")
async def send_code(data: SendCodeRequest):
    code = f"{secrets.randbelow(1000000):06d}"
    expire_at = datetime.utcnow() + timedelta(minutes=10)
    async with async_session() as session:
        record = EmailVerification(email=data.email, code=code, expire_at=expire_at)
        session.add(record)
        await session.commit()
        return {"success": True, "message": "Verification code generated.", "code": code}

@app.post("/api/auth/register")
async def register(data: RegisterRequest):
    async with async_session() as session:
        # 校验验证码
        result = await session.execute(
            select(EmailVerification).where(
                EmailVerification.email == data.email
            ).order_by(EmailVerification.created_at.desc())
        )
        latest = result.scalars().first()
        if not latest or latest.code != data.code or latest.expire_at < datetime.utcnow():
            return {"success": False, "error": "Invalid or expired verification code"}

        # 检查重复
        exist = await session.execute(
            select(User).where((User.email == data.email) | (User.username == data.username))
        )
        if exist.scalars().first():
            return {"success": False, "error": "Email or username already exists"}

        user = User(
            email=data.email,
            username=data.username,
            password_hash=get_password_hash(data.password),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = create_access_token({"sub": user.username})
        return {"success": True, "token": token, "username": user.username}

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    async with async_session() as session:
        result = await session.execute(
            select(User).where((User.username == data.username_or_email) | (User.email == data.username_or_email))
        )
        user = result.scalars().first()
        if not user or not verify_password(data.password, user.password_hash) or not user.is_active:
            return TokenResponse(access_token="", token_type="bearer", username="")
        token = create_access_token({"sub": user.username})
        return TokenResponse(access_token=token, token_type="bearer", username=user.username)

# ==================== API密钥配置 ====================
DEEPSEEK_API_KEY = "sk-eef721b513bc408e9cd14d16e92e5091"  # DeepSeek AI API密钥
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API端点

# ==================== DeepSeek AI 功能函数 ====================

async def get_deepseek_script(prompt: str) -> str:
    """
    使用DeepSeek AI生成视频剧本
    
    Args:
        prompt (str): 用户输入的提示词
        
    Returns:
        str: AI生成的完整剧本内容
        
    Raises:
        Exception: 当API调用失败时抛出异常
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",  # Replace with your actual model name if needed
        "messages": [
            {"role": "system", "content": "You are a AI video script writer, you will be given a video prompt and you will need to generate a long video prompt that will be used for anouther ai to generate a video, this script may but not must contain the detail of the image, the background, the communication, ect.Just give the script, don't give any other text like of course or would you like to adjust."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        # Adjust this if DeepSeek's response format is different
        return result["choices"][0]["message"]["content"]

# ==================== 视频生成API端点 ====================

@app.post("/api/video/step1")
async def video_step1(data: Step1Request):
    """
    视频生成步骤1：接收用户提示词并生成AI剧本
    
    流程：
    1. 清空除了prompt以外的所有数据库表，确保全新的生成流程
    2. 保存用户输入的提示词到数据库
    3. 调用DeepSeek AI生成完整剧本
    4. 保存AI生成的剧本到数据库
    5. 返回生成结果
    
    Args:
        data (Step1Request): 包含用户提示词、风格、比例的请求数据
        
    Returns:
        dict: 包含成功状态、剧本内容、数据库ID等信息的响应
    """
    # 1. 清空除了prompt以外的所有数据库表
    async with async_session() as session:
        # 清空所有相关表，保留prompts表
        await session.execute(GeneratedVideo.__table__.delete())
        await session.execute(ShotImage.__table__.delete())
        await session.execute(CharacterImage.__table__.delete())
        await session.execute(CharacterExtract.__table__.delete())
        await session.execute(DialogueExtract.__table__.delete())
        await session.execute(ShotBreakdown.__table__.delete())
        await session.execute(AIScript.__table__.delete())
        await session.execute(AudioFile.__table__.delete())
        await session.commit()
        print("🧹 Cleared all database tables except prompts for new generation")

        # 2. 保存用户输入的提示词到数据库
        new_prompt = Prompt(
            prompt=data.prompt,
            style=data.style,
            aspect_ratio=data.aspect_ratio
        )
        session.add(new_prompt)
        await session.commit()
        await session.refresh(new_prompt)

        # 3. 调用DeepSeek AI生成完整剧本
        try:
            script = await get_deepseek_script(data.prompt)
        except Exception as e:
            return {"success": False, "error": f"DeepSeek AI error: {str(e)}"}

        # 4. 保存AI生成的剧本到数据库
        ai_script = AIScript(
            prompt_id=new_prompt.id,
            prompt=data.prompt,
            style=data.style,
            aspect_ratio=data.aspect_ratio,
            script=script
        )
        session.add(ai_script)
        await session.commit()
        await session.refresh(ai_script)

        # 5. 返回生成结果
        return {
            "success": True,
            "id": new_prompt.id,
            "data": data.dict(),
            "script": script,
            "ai_script_id": ai_script.id,
            "message": "All database tables cleared for new generation"
        }

@app.get("/api/video/ai-scripts")
async def list_ai_scripts():
    async with async_session() as session:
        result = await session.execute(select(AIScript))
        scripts = result.scalars().all()
        return [
            {
                "id": s.id,
                "prompt_id": s.prompt_id,
                "prompt": s.prompt,
                "style": s.style,
                "aspect_ratio": s.aspect_ratio,
                "script": s.script
            }
            for s in scripts
        ]

class BreakdownRequest(BaseModel):
    """分镜拆解请求模型 - 用于接收剧本拆解请求"""
    script: str  # 要拆解的剧本内容

async def get_deepseek_breakdown(script: str) -> dict:
    """
    使用DeepSeek AI将剧本拆解成分镜列表和对话列表
    
    Args:
        script (str): 完整的剧本内容
        
    Returns:
        dict: 包含分镜列表和对话列表的字典
            {
                "shots": [...],      # 分镜列表
                "dialogues": [...]   # 对话列表
            }
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content":
                "You are a professional video director and script analyst. "
                "You are given a script an you need to break it down into a list of shot-by-shot prompts. Each shot should contain the background, the action, the emotion. if there are dialoges involved inthe shot, just output someone said something. "
                "Return your answer in strict JSON format: {\"shots\": [...], \"dialogues\": [...]} . Do not add any extra explanation or text."
            },
            {"role": "user", "content": script}
        ],
        "temperature": 0.5
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        # 解析 JSON
        try:
            parsed = json.loads(content)
            shots = parsed.get("shots", [])
            dialogues = parsed.get("dialogues", [])
        except Exception:
            # fallback: 只拆分 shots
            shots = [s.strip("- ").strip() for s in content.strip().split("\n") if s.strip()]
            dialogues = []
        return {"shots": shots, "dialogues": dialogues}

@app.post("/api/video/breakdown")
async def breakdown_script(data: BreakdownRequest):
    try:
        result = await get_deepseek_breakdown(data.script)
        shots = result["shots"]
        dialogues = result["dialogues"]
        # 保存到数据库
        async with async_session() as session:
            breakdown = ShotBreakdown(
                script=data.script,
                shots=json.dumps(shots, ensure_ascii=False)
            )
            session.add(breakdown)
            await session.commit()
            await session.refresh(breakdown)
            return {
                "success": True,
                "shots": shots,
                "dialogues": dialogues,
                "breakdown_id": breakdown.id
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/video/shot-breakdowns")
async def list_shot_breakdowns():
    async with async_session() as session:
        result = await session.execute(select(ShotBreakdown))
        breakdowns = result.scalars().all()
        return [
            {
                "id": b.id,
                "script": b.script,
                "shots": json.loads(b.shots)
            }
            for b in breakdowns
        ] 

class BreakdownOnlyRequest(BaseModel):
    script: str

async def get_deepseek_breakdown_only(script: str) -> list:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content":
                "You are a professional video director. Given a full video script, break it down into a list of shot-by-shot prompts. Each shot must contain the background, the action, and the emotion(if there is any you must mention it). If there are dialogues involved in the shot, just output that someone is speaking. Output only the list, no extra text."
            },
            {"role": "user", "content": script}
        ],
        "temperature": 0.5
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        shots = [s.strip("- ").strip() for s in content.strip().split("\n") if s.strip()]
        return shots

@app.post("/api/video/breakdown-shots")
async def breakdown_shots(data: BreakdownOnlyRequest):
    try:
        shots = await get_deepseek_breakdown_only(data.script)
        # 保存到数据库
        async with async_session() as session:
            breakdown = ShotBreakdown(
                script=data.script,
                shots=json.dumps(shots, ensure_ascii=False)
            )
            session.add(breakdown)
            await session.commit()
            await session.refresh(breakdown)
            return {
                "success": True,
                "shots": shots,
                "breakdown_id": breakdown.id
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

class DialogueOnlyRequest(BaseModel):
    script: str

class CharacterOnlyRequest(BaseModel):
    script: str

class CharacterImageRequest(BaseModel):
    character_name: str
    character_info: dict

async def get_deepseek_dialogues_only(script: str) -> list:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content":
                "You are a professional script analyst. Given a full video script, extract all character dialogues and output them as a JSON array of strings, each item being a single line of dialogue (with the character's name if available). Output only the JSON array, no extra text, no markdown, no explanation, no code block, no line breaks between array elements."
            },
            {"role": "user", "content": script}
        ],
        "temperature": 0.5
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        # Remove markdown/code block if present
        if content.startswith("```") and content.endswith("```"):
            content = re.sub(r"^```[a-zA-Z]*", "", content)
            content = content.rstrip("`").strip()
        # Try to parse as JSON array
        try:
            dialogues = json.loads(content)
            # If it's a list of lines like ["[", "\"dialogue1\",", ... "]"], flatten it
            if (isinstance(dialogues, list) and
                len(dialogues) > 2 and
                dialogues[0] == "[" and
                dialogues[-1] == "]"):
                # Remove first and last, strip commas/quotes
                dialogues = [d.strip('", ') for d in dialogues[1:-1]]
        except Exception:
            # fallback: try to extract lines between [ and ]
            matches = re.findall(r'"(.*?)"', content)
            dialogues = matches if matches else []
        return dialogues

async def get_deepseek_characters_only(script: str) -> list:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content":
                "You are a professional script analyst. Given a full video script, identify all characters and extract their information. "
                "For each character, provide: name, gender, age range, appearance description, personality traits, and role in the story. "
                "Output as a JSON array of objects with the following structure: "
                "[{\"name\": \"character_name\", \"gender\": \"male/female/other\", \"age_range\": \"20s/30s/etc\", "
                "\"appearance\": \"detailed appearance description\", \"personality\": \"personality traits\", "
                "\"role\": \"main character/supporting character/etc\"}]. "
                "Output only the JSON array, no extra text, no markdown, no explanation."
            },
            {"role": "user", "content": script}
        ],
        "temperature": 0.3
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        
        # Remove markdown/code block if present
        if content.startswith("```") and content.endswith("```"):
            content = re.sub(r"^```[a-zA-Z]*", "", content)
            content = content.rstrip("`").strip()
        
        # Try to parse as JSON array
        try:
            characters = json.loads(content)
            if not isinstance(characters, list):
                characters = []
        except Exception as e:
            print(f"Error parsing characters JSON: {e}")
            print(f"Raw content: {content}")
            characters = []
        
        return characters

async def generate_shot_image(shot_number: int, shot_content: str, style: str = "Realistic", aspect_ratio: str = "16:9") -> dict:
    """为单个分镜生成第一帧图片 - 使用新的图生图API (i2i_portrait_photo)"""
    try:
        # 首先获取人物图片作为输入
        async with async_session() as session:
            # 获取最新的人物图片
            result = await session.execute(
                select(CharacterImage).where(CharacterImage.status == "success").order_by(CharacterImage.id.desc())
            )
            character_images = result.scalars().all()
            
            if not character_images:
                return {
                    "success": False,
                    "error": "没有找到可用的角色图片，请先生成角色图片"
                }
            
            # 选择第一个成功生成的人物图片作为输入
            input_image = character_images[0]
            input_image_url = input_image.image_url
            
            print(f"使用人物图片作为输入: {input_image.character_name}")
            print(f"输入图片URL: {input_image_url}")
        
        # 构建分镜图片提示词
        prompt = f"{shot_content}，{style}风格，{aspect_ratio}比例，高清图片，电影级画质，电影第一帧，专业摄影"
        
        print(f"生成分镜图片提示词: {prompt}")
        
        # 使用火山引擎官方SDK
        try:
            from volcengine.visual.VisualService import VisualService
            
            # 初始化视觉服务
            visual_service = VisualService()
            
            # 设置API密钥
            visual_service.set_ak(SHOT_IMAGE_ACCESS_KEY_ID)
            visual_service.set_sk(SHOT_IMAGE_SECRET_ACCESS_KEY)
            
            # 构建请求体 - 使用新的图生图API
            form = {
                "req_key": "i2i_portrait_photo",  # 新的图生图API
                "image_input": input_image_url,  # 输入图片URL
                "prompt": prompt,  # 分镜提示词
                "gpen": 0.4,  # 美颜参数
                "skin": 0.3,  # 皮肤参数
                "skin_unifi": 0,  # 皮肤统一参数
                "width": 1024,  # 图片宽度
                "height": 1024,  # 图片高度
                "gen_mode": "creative",  # 生成模式
                "seed": -1  # 随机种子
            }
            
            print(f"调用即梦API生成分镜第一帧图片: {shot_content[:50]}...")
            print(f"请求参数: {form}")
            
            # 提交任务
            submit_resp = visual_service.cv_submit_task(form)
            print(f"即梦API提交响应: {submit_resp}")
            
            # 检查resp是否为None
            if submit_resp is None:
                return {
                    "success": False,
                    "error": "API提交任务返回None",
                    "response": None
                }
            
            # 检查resp是否为字典
            if not isinstance(submit_resp, dict):
                return {
                    "success": False,
                    "error": f"API提交任务返回非字典类型: {type(submit_resp)}",
                    "response": submit_resp
                }
            
            # 检查响应状态
            if submit_resp.get("code") != 10000:
                error_msg = submit_resp.get('message', 'Unknown error')
                return {
                    "success": False,
                    "error": f"提交失败: {error_msg}",
                    "code": submit_resp.get("code")
                }
            
            # 获取任务ID
            task_id = submit_resp.get("data", {}).get("task_id")
            if not task_id:
                return {"success": False, "error": "未收到任务ID"}
            
            print(f"任务提交成功，任务ID: {task_id}")
            
            # 等待10秒后查询结果
            print("等待10秒后查询结果...")
            await asyncio.sleep(10)
            
            # 查询结果
            query_form = {
                "req_key": "i2i_portrait_photo",
                "task_id": task_id
            }
            
            # 轮询查询结果
            for i in range(30):  # 最多查30次
                result_resp = visual_service.cv_get_result(query_form)
                print(f"查询结果 {i+1}: {result_resp}")
                
                status = result_resp.get("data", {}).get("status")
                if status == "done" or status == 2:  # 成功
                    image_urls = result_resp.get("data", {}).get("image_urls", [])
                    if not image_urls or len(image_urls) == 0:
                        return {"success": False, "error": "未收到图片URL"}
                    
                    image_url = image_urls[0]  # 获取第一张图片的URL
                    break
                elif status == "failed" or status == 3:  # 失败
                    return {"success": False, "error": "图生图生成失败"}
                else:
                    # 还在生成中，等待5秒
                    print("图片生成中，等待5秒...")
                    await asyncio.sleep(5)
            else:
                return {"success": False, "error": "图生图生成超时"}
            
            return {
                "success": True,
                "image_url": image_url,
                "shot_number": shot_number,
                "shot_content": shot_content
            }
            
        except ImportError:
            print("火山引擎SDK未安装，尝试使用HTTP请求方式")
            # 如果SDK不可用，回退到HTTP请求方式
            return await generate_shot_image_http(shot_number, shot_content, style, aspect_ratio, prompt, input_image_url)
            
    except Exception as e:
        print(f"生成分镜图片错误: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_shot_image_http(shot_number: int, shot_content: str, style: str, aspect_ratio: str, prompt: str, input_image_url: str) -> dict:
    """使用HTTP请求方式生成分镜图片（备用方案）- 图生图"""
    try:
        # 使用正确的即梦API端点和认证方式
        api_url = "https://visual.volcengineapi.com?Action=CVProcess&Version=2022-08-31"
        
        # 构建请求数据 - 图生图
        data = {
            "req_key": "high_aes_general_v30l_zt2i",
            "prompt": prompt,
            "image_url": input_image_url,  # 输入图片URL
            "width": 1024,
            "height": 1024,
            "seed": -1,
            "scale": 2.5,
            "return_url": True,
            "logo_info": {
                "add_logo": False,
                "position": 0,
                "language": 0,
                "opacity": 0.3,
                "logo_text_content": ""
            }
        }
        
        # 使用正确的签名认证
        http_method = 'POST'
        canonical_uri = '/'
        canonical_querystring = 'Action=CVProcess&Version=2022-08-31'
        
        # 构建规范头部
        canonical_headers = 'content-type:application/json\nhost:visual.volcengineapi.com\nx-date:' + str(int(datetime.utcnow().timestamp())) + '\n'
        signed_headers = 'content-type;host;x-date'
        
        # 计算请求体哈希
        payload_hash = hashlib.sha256(json.dumps(data).encode('utf-8')).hexdigest()
        
        # 生成签名
        authorization_header, timestamp = generate_volc_signature(
            SHOT_IMAGE_ACCESS_KEY_ID, 
            SHOT_IMAGE_SECRET_ACCESS_KEY, 
            http_method, 
            canonical_uri, 
            canonical_querystring, 
            canonical_headers, 
            signed_headers, 
            payload_hash
        )
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Host": "visual.volcengineapi.com",
            "X-Date": timestamp,
            "Authorization": authorization_header
        }
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 10000:
                return {"success": False, "error": f"API错误: {result.get('message', 'Unknown error')}"}
            
            # 获取图片URL - 从image_urls数组中获取
            image_urls = result.get("data", {}).get("image_urls", [])
            if not image_urls or len(image_urls) == 0:
                return {"success": False, "error": "未收到图片URL"}
            
            image_url = image_urls[0]  # 获取第一张图片的URL
            
            return {
                "success": True,
                "image_url": image_url,
                "shot_number": shot_number,
                "shot_content": shot_content
            }
            
    except Exception as e:
        return {"success": False, "error": f"HTTP请求错误: {str(e)}"}

async def generate_character_image(character_name: str, character_info: dict) -> dict:
    """为单个人物生成白色背景图片"""
    try:
        # 构建文生图提示词
        gender = character_info.get('gender', '')
        age_range = character_info.get('age_range', '')
        appearance = character_info.get('appearance', '')
        personality = character_info.get('personality', '')
        
        # 性别中文转换
        gender_cn = '男性' if gender == 'male' else '女性' if gender == 'female' else '人物'
        
        # 年龄中文转换
        age_cn = age_range.replace('s', '多岁') if age_range else ''
        
        # 构建提示词
        prompt = f"一个{age_cn}的{gender_cn}，{appearance}，{personality}"
        
        print(f"生成人物图片提示词: {prompt}")
        
        # 使用火山引擎官方SDK
        try:
            from volcengine.visual.VisualService import VisualService
            
            # 初始化视觉服务
            visual_service = VisualService()
            
            # 设置API密钥
            visual_service.set_ak(JIMENG_ACCESS_KEY_ID)
            visual_service.set_sk(JIMENG_SECRET_ACCESS_KEY)
            
            # 构建请求体 - 专门用于生成白底人物照片
            form = {
                "req_key": "high_aes_general_v30l_zt2i",
                "prompt": f"{prompt}, 白色背景, 高清人像摄影, 正面角度, 自然表情, 专业人像, 全身像",
                "seed": -1,
                "scale": 2.5,
                "width": 1328,
                "height": 1328,
                "return_url": True,
                "logo_info": {
                    "add_logo": False,
                    "position": 0,
                    "language": 0,
                    "opacity": 0.3,
                    "logo_text_content": "这里是明水印内容"
                }
            }
            
            print(f"调用即梦API生成白底人物照片: {prompt}")
            print(f"请求参数: {form}")
            
            # 提交任务
            resp = visual_service.cv_process(form)
            print(f"即梦API响应: {resp}")
            
            # 检查resp是否为None
            if resp is None:
                return {
                    "success": False,
                    "error": "API提交任务返回None",
                    "response": None
                }
            
            # 检查resp是否为字典
            if not isinstance(resp, dict):
                return {
                    "success": False,
                    "error": f"API提交任务返回非字典类型: {type(resp)}",
                    "response": resp
                }
            
            # 检查响应状态
            if resp.get("code") != 10000:
                error_msg = resp.get('message', 'Unknown error')
                return {
                    "success": False,
                    "error": f"提交失败: {error_msg}",
                    "code": resp.get("code")
                }
            
            # 获取图片URL - 从image_urls数组中获取
            image_urls = resp.get("data", {}).get("image_urls", [])
            if not image_urls or len(image_urls) == 0:
                return {"success": False, "error": "未收到图片URL"}
            
            image_url = image_urls[0]  # 获取第一张图片的URL
            
            return {
                "success": True,
                "image_url": image_url,
                "character_name": character_name,
                "character_info": character_info
            }
            
        except ImportError:
            print("火山引擎SDK未安装，尝试使用HTTP请求方式")
            # 如果SDK不可用，回退到HTTP请求方式
            return await generate_character_image_http(character_name, character_info, prompt)
            
    except Exception as e:
        print(f"生成人物图片错误: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_character_image_http(character_name: str, character_info: dict, prompt: str) -> dict:
    """使用HTTP请求方式生成人物图片（备用方案）"""
    try:
        # 使用正确的即梦API端点和认证方式
        api_url = "https://visual.volcengineapi.com?Action=CVProcess&Version=2022-08-31"
        
        # 构建请求数据 - 根据火山引擎技术支持解决方案
        data = {
            "req_key": "jimeng_high_aes_general_v21_L",
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "seed": 42,
            "use_pre_llm": True,
            "use_sr": True,
            "req_json": "{\"logo_info\":{\"add_logo\":true,\"position\":0,\"language\":0,\"opacity\":0.3,\"logo_text_content\":\"这里是明水印内容\"},\"return_url\":true}"
        }
        
        # 使用正确的签名认证
        http_method = 'POST'
        canonical_uri = '/'
        canonical_querystring = 'Action=CVProcess&Version=2022-08-31'
        
        # 构建规范头部
        canonical_headers = 'content-type:application/json\nhost:visual.volcengineapi.com\nx-date:' + str(int(datetime.utcnow().timestamp())) + '\n'
        signed_headers = 'content-type;host;x-date'
        
        # 计算请求体哈希
        payload_hash = hashlib.sha256(json.dumps(data).encode('utf-8')).hexdigest()
        
        # 生成签名
        authorization_header, timestamp = generate_volc_signature(
            JIMENG_ACCESS_KEY_ID, 
            JIMENG_SECRET_ACCESS_KEY, 
            http_method, 
            canonical_uri, 
            canonical_querystring, 
            canonical_headers, 
            signed_headers, 
            payload_hash
        )
        
        headers = {
            "Authorization": authorization_header,
            "Content-Type": "application/json",
            "X-Date": timestamp,
            "Host": "visual.volcengineapi.com"
        }
        
        print(f"调用即梦API (HTTP): {api_url}")
        print(f"请求数据: {data}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=data,
                timeout=120,
                follow_redirects=True
            )
            
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应头: {dict(response.headers)}")
            
            content_type = response.headers.get('content-type', '')
            print(f"响应内容类型: {content_type}")
            
            if response.status_code == 200:
                if 'application/json' in content_type:
                    try:
                        result = response.json()
                        print(f"即梦API响应: {result}")
                        
                        if 'data' in result and 'image_urls' in result['data'] and result['data']['image_urls']:
                            image_url = result['data']['image_urls'][0]
                            request_id = result.get('request_id', '')
                            
                            return {
                                "success": True,
                                "image_url": image_url,
                                "task_id": request_id,
                                "prompt": prompt
                            }
                        else:
                            return {
                                "success": False,
                                "error": "API响应格式错误",
                                "response": result
                            }
                    except Exception as json_error:
                        print(f"JSON解析错误: {json_error}")
                        return {
                            "success": False,
                            "error": f"JSON解析失败: {json_error}",
                            "response": response.text[:200]
                        }
                else:
                    print(f"API返回HTML而不是JSON，响应内容: {response.text[:500]}...")
                    return {
                        "success": False,
                        "error": "API返回HTML页面，请检查端点和认证",
                        "response": response.text[:200]
                    }
            elif response.status_code == 400:
                try:
                    error_result = response.json()
                    print(f"API 400错误响应: {error_result}")
                    error_code = error_result.get('code', 'unknown')
                    error_message = error_result.get('message', 'unknown error')
                    return {
                        "success": False,
                        "error": f"API错误 {error_code}: {error_message}",
                        "response": error_result
                    }
                except Exception as json_error:
                    print(f"400错误JSON解析失败: {json_error}")
                    return {
                        "success": False,
                        "error": f"API调用失败: 400",
                        "response": response.text[:200]
                    }
            else:
                return {
                    "success": False,
                    "error": f"API调用失败: {response.status_code}",
                    "response": response.text
                }
                
    except Exception as e:
        print(f"HTTP方式生成人物图片错误: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_all_shot_images():
    """为所有分镜生成第一帧图片"""
    try:
        async with async_session() as session:
            # 获取最新的分镜数据
            result = await session.execute(
                select(ShotBreakdown).order_by(ShotBreakdown.id.desc()).limit(1)
            )
            shot_breakdown = result.scalar_one_or_none()
            
            if not shot_breakdown:
                return {"success": False, "error": "No shot breakdown found"}
            
            # 解析分镜数据
            shots = json.loads(shot_breakdown.shots)
            print(f"找到 {len(shots)} 个分镜需要生成第一帧图片")
            
            success_count = 0
            total_count = len(shots)
            
            # 为每个分镜生成图片
            for i, shot in enumerate(shots):
                shot_number = i + 1
                print(f"正在处理第 {shot_number}/{total_count} 个分镜: {shot[:50]}...")
                
                # 检查是否已经生成过
                existing_result = await session.execute(
                    select(ShotImage).where(
                        ShotImage.shot_number == shot_number,
                        ShotImage.status == "success"
                    ).order_by(ShotImage.id.desc()).limit(1)
                )
                existing_image = existing_result.scalar_one_or_none()
                
                if existing_image:
                    print(f"分镜 {shot_number} 已有第一帧图片，跳过生成")
                    success_count += 1
                    continue
                
                # 生成图片
                image_result = await generate_shot_image(shot_number, shot)
                
                # 保存到数据库
                shot_image = ShotImage(
                    shot_number=shot_number,
                    shot_content=shot,
                    style="Realistic",  # 默认风格
                    aspect_ratio="16:9",  # 默认比例
                    image_url=image_result.get("image_url", ""),
                    task_id="",  # 暂时为空
                    status="success" if image_result["success"] else "failed",
                    error_message=image_result.get("error", "") if not image_result["success"] else None
                )
                
                session.add(shot_image)
                await session.commit()
                
                if image_result["success"]:
                    success_count += 1
                    print(f"✅ 分镜 {shot_number} 第一帧图片生成成功")
                else:
                    print(f"❌ 分镜 {shot_number} 第一帧图片生成失败: {image_result.get('error', 'Unknown error')}")
                
                # 等待10秒再生成下一个
                if i < total_count - 1:
                    print("等待10秒后继续...")
                    await asyncio.sleep(10)
            
            print(f"所有分镜第一帧图片生成完成，成功: {success_count}/{total_count}")
            return {
                "success": True,
                "total_shots": total_count,
                "successful_shots": success_count,
                "failed_shots": total_count - success_count
            }
            
    except Exception as e:
        print(f"生成分镜图片错误: {str(e)}")
        return {"success": False, "error": f"Shot images generation error: {str(e)}"}

async def generate_all_character_images() -> dict:
    """为所有识别出的人物生成图片 - 顺序生成，每次一张，间隔5秒"""
    try:
        # 获取最新的人物识别结果
        async with async_session() as session:
            result = await session.execute(
                select(CharacterExtract).order_by(CharacterExtract.id.desc()).limit(1)
            )
            latest_extract = result.scalar_one_or_none()
            
            if not latest_extract:
                return {"success": False, "error": "没有找到人物识别结果"}
            
            characters = json.loads(latest_extract.characters)
            print(f"找到 {len(characters)} 个人物需要生成图片")
            
            results = []
            for i, character in enumerate(characters):
                character_name = character.get('name', '')
                print(f"正在处理第 {i+1}/{len(characters)} 个人物: {character_name}")
                
                # 检查是否已经生成过图片（只检查最新的成功记录）
                existing_result = await session.execute(
                    select(CharacterImage)
                    .where(CharacterImage.character_name == character_name)
                    .where(CharacterImage.status == 'success')
                    .order_by(CharacterImage.id.desc())
                    .limit(1)
                )
                existing_image = existing_result.scalar_one_or_none()
                
                if existing_image:
                    print(f"人物 {character_name} 已有成功图片，跳过生成")
                    results.append({
                        "character_name": character_name,
                        "status": "already_exists",
                        "image_url": existing_image.image_url
                    })
                    continue
                
                # 生成新图片 - 重试直到成功
                max_retries = 3
                retry_count = 0
                image_result = None
                
                while retry_count < max_retries:
                    try:
                        print(f"开始生成人物 {character_name} 的图片... (尝试 {retry_count + 1}/{max_retries})")
                        image_result = await generate_character_image(character_name, character)
                        
                        if image_result['success']:
                            print(f"人物 {character_name} 图片生成成功")
                            break
                        else:
                            print(f"人物 {character_name} 图片生成失败: {image_result.get('error', '未知错误')}")
                            retry_count += 1
                            if retry_count < max_retries:
                                print(f"等待5秒后重试...")
                                await asyncio.sleep(5)
                            
                    except Exception as e:
                        print(f"生成人物 {character_name} 图片时发生异常: {e}")
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"等待5秒后重试...")
                            await asyncio.sleep(5)
                
                # 保存到数据库
                if image_result and image_result['success']:
                    character_image = CharacterImage(
                        character_name=character_name,
                        character_info=json.dumps(character, ensure_ascii=False),
                        image_url=image_result.get('image_url', ''),
                        task_id=image_result.get('task_id', ''),
                        status='success',
                        error_message=''
                    )
                    
                    session.add(character_image)
                    await session.commit()
                    
                    results.append({
                        "character_name": character_name,
                        "status": "success",
                        "image_url": image_result.get('image_url', ''),
                        "error": ""
                    })
                else:
                    # 保存失败记录
                    character_image = CharacterImage(
                        character_name=character_name,
                        character_info=json.dumps(character, ensure_ascii=False),
                        image_url='',
                        task_id='',
                        status='failed',
                        error_message=image_result.get('error', '生成失败') if image_result else '未知错误'
                    )
                    
                    session.add(character_image)
                    await session.commit()
                    
                    results.append({
                        "character_name": character_name,
                        "status": "failed",
                        "image_url": "",
                        "error": image_result.get('error', '生成失败') if image_result else '未知错误'
                    })
                
                # 如果不是最后一个人物，等待5秒再处理下一个
                if i < len(characters) - 1:
                    print(f"等待5秒后处理下一个人物...")
                    await asyncio.sleep(5)
            
            print(f"所有人物图片生成完成，成功: {len([r for r in results if r['status'] == 'success'])}/{len(characters)}")
            return {
                "success": True,
                "results": results,
                "total_characters": len(characters)
            }
            
    except Exception as e:
        print(f"生成所有人物图片错误: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/video/characters")
async def extract_characters(data: CharacterOnlyRequest):
    try:
        characters = await get_deepseek_characters_only(data.script)
        
        # 保存到数据库
        async with async_session() as session:
            character_row = CharacterExtract(
                script=data.script,
                characters=json.dumps(characters, ensure_ascii=False)
            )
            session.add(character_row)
            await session.commit()
            await session.refresh(character_row)
            
            print('Characters from deepseek:', characters, type(characters))
            return {
                "success": True,
                "characters": characters,
                "character_id": character_row.id
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/video/character-extracts")
async def list_character_extracts():
    async with async_session() as session:
        result = await session.execute(select(CharacterExtract))
        extracts = result.scalars().all()
        return [
            {
                "id": c.id,
                "script": c.script,
                "characters": json.loads(c.characters)
            }
            for c in extracts
        ]

@app.post("/api/video/generate-character-images")
async def generate_character_images():
    """为所有识别出的人物生成白色背景图片"""
    try:
        result = await generate_all_character_images()
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/video/character-images")
async def list_character_images():
    """获取所有人物图片"""
    async with async_session() as session:
        result = await session.execute(select(CharacterImage))
        images = result.scalars().all()
        return [
            {
                "id": img.id,
                "character_name": img.character_name,
                "character_info": json.loads(img.character_info),
                "image_url": img.image_url,
                "task_id": img.task_id,
                "status": img.status,
                "error_message": img.error_message,
                "created_at": img.created_at.isoformat() if img.created_at else None
            }
            for img in images
        ]

@app.get("/api/video/character-images/latest")
async def get_latest_character_images():
    """获取最新的人物图片生成结果"""
    async with async_session() as session:
        # 获取最新的人物识别结果
        result = await session.execute(
            select(CharacterExtract).order_by(CharacterExtract.id.desc()).limit(1)
        )
        latest_extract = result.scalar_one_or_none()
        
        if not latest_extract:
            return {"success": False, "error": "没有找到人物识别结果"}
        
        characters = json.loads(latest_extract.characters)
        character_names = [char.get('name', '') for char in characters]
        
        # 获取每个人物的最新图片
        latest_images = []
        for character_name in character_names:
            result = await session.execute(
                select(CharacterImage)
                .where(CharacterImage.character_name == character_name)
                .order_by(CharacterImage.id.desc())
                .limit(1)
            )
            latest_image = result.scalar_one_or_none()
            
            if latest_image:
                latest_images.append({
                    "character_name": character_name,
                    "status": latest_image.status,
                    "image_url": latest_image.image_url,
                    "error_message": latest_image.error_message,
                    "created_at": latest_image.created_at.isoformat() if latest_image.created_at else None
                })
            else:
                latest_images.append({
                    "character_name": character_name,
                    "status": "not_started",
                    "image_url": "",
                    "error_message": "",
                    "created_at": None
                })
        
        return {
            "success": True,
            "characters": characters,
            "images": latest_images,
            "total_characters": len(characters),
            "completed": len([img for img in latest_images if img['status'] == 'success']),
        }







@app.post("/api/video/generate-shot-images")
async def generate_shot_images():
    """为所有分镜生成第一帧图片"""
    try:
        result = await generate_all_shot_images()
        
        # 如果生成成功，获取生成的图片列表
        if result.get("success"):
            # 获取生成的图片数据
            async with async_session() as session:
                result_query = await session.execute(select(ShotImage).order_by(ShotImage.shot_number))
                images = result_query.scalars().all()
                
                results = [
                    {
                        "shot_number": img.shot_number,
                        "shot_content": img.shot_content,
                        "status": img.status,
                        "image_url": img.image_url,
                        "error_message": img.error_message
                    }
                    for img in images
                ]
                
                return {
                    "success": True,
                    "results": results,
                    "total_shots": result.get("total_shots", 0),
                    "successful_shots": result.get("successful_shots", 0),
                    "failed_shots": result.get("failed_shots", 0)
                }
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/video/shot-images")
async def list_shot_images():
    """获取所有分镜图片"""
    async with async_session() as session:
        result = await session.execute(select(ShotImage).order_by(ShotImage.shot_number))
        images = result.scalars().all()
        return [
            {
                "id": img.id,
                "shot_number": img.shot_number,
                "shot_content": img.shot_content,
                "style": img.style,
                "aspect_ratio": img.aspect_ratio,
                "image_url": img.image_url,
                "task_id": img.task_id,
                "status": img.status,
                "error_message": img.error_message,
                "created_at": img.created_at.isoformat() if img.created_at else None
            }
            for img in images
        ]

@app.get("/api/video/shot-images/latest")
async def get_latest_shot_images():
    """获取最新的分镜图片生成结果"""
    async with async_session() as session:
        # 获取最新的分镜数据
        result = await session.execute(
            select(ShotBreakdown).order_by(ShotBreakdown.id.desc()).limit(1)
        )
        latest_breakdown = result.scalar_one_or_none()
        
        if not latest_breakdown:
            return {"success": False, "error": "没有找到分镜数据"}
        
        shots = json.loads(latest_breakdown.shots)
        total_shots = len(shots)
        
        # 获取每个分镜的最新图片
        latest_images = []
        for i, shot in enumerate(shots):
            shot_number = i + 1
            result = await session.execute(
                select(ShotImage)
                .where(ShotImage.shot_number == shot_number)
                .order_by(ShotImage.id.desc())
                .limit(1)
            )
            latest_image = result.scalar_one_or_none()
            
            if latest_image:
                latest_images.append({
                    "shot_number": shot_number,
                    "shot_content": shot,
                    "status": latest_image.status,
                    "image_url": latest_image.image_url,
                    "error_message": latest_image.error_message,
                    "created_at": latest_image.created_at.isoformat() if latest_image.created_at else None
                })
            else:
                latest_images.append({
                    "shot_number": shot_number,
                    "shot_content": shot,
                    "status": "not_started",
                    "image_url": "",
                    "error_message": "",
                    "created_at": None
                })
        
        return {
            "success": True,
            "shots": shots,
            "images": latest_images,
            "total_shots": total_shots,
            "completed": len([img for img in latest_images if img['status'] == 'success']),
            "failed": len([img for img in latest_images if img['status'] == 'failed']),
            "pending": len([img for img in latest_images if img['status'] == 'not_started'])
        }

@app.post("/api/video/generate-single-character-image")
async def generate_single_character_image(data: CharacterImageRequest):
    """为单个人物生成图片"""
    try:
        result = await generate_character_image(data.character_name, data.character_info)
        
        # 保存到数据库
        async with async_session() as session:
            character_image = CharacterImage(
                character_name=data.character_name,
                character_info=json.dumps(data.character_info, ensure_ascii=False),
                image_url=result.get('image_url', ''),
                task_id=result.get('task_id', ''),
                status='success' if result['success'] else 'failed',
                error_message=result.get('error', '')
            )
            session.add(character_image)
            await session.commit()
            await session.refresh(character_image)
            
            return {
                "success": result['success'],
                "character_image_id": character_image.id,
                "image_url": result.get('image_url', ''),
                "error": result.get('error', '')
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/video/character-images/{character_name}")
async def get_character_image(character_name: str):
    """获取特定人物的图片"""
    async with async_session() as session:
        result = await session.execute(
            select(CharacterImage).where(CharacterImage.character_name == character_name)
        )
        image = result.scalar_one_or_none()
        
        if image:
            return {
                "success": True,
                "character_name": image.character_name,
                "character_info": json.loads(image.character_info),
                "image_url": image.image_url,
                "status": image.status,
                "created_at": image.created_at.isoformat() if image.created_at else None
            }
        else:
            return {"success": False, "error": "未找到该人物的图片"}

@app.post("/api/video/dialogues")
async def extract_dialogues(data: DialogueOnlyRequest):
    try:
        dialogues = await get_deepseek_dialogues_only(data.script)
        # 保存到数据库
        if isinstance(dialogues, str):
            try:
                dialogues = json.loads(dialogues)
            except Exception:
                dialogues = []
        async with async_session() as session:
            dialogue_row = DialogueExtract(
                script=data.script,
                dialogues=json.dumps(dialogues, ensure_ascii=False)
            )
            session.add(dialogue_row)
            await session.commit()
            await session.refresh(dialogue_row)
            print('dialogues from deepseek:', dialogues, type(dialogues))
            return {
                "success": True,
                "dialogues": dialogues,
                "dialogue_id": dialogue_row.id
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/video/dialogue-extracts")
async def list_dialogue_extracts():
    async with async_session() as session:
        result = await session.execute(select(DialogueExtract))
        extracts = result.scalars().all()
        return [
            {
                "id": d.id,
                "script": d.script,
                "dialogues": json.loads(d.dialogues)
            }
            for d in extracts
        ] 

# ==================== 火山引擎API配置 ====================

# 字节跳动即梦AI API 配置 - 用于视频生成
BYTEDANCE_ACCESS_KEY_ID = "AKLTMTE0YWY5OTI3YThjNDNiMDlmNGRmNWY5YWY1Y2M5MDI"
BYTEDANCE_SECRET_ACCESS_KEY = "WlRobU9UaGlPREl6WlRNMk5HVmlZV0prWlRGa01tTXhOR1JsTURZNFpHRQ=="

# 即梦文生图API 配置 - 用于人物图片生成
JIMENG_ACCESS_KEY_ID = "AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU"
JIMENG_SECRET_ACCESS_KEY = "TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ=="

# 分镜图片生成API配置 - 用于分镜第一帧图片生成
SHOT_IMAGE_ACCESS_KEY_ID = "AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU"
SHOT_IMAGE_SECRET_ACCESS_KEY = "TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ=="



def generate_volc_signature(access_key_id, secret_access_key, http_method, canonical_uri, canonical_querystring, canonical_headers, signed_headers, payload_hash):
    """
    生成火山引擎API签名 - 基于AWS4签名算法
    
    这是火山引擎API认证的核心函数，用于生成请求签名。
    签名算法基于AWS4标准，确保API调用的安全性。
    
    Args:
        access_key_id (str): 访问密钥ID
        secret_access_key (str): 秘密访问密钥
        http_method (str): HTTP方法（GET, POST等）
        canonical_uri (str): 规范化的URI路径
        canonical_querystring (str): 规范化的查询字符串
        canonical_headers (str): 规范化的请求头
        signed_headers (str): 已签名的请求头列表
        payload_hash (str): 请求体的哈希值
        
    Returns:
        tuple: (authorization_header, timestamp)
            - authorization_header (str): 完整的授权头
            - timestamp (str): 时间戳
            
    Note:
        此函数实现了AWS4签名算法的完整流程：
        1. 创建规范请求
        2. 创建待签名字符串
        3. 计算签名密钥
        4. 生成最终签名
    """
    # 1. 创建规范请求 - 按照AWS4标准格式化请求
    canonical_request = http_method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
    
    # 2. 创建待签名字符串 - 包含算法、时间戳、凭证范围等
    algorithm = 'HMAC-SHA256'
    timestamp = str(int(datetime.utcnow().timestamp()))
    date = datetime.utcnow().strftime('%Y%m%d')
    credential_scope = date + '/cn-north-1/cv/aws4_request'  # 火山引擎的凭证范围
    
    string_to_sign = algorithm + '\n' + timestamp + '\n' + credential_scope + '\n' + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    
    # 3. 计算签名密钥 - 使用HMAC-SHA256算法生成签名密钥
    k_date = hmac.new(('AWS4' + secret_access_key).encode('utf-8'), date.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, 'cn-north-1'.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, 'cv'.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, 'aws4_request'.encode('utf-8'), hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 4. 创建授权头 - 组合所有签名信息
    authorization_header = algorithm + ' ' + 'Credential=' + access_key_id + '/' + credential_scope + ', ' + 'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
    
    return authorization_header, timestamp

# ==================== SDK导入和初始化 ====================

# 导入字节跳动火山引擎SDK
try:
    from volcengine.visual.VisualService import VisualService
    BYTEDANCE_AVAILABLE = True
    print("✅ 火山引擎SDK导入成功")
except ImportError:
    BYTEDANCE_AVAILABLE = False
    print("⚠️ 警告: 火山引擎SDK未安装，字节跳动AI功能将被禁用")
    print("请运行: pip install volcengine")

# ==================== 请求模型定义 ====================

class VideoGenerationRequest(BaseModel):
    """视频生成请求模型 - 用于接收视频生成请求"""
    shot: str  # 分镜内容描述
    style: str = "Realistic"  # 视频风格，默认为写实风格
    aspect_ratio: str = "16:9"  # 视频比例，默认为16:9

async def generate_bytedance_video_from_image(image_url: str, shot_content: str, style: str = "Realistic", aspect_ratio: str = "16:9"):
    """使用字节即梦AI基于图片生成视频 - 图生视频"""
    if not BYTEDANCE_AVAILABLE:
        return {"success": False, "error": "ByteDance SDK not available"}
    
    try:
        # 初始化字节AI服务
        vs = VisualService()
        vs.set_ak(BYTEDANCE_ACCESS_KEY_ID)
        vs.set_sk(BYTEDANCE_SECRET_ACCESS_KEY)
        vs.set_host("visual.volcengineapi.com")
        
        # 构建请求体 - 使用图生视频模型
        body = {
            "req_key": "jimeng_vgfm_i2v_l20",  # 图生视频模型
            "image_url": image_url,  # 输入图片URL
            "prompt": shot_content,  # 补充提示词
            "aspect_ratio": aspect_ratio
        }
        
        print(f"图生视频请求: {body}")
        
        # 提交任务
        submit_resp = vs.cv_sync2async_submit_task(body)
        print("ByteDance图生视频提交响应:", submit_resp)
        
        if submit_resp.get("code") != 10000:
            error_msg = submit_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"图生视频提交失败: {error_msg}", "code": submit_resp.get("code")}
        
        task_id = submit_resp.get("data", {}).get("task_id")
        if not task_id:
            return {"success": False, "error": "未收到task_id"}
        
        # 轮询查询结果
        for i in range(30):  # 最多查30次
            result = vs.cv_sync2async_get_result({
                "task_id": task_id,
                "req_key": "jimeng_vgfm_i2v_l20"
            })
            print(f"ByteDance图生视频查询 {i+1}:", result)
            
            status = result.get("data", {}).get("status")
            if status == "done" or status == 2:  # 成功
                video_url = result["data"].get("video_url")
                return {
                    "success": True,
                    "task_id": task_id,
                    "video_url": video_url,
                    "shot": shot_content,
                    "image_url": image_url
                }
            elif status == "failed" or status == 3:  # 失败
                return {"success": False, "error": "图生视频生成失败"}
            else:
                # 还在生成中，等待5秒
                await asyncio.sleep(5)
        
        return {"success": False, "error": "图生视频生成超时"}
        
    except Exception as e:
        error_str = str(e)
        # 检查是否是并发限制错误
        if "50430" in error_str or "Concurrent Limit" in error_str:
            return {"success": False, "error": f"并发限制: {error_str}", "code": 50430}
        else:
            return {"success": False, "error": f"图生视频API错误: {error_str}"}

async def generate_bytedance_video(shot: str, style: str = "Realistic", aspect_ratio: str = "16:9"):
    """使用字节即梦AI生成视频 - 基于文本提示词"""
    if not BYTEDANCE_AVAILABLE:
        return {"success": False, "error": "ByteDance SDK not available"}
    
    try:
        # 初始化字节AI服务
        vs = VisualService()
        vs.set_ak(BYTEDANCE_ACCESS_KEY_ID)
        vs.set_sk(BYTEDANCE_SECRET_ACCESS_KEY)
        vs.set_host("visual.volcengineapi.com")
        
        # 构建请求体
        body = {
            "req_key": "jimeng_vgfm_t2v_l20",
            "prompt": shot,
            "aspect_ratio": aspect_ratio
        }
        
        # 提交任务
        submit_resp = vs.cv_sync2async_submit_task(body)
        print("ByteDance submit response:", submit_resp)
        
        if submit_resp.get("code") != 10000:
            error_msg = submit_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"Submit failed: {error_msg}", "code": submit_resp.get("code")}
        
        task_id = submit_resp.get("data", {}).get("task_id")
        if not task_id:
            return {"success": False, "error": "No task_id received"}
        
        # 轮询查询结果
        import time
        for i in range(30):  # 最多查30次
            result = vs.cv_sync2async_get_result({
                "task_id": task_id,
                "req_key": "jimeng_vgfm_t2v_l20"
            })
            print(f"ByteDance query {i+1}:", result)
            
            status = result.get("data", {}).get("status")
            if status == "done" or status == 2:  # 成功
                video_url = result["data"].get("video_url")
                return {
                    "success": True,
                    "task_id": task_id,
                    "video_url": video_url,
                    "shot": shot
                }
            elif status == "failed" or status == 3:  # 失败
                return {"success": False, "error": "Video generation failed"}
            else:
                # 还在生成中，等待5秒
                await asyncio.sleep(5)
        
        return {"success": False, "error": "Generation timeout"}
        
    except Exception as e:
        error_str = str(e)
        # 检查是否是并发限制错误
        if "50430" in error_str or "Concurrent Limit" in error_str:
            return {"success": False, "error": f"Concurrent limit reached: {error_str}", "code": 50430}
        else:
            return {"success": False, "error": f"ByteDance API error: {error_str}"}



class ShotVideoGenerationRequest(BaseModel):
    shot_number: int
    style: str = "Realistic"
    aspect_ratio: str = "16:9"

class DigitalHumanVideoRequest(BaseModel):
    shot_number: int
    dialogue: str = ""  # 对话文本，如果不提供则使用分镜内容
    audio_url: str = ""  # 可选的自定义音频URL

@app.post("/api/video/generate-digital-human-video")
async def generate_digital_human_video_endpoint(data: DigitalHumanVideoRequest):
    """基于分镜图片和对话生成数字人视频"""
    try:
        async with async_session() as session:
            # 获取对应的分镜图片
            result = await session.execute(
                select(ShotImage).where(
                    ShotImage.shot_number == data.shot_number,
                    ShotImage.status == "success"
                ).order_by(ShotImage.id.desc()).limit(1)
            )
            shot_image = result.scalar_one_or_none()
            
            if not shot_image:
                return {"success": False, "error": f"分镜 {data.shot_number} 的图片未找到或生成失败"}
            
            print(f"基于分镜图片和对话生成数字人视频:")
            print(f"  分镜编号: {data.shot_number}")
            print(f"  图片URL: {shot_image.image_url}")
            print(f"  对话文本: {data.dialogue[:50] if data.dialogue else '使用分镜内容'}...")
            print(f"  分镜内容: {shot_image.shot_content[:50]}...")
            
            # 如果提供了自定义音频URL，使用原来的方法
            if data.audio_url:
                print(f"使用自定义音频URL: {data.audio_url}")
                result = await generate_digital_human_video(
                    shot_image.image_url,
                    data.audio_url,
                    shot_image.shot_content
                )
            else:
                # 使用新的方法，自动生成语音
                print("自动生成语音并创建数字人视频...")
                result = await generate_digital_human_video_with_dialogue(
                    shot_image.image_url,
                    shot_image.shot_content,
                    data.dialogue
                )
            
            print(f"数字人视频生成结果: {result}")
            
            if result["success"]:
                # 保存到数据库
                generated_video = GeneratedVideo(
                    shot_number=data.shot_number,
                    shot_content=shot_image.shot_content,
                    style="DigitalHuman",  # 标记为数字人视频
                    aspect_ratio="16:9",
                    task_id=result.get("task_id", ""),
                    video_url=result.get("video_url", ""),
                    status="success"
                )
                
                session.add(generated_video)
                await session.commit()
                
                return {
                    "success": True,
                    "shot_number": data.shot_number,
                    "video_url": result.get("video_url"),
                    "task_id": result.get("task_id"),
                    "resource_id": result.get("resource_id"),
                    "image_url": shot_image.image_url,
                    "audio_url": result.get("audio_url", ""),
                    "audio_filename": result.get("audio_filename", ""),
                    "dialogue": result.get("dialogue", "")
                }
            else:
                # 保存失败记录
                generated_video = GeneratedVideo(
                    shot_number=data.shot_number,
                    shot_content=shot_image.shot_content,
                    style="DigitalHuman",
                    aspect_ratio="16:9",
                    task_id="",
                    video_url="",
                    status="failed",
                    error_message=result.get("error", "Unknown error")
                )
                
                session.add(generated_video)
                await session.commit()
                
                return {"success": False, "error": result.get("error", "Unknown error")}
                
    except Exception as e:
        print(f"生成数字人视频错误: {str(e)}")
        return {"success": False, "error": f"Digital human video generation error: {str(e)}"}

class DialogueDigitalHumanRequest(BaseModel):
    shot_number: int
    dialogue: str  # 对话文本

@app.post("/api/video/generate-dialogue-digital-human")
async def generate_dialogue_digital_human(data: DialogueDigitalHumanRequest):
    """为指定对话生成数字人视频"""
    try:
        async with async_session() as session:
            # 获取对应的分镜图片
            result = await session.execute(
                select(ShotImage).where(
                    ShotImage.shot_number == data.shot_number,
                    ShotImage.status == "success"
                ).order_by(ShotImage.id.desc()).limit(1)
            )
            shot_image = result.scalar_one_or_none()
            
            if not shot_image:
                return {"success": False, "error": f"分镜 {data.shot_number} 的图片未找到或生成失败"}
            
            print(f"为对话生成数字人视频:")
            print(f"  分镜编号: {data.shot_number}")
            print(f"  对话文本: {data.dialogue}")
            print(f"  图片URL: {shot_image.image_url}")
            
            # 使用新的方法，自动生成语音
            result = await generate_digital_human_video_with_dialogue(
                shot_image.image_url,
                shot_image.shot_content,
                data.dialogue
            )
            
            print(f"数字人视频生成结果: {result}")
            
            if result["success"]:
                # 保存到数据库
                generated_video = GeneratedVideo(
                    shot_number=data.shot_number,
                    shot_content=shot_image.shot_content,
                    style="DigitalHuman",
                    aspect_ratio="16:9",
                    task_id=result.get("task_id", ""),
                    video_url=result.get("video_url", ""),
                    status="success"
                )
                
                session.add(generated_video)
                await session.commit()
                
                return {
                    "success": True,
                    "shot_number": data.shot_number,
                    "dialogue": data.dialogue,
                    "video_url": result.get("video_url"),
                    "task_id": result.get("task_id"),
                    "resource_id": result.get("resource_id"),
                    "image_url": shot_image.image_url,
                    "audio_url": result.get("audio_url", ""),
                    "audio_filename": result.get("audio_filename", "")
                }
            else:
                # 保存失败记录
                generated_video = GeneratedVideo(
                    shot_number=data.shot_number,
                    shot_content=shot_image.shot_content,
                    style="DigitalHuman",
                    aspect_ratio="16:9",
                    task_id="",
                    video_url="",
                    status="failed",
                    error_message=result.get("error", "Unknown error")
                )
                
                session.add(generated_video)
                await session.commit()
                
                return {"success": False, "error": result.get("error", "Unknown error")}
                
    except Exception as e:
        print(f"生成对话数字人视频错误: {str(e)}")
        return {"success": False, "error": f"Dialogue digital human generation error: {str(e)}"}

@app.post("/api/video/generate-all-dialogues-digital-human")
async def generate_all_dialogues_digital_human():
    """为所有分镜生成数字人视频 - 每个分镜都生成一个数字人视频"""
    try:
        async with async_session() as session:
            # 获取所有成功的分镜图片
            shot_result = await session.execute(
                select(ShotImage).where(ShotImage.status == "success").order_by(ShotImage.shot_number)
            )
            shot_images = shot_result.scalars().all()
            
            if not shot_images:
                return {"success": False, "error": "没有找到成功的分镜图片"}
            
            print(f"找到 {len(shot_images)} 个分镜图片需要生成数字人视频")
            
            success_count = 0
            total_count = len(shot_images)
            
            # 为每个分镜生成数字人视频
            for i, shot_image in enumerate(shot_images):
                print(f"正在处理第 {i+1}/{total_count} 个分镜数字人视频:")
                print(f"  分镜编号: {shot_image.shot_number}")
                print(f"  分镜内容: {shot_image.shot_content[:50]}...")
                
                # 检查是否已经生成过
                existing_result = await session.execute(
                    select(GeneratedVideo).where(
                        GeneratedVideo.shot_number == shot_image.shot_number,
                        GeneratedVideo.style == "DigitalHuman",
                        GeneratedVideo.status == "success"
                    ).order_by(GeneratedVideo.id.desc()).limit(1)
                )
                existing_video = existing_result.scalar_one_or_none()
                
                if existing_video:
                    print(f"分镜 {shot_image.shot_number} 已有数字人视频，跳过生成")
                    success_count += 1
                    continue
                
                # 生成数字人视频 - 使用分镜内容作为对话，如果没有对话就使用空白
                video_result = await generate_digital_human_video_with_dialogue(
                    shot_image.image_url,
                    shot_image.shot_content,
                    ""  # 使用空白对话，让函数使用分镜内容
                )
                
                # 保存到数据库
                generated_video = GeneratedVideo(
                    shot_number=shot_image.shot_number,
                    shot_content=shot_image.shot_content,
                    style="DigitalHuman",
                    aspect_ratio="16:9",
                    task_id=video_result.get("task_id", ""),
                    video_url=video_result.get("video_url", ""),
                    status="success" if video_result["success"] else "failed",
                    error_message=video_result.get("error", "") if not video_result["success"] else None
                )
                
                session.add(generated_video)
                await session.commit()
                
                if video_result["success"]:
                    success_count += 1
                    print(f"✅ 分镜 {shot_image.shot_number} 数字人视频生成成功")
                    print(f"   音频文件: {video_result.get('audio_filename', 'N/A')}")
                else:
                    print(f"❌ 分镜 {shot_image.shot_number} 数字人视频生成失败: {video_result.get('error', 'Unknown error')}")
                
                # 等待3秒再生成下一个
                if i < total_count - 1:
                    print("等待3秒后继续...")
                    await asyncio.sleep(3)
            
            print(f"所有分镜数字人视频生成完成，成功: {success_count}/{total_count}")
            return {
                "success": True,
                "total_shots": total_count,
                "successful_videos": success_count,
                "failed_videos": total_count - success_count
            }
            
    except Exception as e:
        print(f"生成数字人视频错误: {str(e)}")
        return {"success": False, "error": f"All digital human generation error: {str(e)}"}

@app.post("/api/video/generate-all-digital-human-videos")
async def generate_all_digital_human_videos():
    """为所有分镜生成数字人视频 - 自动生成语音"""
    try:
        async with async_session() as session:
            # 获取所有成功的分镜图片
            result = await session.execute(
                select(ShotImage).where(ShotImage.status == "success").order_by(ShotImage.shot_number)
            )
            shot_images = result.scalars().all()
            
            if not shot_images:
                return {"success": False, "error": "没有找到成功的分镜图片，请先生成分镜图片"}
            
            print(f"找到 {len(shot_images)} 个分镜图片需要生成数字人视频")
            
            success_count = 0
            total_count = len(shot_images)
            
            # 为每个分镜生成数字人视频
            for i, shot_image in enumerate(shot_images):
                print(f"正在处理第 {i+1}/{total_count} 个分镜数字人视频: {shot_image.shot_number}")
                
                # 检查是否已经生成过
                existing_result = await session.execute(
                    select(GeneratedVideo).where(
                        GeneratedVideo.shot_number == shot_image.shot_number,
                        GeneratedVideo.style == "DigitalHuman",
                        GeneratedVideo.status == "success"
                    ).order_by(GeneratedVideo.id.desc()).limit(1)
                )
                existing_video = existing_result.scalar_one_or_none()
                
                if existing_video:
                    print(f"分镜 {shot_image.shot_number} 已有数字人视频，跳过生成")
                    success_count += 1
                    continue
                
                # 使用新的方法，自动生成语音
                print(f"为分镜 {shot_image.shot_number} 自动生成语音并创建数字人视频...")
                video_result = await generate_digital_human_video_with_dialogue(
                    shot_image.image_url,
                    shot_image.shot_content,
                    ""  # 使用分镜内容作为对话
                )
                
                # 保存到数据库
                generated_video = GeneratedVideo(
                    shot_number=shot_image.shot_number,
                    shot_content=shot_image.shot_content,
                    style="DigitalHuman",
                    aspect_ratio="16:9",
                    task_id=video_result.get("task_id", ""),
                    video_url=video_result.get("video_url", ""),
                    status="success" if video_result["success"] else "failed",
                    error_message=video_result.get("error", "") if not video_result["success"] else None
                )
                
                session.add(generated_video)
                await session.commit()
                
                if video_result["success"]:
                    success_count += 1
                    print(f"✅ 分镜 {shot_image.shot_number} 数字人视频生成成功")
                    print(f"   音频文件: {video_result.get('audio_filename', 'N/A')}")
                else:
                    print(f"❌ 分镜 {shot_image.shot_number} 数字人视频生成失败: {video_result.get('error', 'Unknown error')}")
                
                # 等待15秒再生成下一个（数字人视频生成需要更多时间）
                if i < total_count - 1:
                    print("等待15秒后继续...")
                    await asyncio.sleep(15)
            
            print(f"所有分镜数字人视频生成完成，成功: {success_count}/{total_count}")
            return {
                "success": True,
                "total_shots": total_count,
                "successful_videos": success_count,
                "failed_videos": total_count - success_count
            }
            
    except Exception as e:
        print(f"生成数字人视频错误: {str(e)}")
        return {"success": False, "error": f"All digital human videos generation error: {str(e)}"}

@app.post("/api/video/generate-shot-video")
async def generate_shot_video(data: ShotVideoGenerationRequest):
    """基于分镜图片生成视频"""
    try:
        async with async_session() as session:
            # 获取对应的分镜图片
            result = await session.execute(
                select(ShotImage).where(
                    ShotImage.shot_number == data.shot_number,
                    ShotImage.status == "success"
                ).order_by(ShotImage.id.desc()).limit(1)
            )
            shot_image = result.scalar_one_or_none()
            
            if not shot_image:
                return {"success": False, "error": f"分镜 {data.shot_number} 的图片未找到或生成失败"}
            
            print(f"基于分镜图片生成视频:")
            print(f"  分镜编号: {data.shot_number}")
            print(f"  图片URL: {shot_image.image_url}")
            print(f"  分镜内容: {shot_image.shot_content[:50]}...")
            print(f"  风格: {data.style}")
            print(f"  比例: {data.aspect_ratio}")
            
            # 调用图生视频API
            result = await generate_bytedance_video_from_image(
                shot_image.image_url,
                shot_image.shot_content,
                data.style,
                data.aspect_ratio
            )
            
            print(f"图生视频结果: {result}")
            
            if result["success"]:
                # 保存到数据库
                generated_video = GeneratedVideo(
                    shot_number=data.shot_number,
                    shot_content=shot_image.shot_content,
                    style=data.style,
                    aspect_ratio=data.aspect_ratio,
                    task_id=result.get("task_id", ""),
                    video_url=result.get("video_url", ""),
                    status="success"
                )
                
                session.add(generated_video)
                await session.commit()
                
                return {
                    "success": True,
                    "shot_number": data.shot_number,
                    "video_url": result.get("video_url"),
                    "task_id": result.get("task_id"),
                    "image_url": shot_image.image_url
                }
            else:
                # 保存失败记录
                generated_video = GeneratedVideo(
                    shot_number=data.shot_number,
                    shot_content=shot_image.shot_content,
                    style=data.style,
                    aspect_ratio=data.aspect_ratio,
                    task_id="",
                    video_url="",
                    status="failed",
                    error_message=result.get("error", "Unknown error")
                )
                
                session.add(generated_video)
                await session.commit()
                
                return {"success": False, "error": result.get("error", "Unknown error")}
                
    except Exception as e:
        print(f"生成分镜视频错误: {str(e)}")
        return {"success": False, "error": f"Shot video generation error: {str(e)}"}

@app.post("/api/video/generate-video")
async def generate_video(data: VideoGenerationRequest):
    """生成单个分镜的视频 - 基于文本提示词"""
    try:
        # 获取用户选择的风格和比例
        style = data.style
        aspect_ratio = data.aspect_ratio
        shot = data.shot
        
        print(f"Received video generation request:")
        print(f"  Shot: {shot[:50]}...")
        print(f"  Style: {style}")
        print(f"  Aspect Ratio: {aspect_ratio}")
        
        # 调用字节AI生成视频
        result = await generate_bytedance_video(shot, style, aspect_ratio)
        
        print(f"ByteDance result: {result}")
        
        # 保存到数据库
        async with async_session() as session:
            # 获取当前最大的shot_number，用于确定新分镜的编号
            result_query = await session.execute(select(GeneratedVideo.shot_number))
            existing_numbers = result_query.scalars().all()
            shot_number = max(existing_numbers) + 1 if existing_numbers else 1
            
            # 创建新的GeneratedVideo记录
            generated_video = GeneratedVideo(
                shot_number=shot_number,
                shot_content=shot,
                style=style,
                aspect_ratio=aspect_ratio,
                task_id=result.get("task_id", ""),
                video_url=result.get("video_url", ""),
                status="success" if result.get("success") else "failed",
                error_message=result.get("error", "") if not result.get("success") else None
            )
            
            session.add(generated_video)
            await session.commit()
            await session.refresh(generated_video)
            
            print(f"Saved to database with ID: {generated_video.id}")
        
        return result
        
    except Exception as e:
        print(f"Video generation error: {str(e)}")
        
        # 即使出错也要保存到数据库
        try:
            async with async_session() as session:
                result_query = await session.execute(select(GeneratedVideo.shot_number))
                existing_numbers = result_query.scalars().all()
                shot_number = max(existing_numbers) + 1 if existing_numbers else 1
                
                generated_video = GeneratedVideo(
                    shot_number=shot_number,
                    shot_content=shot,
                    style=style,
                    aspect_ratio=aspect_ratio,
                    task_id="",
                    video_url="",
                    status="failed",
                    error_message=str(e)
                )
                
                session.add(generated_video)
                await session.commit()
                print(f"Saved error to database with ID: {generated_video.id}")
        except Exception as db_error:
            print(f"Database save error: {str(db_error)}")
        
        return {"success": False, "error": f"Video generation error: {str(e)}"}



@app.post("/api/video/generate-all-shot-videos")
async def generate_all_shot_videos():
    """为所有分镜生成视频 - 基于分镜第一帧图片生成"""
    try:
        async with async_session() as session:
            # 获取所有成功的分镜图片
            result = await session.execute(
                select(ShotImage).where(ShotImage.status == "success").order_by(ShotImage.shot_number)
            )
            shot_images = result.scalars().all()
            
            if not shot_images:
                return {"success": False, "error": "没有找到成功的分镜图片，请先生成分镜图片"}
            
            print(f"找到 {len(shot_images)} 个分镜图片需要生成视频")
            
            success_count = 0
            total_count = len(shot_images)
            
            # 为每个分镜生成视频
            for i, shot_image in enumerate(shot_images):
                print(f"正在处理第 {i+1}/{total_count} 个分镜视频: {shot_image.shot_number}")
                
                # 检查是否已经生成过
                existing_result = await session.execute(
                    select(GeneratedVideo).where(
                        GeneratedVideo.shot_number == shot_image.shot_number,
                        GeneratedVideo.status == "success"
                    ).order_by(GeneratedVideo.id.desc()).limit(1)
                )
                existing_video = existing_result.scalar_one_or_none()
                
                if existing_video:
                    print(f"分镜 {shot_image.shot_number} 已有视频，跳过生成")
                    success_count += 1
                    continue
                
                # 基于分镜图片生成视频
                video_result = await generate_bytedance_video_from_image(
                    shot_image.image_url,
                    shot_image.shot_content,
                    shot_image.style,
                    shot_image.aspect_ratio
                )
                
                # 保存到数据库
                generated_video = GeneratedVideo(
                    shot_number=shot_image.shot_number,
                    shot_content=shot_image.shot_content,
                    style=shot_image.style,
                    aspect_ratio=shot_image.aspect_ratio,
                    task_id=video_result.get("task_id", ""),
                    video_url=video_result.get("video_url", ""),
                    status="success" if video_result["success"] else "failed",
                    error_message=video_result.get("error", "") if not video_result["success"] else None
                )
                
                session.add(generated_video)
                await session.commit()
                
                if video_result["success"]:
                    success_count += 1
                    print(f"✅ 分镜 {shot_image.shot_number} 视频生成成功")
                else:
                    print(f"❌ 分镜 {shot_image.shot_number} 视频生成失败: {video_result.get('error', 'Unknown error')}")
                
                # 等待5秒再生成下一个
                if i < total_count - 1:
                    print("等待5秒后继续...")
                    await asyncio.sleep(5)
            
            print(f"所有分镜视频生成完成，成功: {success_count}/{total_count}")
            return {
                "success": True,
                "total_shots": total_count,
                "successful_videos": success_count,
                "failed_videos": total_count - success_count
            }
            
    except Exception as e:
        print(f"生成分镜视频错误: {str(e)}")
        return {"success": False, "error": f"All shot videos generation error: {str(e)}"}

@app.get("/api/video/generated-videos")
async def list_generated_videos():
    """获取所有生成的视频列表"""
    async with async_session() as session:
        result = await session.execute(select(GeneratedVideo).order_by(GeneratedVideo.created_at.desc()))
        videos = result.scalars().all()
        return [
            {
                "id": v.id,
                "shot_number": v.shot_number,
                "shot_content": v.shot_content,
                "style": v.style,
                "aspect_ratio": v.aspect_ratio,
                "task_id": v.task_id,
                "video_url": v.video_url,
                "status": v.status,
                "error_message": v.error_message,
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in videos
        ]

@app.delete("/api/video/generated-videos/{video_id}")
async def delete_generated_video(video_id: int):
    """删除指定的生成视频记录"""
    async with async_session() as session:
        result = await session.execute(select(GeneratedVideo).where(GeneratedVideo.id == video_id))
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        await session.delete(video)
        await session.commit()
        
        return {"success": True, "message": "Video deleted successfully"}

@app.delete("/api/video/generated-videos")
async def clear_all_generated_videos():
    """清空所有生成的视频记录"""
    async with async_session() as session:
        await session.execute(GeneratedVideo.__table__.delete())
        await session.commit()
        
        return {"success": True, "message": "All videos cleared successfully"}

@app.post("/api/video/clear-current-session")
async def clear_current_session():
    """清空当前会话的视频数据（保留其他数据）"""
    async with async_session() as session:
        # 只清空generated_videos表，保留其他数据
        await session.execute(GeneratedVideo.__table__.delete())
        await session.commit()
        
        return {
            "success": True, 
            "message": "Current session videos cleared successfully",
            "cleared_tables": ["generated_videos"]
        }

@app.post("/api/video/combine-videos")
async def combine_videos():
    """将所有成功的视频合并成一个完整视频"""
    try:
        async with async_session() as session:
            # 获取所有成功的视频，按shot_number排序
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 构建合并后的视频信息
            combined_video = {
                "success": True,
                "total_shots": len(videos),
                "videos": [
                    {
                        "shot_number": v.shot_number,
                        "shot_content": v.shot_content,
                        "video_url": v.video_url,
                        "style": v.style,
                        "aspect_ratio": v.aspect_ratio,
                        "duration": 5  # ByteDance生成的视频通常是5秒
                    }
                    for v in videos
                ],
                "total_duration": len(videos) * 5,  # 总时长（秒）
                "message": f"Successfully combined {len(videos)} video shots"
            }
            
            return combined_video
            
    except Exception as e:
        print(f"Combine videos error: {str(e)}")
        return {"success": False, "error": f"Combine videos error: {str(e)}"}

@app.get("/api/video/combine-status")
async def get_combine_status():
    """获取视频合并状态"""
    try:
        async with async_session() as session:
            # 获取统计信息
            total_result = await session.execute(select(GeneratedVideo))
            total_videos = len(total_result.scalars().all())
            
            success_result = await session.execute(
                select(GeneratedVideo).where(GeneratedVideo.status == "success")
            )
            success_videos = len(success_result.scalars().all())
            
            failed_result = await session.execute(
                select(GeneratedVideo).where(GeneratedVideo.status == "failed")
            )
            failed_videos = len(failed_result.scalars().all())
            
            return {
                "success": True,
                "total_videos": total_videos,
                "success_videos": success_videos,
                "failed_videos": failed_videos,
                "can_combine": success_videos > 0,
                "estimated_duration": success_videos * 5  # 每个视频5秒
            }
            
    except Exception as e:
        return {"success": False, "error": f"Status check error: {str(e)}"}

@app.get("/api/video/test-url/{video_id}")
async def test_video_url(video_id: int):
    """测试视频URL是否可访问"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(GeneratedVideo).where(GeneratedVideo.id == video_id)
            )
            video = result.scalar_one_or_none()
            
            if not video:
                return {"success": False, "error": "Video not found"}
            
            # 测试URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            
            response = requests.head(video.video_url, headers=headers, timeout=10)
            
            return {
                "success": True,
                "video_id": video_id,
                "shot_number": video.shot_number,
                "url": video.video_url,
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', 'Unknown'),
                "content_length": response.headers.get('Content-Length', 'Unknown'),
                "accessible": response.status_code == 200
            }
            
    except Exception as e:
        return {"success": False, "error": f"Test failed: {str(e)}"}

async def download_video(url: str, filename: str) -> str:
    """下载视频到临时文件"""
    try:
        print(f"Attempting to download: {url}")
        
        # 添加请求头，模拟浏览器请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://visual.volcengineapi.com/',  # 或者你实际访问的页面
        }
        
        response = requests.get(url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
        
        # 创建临时文件
        temp_dir = Path(tempfile.gettempdir()) / "aiva_videos"
        temp_dir.mkdir(exist_ok=True)
        
        file_path = temp_dir / filename
        
        # 检查文件大小
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded_size = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"Download progress: {progress:.1f}%")
        
        # 验证文件是否下载成功
        if file_path.exists() and file_path.stat().st_size > 0:
            print(f"Successfully downloaded: {filename} ({file_path.stat().st_size} bytes)")
            return str(file_path)
        else:
            raise Exception("Downloaded file is empty or doesn't exist")
            
    except Exception as e:
        print(f"Error downloading video {url}: {str(e)}")
        # 如果文件存在但下载失败，删除它
        temp_dir = Path(tempfile.gettempdir()) / "aiva_videos"
        file_path = temp_dir / filename
        if file_path.exists():
            file_path.unlink()
        raise

@app.post("/api/video/download-combined")
async def download_combined_video():
    """下载合并后的完整视频"""
    try:
        async with async_session() as session:
            # 获取所有成功的视频，按shot_number排序
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 创建临时目录
            temp_dir = Path(tempfile.gettempdir()) / "aiva_videos"
            temp_dir.mkdir(exist_ok=True)
            
            # 下载所有视频
            downloaded_files = []
            for i, video in enumerate(videos):
                try:
                    print(f"\n--- Downloading video {video.shot_number} ---")
                    print(f"URL: {video.video_url}")
                    print(f"Style: {video.style}")
                    print(f"Aspect Ratio: {video.aspect_ratio}")
                    
                    filename = f"shot_{video.shot_number:02d}.mp4"
                    file_path = await download_video(video.video_url, filename)
                    downloaded_files.append(file_path)
                    print(f"✅ Successfully downloaded: {filename}")
                except Exception as e:
                    error_msg = f"Failed to download video {video.shot_number}: {str(e)}"
                    print(f"❌ {error_msg}")
                    print(f"Video URL: {video.video_url}")
                    return {"success": False, "error": error_msg}
            
            # 创建合并后的视频信息
            combined_info = {
                "success": True,
                "total_shots": len(videos),
                "total_duration": len(videos) * 5,  # 每个视频5秒
                "downloaded_files": downloaded_files,
                "message": f"Successfully downloaded {len(videos)} video shots",
                "download_links": [
                    {
                        "shot_number": video.shot_number,
                        "video_url": video.video_url,
                        "local_file": downloaded_files[i]
                    }
                    for i, video in enumerate(videos)
                ]
            }
            
            return combined_info
            
    except Exception as e:
        print(f"Download combined video error: {str(e)}")
        return {"success": False, "error": f"Download error: {str(e)}"}

@app.get("/api/video/download-status")
async def get_download_status():
    """获取下载状态"""
    try:
        temp_dir = Path(tempfile.gettempdir()) / "aiva_videos"
        if temp_dir.exists():
            files = list(temp_dir.glob("*.mp4"))
            return {
                "success": True,
                "downloaded_files": len(files),
                "files": [f.name for f in files]
            }
        else:
            return {
                "success": True,
                "downloaded_files": 0,
                "files": []
            }
    except Exception as e:
        return {"success": False, "error": f"Status check error: {str(e)}"} 

@app.get("/api/video/download-urls")
async def get_video_download_urls():
    """获取所有成功视频的下载链接，用于手动下载"""
    try:
        async with async_session() as session:
            # 获取所有成功的视频，按shot_number排序
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 构建下载链接列表
            download_links = []
            for video in videos:
                download_links.append({
                    "shot_number": video.shot_number,
                    "shot_content": video.shot_content[:100] + "..." if len(video.shot_content) > 100 else video.shot_content,
                    "video_url": video.video_url,
                    "style": video.style,
                    "aspect_ratio": video.aspect_ratio,
                    "duration": 5  # ByteDance生成的视频通常是5秒
                })
            
            return {
                "success": True,
                "total_shots": len(videos),
                "total_duration": len(videos) * 5,
                "message": f"Found {len(videos)} video shots for manual download",
                "download_links": download_links,
                "instructions": [
                    "1. Click each video URL to download the individual video files",
                    "2. Use a video editing software (like FFmpeg, Adobe Premiere, etc.) to combine them",
                    "3. Or use online video combiners like:",
                    "   - https://www.onlinevideoconverter.com/",
                    "   - https://www.youcompress.com/",
                    "   - https://www.media.io/"
                ]
            }
            
    except Exception as e:
        print(f"Get download URLs error: {str(e)}")
        return {"success": False, "error": f"Get download URLs error: {str(e)}"} 

@app.post("/api/video/download-and-combine")
async def download_and_combine_videos():
    """下载所有视频并在后端合并"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 创建临时目录
            temp_dir = Path("temp_videos")
            temp_dir.mkdir(exist_ok=True)
            
            downloaded_files = []
            
            # 下载所有视频
            for i, video in enumerate(videos):
                try:
                    filename = f"shot_{video.shot_number:02d}.mp4"
                    filepath = temp_dir / filename
                    
                    # 使用 requests 下载视频，添加更多请求头
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': 'https://www.volcengine.com/',
                        'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'video',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'cross-site',
                    }
                    
                    response = requests.get(video.video_url, headers=headers, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    downloaded_files.append(str(filepath))
                    print(f"✅ Downloaded video {i+1}/{len(videos)}: {filename}")
                    
                except Exception as e:
                    print(f"❌ Failed to download video {i+1}: {str(e)}")
                    return {"success": False, "error": f"Failed to download video {i+1}: {str(e)}"}
            
            # 使用 ffmpeg 合并视频
            try:
                import subprocess
                
                # 创建视频列表文件
                list_file = temp_dir / "video_list.txt"
                with open(list_file, 'w') as f:
                    for filepath in downloaded_files:
                        f.write(f"file '{filepath}'\n")
                
                # 合并视频
                output_file = "combined_video.mp4"
                background_music = "Back-end/embrace-364091.mp3"
                
                # 先合并视频（不包含音频混合）
                temp_output = "temp_combined_video.mp4"
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0', 
                    '-i', str(list_file), '-c', 'copy', str(Path(temp_output).resolve()), '-y'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"FFmpeg error: {result.stderr}")
                    return {"success": False, "error": f"FFmpeg error: {result.stderr}"}
                
                # 验证临时输出文件
                if not Path(temp_output).exists():
                    return {"success": False, "error": "Combined video file was not created"}
                
                # 添加背景音乐
                if Path(background_music).exists():
                    print(f"Adding background music: {background_music}")
                    cmd_with_music = [
                        'ffmpeg',
                        '-i', temp_output,
                        '-i', background_music,
                        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:weights=0.7,0.3[out]',
                        '-map', '0:v',
                        '-map', '[out]',
                        '-c:v', 'copy',
                        str(Path(output_file).resolve()),
                        '-y'
                    ]
                    
                    result = subprocess.run(cmd_with_music, capture_output=True, text=True)
                    
                    # 删除临时文件
                    if Path(temp_output).exists():
                        os.remove(temp_output)
                    
                    if result.returncode != 0:
                        print(f"FFmpeg music error: {result.stderr}")
                        return {"success": False, "error": f"FFmpeg music error: {result.stderr}"}
                else:
                    # 如果没有背景音乐文件，直接重命名临时文件
                    print(f"Background music file not found: {background_music}, using video without background music")
                    os.rename(temp_output, output_file)
                
                # 返回合并后的视频文件路径
                return {
                    "success": True,
                    "message": f"Successfully combined {len(videos)} videos",
                    "output_file": str(Path(output_file).resolve()),
                    "total_duration": len(videos) * 5,
                    "total_shots": len(videos),
                    "file_size": Path(output_file).stat().st_size if Path(output_file).exists() else 0
                }
                
            except Exception as e:
                print(f"FFmpeg error: {str(e)}")
                return {"success": False, "error": f"FFmpeg error: {str(e)}"}
            
    except Exception as e:
        print(f"Download and combine error: {str(e)}")
        return {"success": False, "error": f"Download and combine error: {str(e)}"}

@app.get("/api/video/download-combined-file")
async def download_combined_file():
    """下载合并后的视频文件"""
    try:
        combined_file = Path("temp_videos/combined_video.mp4")
        
        if not combined_file.exists():
            return {"success": False, "error": "Combined video file not found"}
        
        # 返回文件下载链接
        return {
            "success": True,
            "download_url": f"/download/combined_video.mp4",
            "file_size": combined_file.stat().st_size
        }
        
    except Exception as e:
        print(f"Download combined file error: {str(e)}")
        return {"success": False, "error": f"Download combined file error: {str(e)}"}

from fastapi.responses import FileResponse, StreamingResponse
from fastapi import HTTPException

@app.get("/download/combined_video.mp4")
async def serve_combined_video():
    """提供合并后的视频文件下载"""
    try:
        # 检查多个可能的位置
        possible_paths = [
            Path("combined_video.mp4"),
            Path("temp_videos/combined_video.mp4"),
            Path("./combined_video.mp4")
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            return {"error": "Combined video file not found"}
        
        return FileResponse(
            path=str(file_path),
            filename="combined_video.mp4",
            media_type="video/mp4",
            headers={
                "Content-Disposition": "attachment; filename=combined_video.mp4",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        print(f"Serve combined video error: {str(e)}")
        return {"error": f"Serve combined video error: {str(e)}"}

@app.get("/api/video/debug-files")
async def debug_files():
    """调试文件状态"""
    try:
        import os
        current_dir = Path.cwd()
        
        # 检查当前目录的文件
        current_files = [f.name for f in current_dir.iterdir() if f.is_file()]
        
        # 检查temp_videos目录
        temp_dir = Path("temp_videos")
        temp_files = []
        if temp_dir.exists():
            temp_files = [f.name for f in temp_dir.iterdir() if f.is_file()]
        
        # 检查combined_video.mp4是否存在
        combined_paths = [
            Path("combined_video.mp4"),
            Path("temp_videos/combined_video.mp4"),
            Path("./combined_video.mp4")
        ]
        
        combined_exists = []
        for path in combined_paths:
            combined_exists.append({
                "path": str(path),
                "exists": path.exists(),
                "size": path.stat().st_size if path.exists() else 0
            })
        
        return {
            "current_directory": str(current_dir),
            "current_files": current_files,
            "temp_videos_files": temp_files,
            "combined_video_status": combined_exists
        }
        
    except Exception as e:
        return {"error": f"Debug error: {str(e)}"}

@app.get("/api/video/proxy-download/{video_id}")
async def proxy_download_video(video_id: int):
    """代理下载单个视频文件，绕过CDN限制"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(GeneratedVideo).where(GeneratedVideo.id == video_id)
            )
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            if video.status != "success":
                raise HTTPException(status_code=400, detail="Video generation failed")
            
            # 使用requests下载视频（后端代理）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://visual.volcengineapi.com/',
                'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(video.video_url, headers=headers, stream=True)
            response.raise_for_status()
            
            # 返回视频流
            return StreamingResponse(
                response.iter_content(chunk_size=8192),
                media_type="video/mp4",
                headers={
                    "Content-Disposition": f"attachment; filename=video_{video.shot_number}.mp4",
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
    except Exception as e:
        print(f"Proxy download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.post("/api/video/proxy-combine")
async def proxy_combine_videos():
    """代理下载并合并所有视频 - 使用更强大的反爬虫策略"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 创建临时目录
            temp_dir = Path("temp_videos")
            temp_dir.mkdir(exist_ok=True)
            
            downloaded_files = []
            
            # 下载所有视频 - 使用更强大的请求头
            for i, video in enumerate(videos):
                try:
                    # 使用更真实的浏览器头信息
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'video',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'cross-site',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'DNT': '1',
                        'Referer': 'https://visual.volcengineapi.com/',
                        'Origin': 'https://visual.volcengineapi.com',
                        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"macOS"'
                    }
                    
                    # 使用session来保持连接
                    session_requests = requests.Session()
                    session_requests.headers.update(headers)
                    
                    # 先访问主页面建立会话
                    session_requests.get('https://visual.volcengineapi.com/', timeout=10)
                    
                    # 然后下载视频
                    response = session_requests.get(video.video_url, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    file_path = temp_dir / f"video_{video.shot_number}.mp4"
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    downloaded_files.append(str(file_path))
                    print(f"✅ Downloaded video {video.shot_number}: {file_path}")
                    
                except Exception as e:
                    print(f"❌ Failed to download video {video.shot_number}: {e}")
                    # 尝试备用下载方法
                    try:
                        print(f"🔄 Trying alternative download method for video {video.shot_number}")
                        alt_headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': '*/*',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Connection': 'keep-alive',
                            'Referer': 'https://www.volcengine.com/',
                        }
                        
                        response = requests.get(video.video_url, headers=alt_headers, timeout=30)
                        response.raise_for_status()
                        
                        file_path = temp_dir / f"video_{video.shot_number}.mp4"
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        
                        downloaded_files.append(str(file_path))
                        print(f"✅ Alternative method succeeded for video {video.shot_number}")
                        
                    except Exception as alt_e:
                        print(f"❌ Alternative method also failed: {alt_e}")
                        return {"success": False, "error": f"Failed to download video {video.shot_number}: {str(e)}"}
            
            # 使用ffmpeg合并视频
            try:
                import subprocess
                
                # 创建文件列表
                list_file = temp_dir / "video_list.txt"
                with open(list_file, 'w') as f:
                    for file_path in downloaded_files:
                        # 使用绝对路径，避免路径重复问题
                        abs_path = Path(file_path).resolve()
                        f.write(f"file '{abs_path}'\n")
                
                # 合并视频
                output_file = "combined_video.mp4"
                background_music = "Back-end/embrace-364091.mp3"
                
                # 先合并视频（不包含音频混合）
                temp_output = "temp_combined_video.mp4"
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0', 
                    '-i', str(list_file), '-c', 'copy', str(Path(temp_output).resolve()), '-y'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"FFmpeg error: {result.stderr}")
                    return {"success": False, "error": f"FFmpeg error: {result.stderr}"}
                
                # 验证临时输出文件
                if not Path(temp_output).exists():
                    return {"success": False, "error": "Combined video file was not created"}
                
                # 添加背景音乐
                if Path(background_music).exists():
                    print(f"Adding background music: {background_music}")
                    cmd_with_music = [
                        'ffmpeg',
                        '-i', temp_output,
                        '-i', background_music,
                        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:weights=0.7,0.3[out]',
                        '-map', '0:v',
                        '-map', '[out]',
                        '-c:v', 'copy',
                        str(Path(output_file).resolve()),
                        '-y'
                    ]
                    
                    result = subprocess.run(cmd_with_music, capture_output=True, text=True)
                    
                    # 删除临时文件
                    if Path(temp_output).exists():
                        os.remove(temp_output)
                    
                    if result.returncode != 0:
                        print(f"FFmpeg music error: {result.stderr}")
                        return {"success": False, "error": f"FFmpeg music error: {result.stderr}"}
                else:
                    # 如果没有背景音乐文件，直接重命名临时文件
                    print(f"Background music file not found: {background_music}, using video without background music")
                    os.rename(temp_output, output_file)
                
                # 清理临时文件
                for file_path in downloaded_files:
                    if Path(file_path).exists():
                        os.remove(file_path)
                if list_file.exists():
                    os.remove(list_file)
                if temp_dir.exists() and not any(temp_dir.iterdir()):
                    temp_dir.rmdir()
                
                # 获取输出文件的绝对路径
                output_path = Path(output_file).resolve()
                
                return {
                    "success": True,
                    "message": f"Successfully combined {len(videos)} videos",
                    "output_file": str(output_path),
                    "total_duration": len(videos) * 5,
                    "total_shots": len(videos),
                    "file_size": output_path.stat().st_size if output_path.exists() else 0
                }
                
            except Exception as e:
                print(f"FFmpeg error: {str(e)}")
                return {"success": False, "error": f"FFmpeg error: {str(e)}"}
                
    except Exception as e:
        print(f"Proxy combine error: {str(e)}")
        return {"success": False, "error": f"Proxy combine error: {str(e)}"}

# 启动服务器
# ==================== 应用启动配置 ====================

if __name__ == "__main__":
    """
    应用启动入口
    
    当直接运行此文件时，启动FastAPI应用服务器。
    服务器配置：
    - 主机: 0.0.0.0 (允许所有网络接口访问)
    - 端口: 8000
    - 自动重载: 开发模式下启用
    """
    import uvicorn
    print("🚀 启动AI视频生成平台后端服务...")
    print("📍 服务地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("🔧 按 Ctrl+C 停止服务")
    uvicorn.run(app, host="0.0.0.0", port=8000) 

# ==================== 海螺AI语音合成配置 ====================

# 海螺AI语音合成API配置 - 用于文本转语音功能
HAILUO_API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLlrZnplKbmt7siLCJVc2VyTmFtZSI6IuWtmemUpua3uyIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTUxMTE2MDg5NTk3MzcxMDQ0IiwiUGhvbmUiOiIxMzcwMTE2NDgxNiIsIkdyb3VwSUQiOiIxOTUxMTE2MDg5NTg4OTgyNDM2IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMDgtMTEgMTA6MTQ6MDIiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.ce-7TXB4JC9R31woacWZFx_ZChK35h-KpGriEljduvaYg0Ws-1ECVUnI9SCY_9QX6DzHXFbjNsN2cg-WBPPMJPdUoI4Ynf4jx1XXW6IzgIM4swKNfwMWOTCDJ9_VNKvTpUnEDK9gX4mfSFwkdB62zdMOUgDQONh1GditOurfGsT9UMG4w6jczypl7I4PBG4uO5E-vjRuvV9Hr3g9CGXPMk3iJ-A6-3Y5uZMX1XKWo_l5mPxWls_O8YudULhUPeVq8CJSA5lpLAgkcpj6_Nx8827uKbKyjpjJ1CW1oBt3lk5RxR6JgwichJKZnt0oMEkAGW2FMbbJJl3KK4-pKu282w"

def extract_hailuo_group_id_from_token(token):
    """
    从海螺AI JWT token中提取GroupId
    
    海螺AI使用JWT token进行认证，其中包含了GroupId信息。
    此函数解析JWT token的payload部分，提取GroupId用于API调用。
    
    Args:
        token (str): 海螺AI的JWT token
        
    Returns:
        str: 提取到的GroupId，如果提取失败则返回空字符串
        
    Note:
        JWT token由三部分组成：header.payload.signature
        我们只需要解析payload部分来获取GroupId
    """
    try:
        import base64
        # JWT token由三部分组成，用.分隔
        parts = token.split('.')
        if len(parts) == 3:
            # 解码payload部分（第二部分）
            payload = parts[1]
            # 添加padding
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded.decode('utf-8'))
            return payload_data.get('GroupID', '')
    except Exception as e:
        print(f"提取海螺AI GroupId失败: {e}")
    return ''

async def generate_hailuo_audio(text: str, voice_id: str = "male-qn-qingse") -> dict:
    """
    使用海螺AI生成语音文件
    
    此函数调用海螺AI的文本转语音API，将文本内容转换为高质量的语音文件。
    支持多种音色和语音参数配置。
    
    Args:
        text (str): 要转换为语音的文本内容
        voice_id (str): 音色ID，默认为男性青涩音色
        
    Returns:
        dict: 包含生成结果的字典
            {
                "success": bool,           # 是否成功
                "filename": str,           # 生成的音频文件名
                "file_path": str,          # 音频文件完整路径
                "audio_size": int,         # 音频文件大小（字节）
                "audio_hex": str,          # 音频数据的十六进制表示
                "extra_info": dict,        # 额外信息
                "error": str               # 错误信息（如果失败）
            }
            
    Note:
        - 生成的音频文件保存在 audio_files 目录下
        - 文件名格式：hailuo_audio_{timestamp}.mp3
        - 支持MP3格式，采样率32kHz，比特率128kbps
    """
    try:
        # 提取GroupId
        group_id = extract_hailuo_group_id_from_token(HAILUO_API_KEY)
        if not group_id:
            return {"success": False, "error": "无法提取GroupId"}
        
        # API配置
        url = f"https://api.minimaxi.com/v1/t2a_v2?GroupId={group_id}"
        headers = {
            "Authorization": f"Bearer {HAILUO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 请求数据
        data = {
            "model": "speech-2.5-hd-preview",
            "text": text,
            "stream": False,
            "language_boost": "Chinese",
            "output_format": "hex",
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0,
                "emotion": "happy"
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            }
        }
        
        print(f"🎵 海螺AI语音合成: {text[:50]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and 'audio' in result['data']:
                    audio_hex = result['data']['audio']
                    audio_bytes = bytes.fromhex(audio_hex)
                    
                    # 保存音频文件
                    timestamp = int(time.time())
                    filename = f"hailuo_audio_{timestamp}.mp3"
                    
                    # 创建音频目录
                    audio_dir = Path("audio_files")
                    audio_dir.mkdir(exist_ok=True)
                    
                    file_path = audio_dir / filename
                    with open(file_path, 'wb') as f:
                        f.write(audio_bytes)
                    
                    print(f"✅ 海螺AI语音生成成功: {filename}")
                    
                    return {
                        "success": True,
                        "filename": filename,
                        "file_path": str(file_path),
                        "audio_size": len(audio_bytes),
                        "audio_hex": audio_hex,
                        "extra_info": result.get('extra_info', {})
                    }
                else:
                    return {"success": False, "error": "API响应中没有音频数据"}
            else:
                return {"success": False, "error": f"API请求失败: {response.status_code}"}
                
    except Exception as e:
        print(f"❌ 海螺AI语音合成错误: {e}")
        return {"success": False, "error": str(e)}

# ... existing code ... 

async def generate_digital_human_video_with_dialogue(image_url: str, shot_content: str = "", dialogue: str = "") -> dict:
    """使用火山引擎数字人API生成视频 - 基于分镜图片和对话文本自动生成语音"""
    if not BYTEDANCE_AVAILABLE:
        return {"success": False, "error": "ByteDance SDK not available"}
    
    try:
        # 如果没有提供对话文本，使用分镜内容作为对话
        if not dialogue:
            dialogue = shot_content
        
        print(f"开始数字人视频生成流程:")
        print(f"  图片URL: {image_url}")
        print(f"  分镜内容: {shot_content[:50]}...")
        print(f"  对话文本: {dialogue[:50]}...")
        
        # 第一步：生成语音
        print("步骤1: 生成语音...")
        audio_result = await generate_hailuo_audio(dialogue, "male-qn-qingse")
        
        if not audio_result["success"]:
            return {"success": False, "error": f"语音生成失败: {audio_result.get('error', 'Unknown error')}"}
        
        # 构建音频URL
        audio_filename = audio_result.get('filename', '')
        audio_url = f"http://127.0.0.1:8000/audio/{audio_filename}"
        
        print(f"✅ 语音生成成功: {audio_filename}")
        print(f"   音频URL: {audio_url}")
        
        # 第二步：创建数字人角色
        print("步骤2: 创建数字人角色...")
        visual_service = VisualService()
        visual_service.set_ak(BYTEDANCE_ACCESS_KEY_ID)
        visual_service.set_sk(BYTEDANCE_SECRET_ACCESS_KEY)
        
        create_role_form = {
            "req_key": "realman_avatar_picture_create_role",
            "image_url": image_url
        }
        
        create_resp = visual_service.cv_submit_task(create_role_form)
        print(f"创建角色响应: {create_resp}")
        
        if create_resp.get("code") != 10000:
            error_msg = create_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"创建角色失败: {error_msg}", "code": create_resp.get("code")}
        
        task_id = create_resp.get("data", {}).get("task_id")
        if not task_id:
            return {"success": False, "error": "未收到创建角色的task_id"}
        
        print(f"创建角色任务ID: {task_id}")
        
        # 等待10秒后查询角色创建结果
        print("等待10秒后查询角色创建结果...")
        await asyncio.sleep(10)
        
        # 第三步：查询角色创建结果
        print("步骤3: 查询角色创建结果...")
        get_role_form = {
            "req_key": "realman_avatar_picture_create_role",
            "task_id": task_id
        }
        
        get_role_resp = visual_service.cv_get_result(get_role_form)
        print(f"获取角色响应: {get_role_resp}")
        
        if get_role_resp.get("code") != 10000:
            error_msg = get_role_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"获取角色失败: {error_msg}", "code": get_role_resp.get("code")}
        
        resp_data = json.loads(get_role_resp["data"]["resp_data"])
        resource_id = resp_data.get("resource_id")
        if not resource_id:
            return {"success": False, "error": "未收到角色资源ID"}
        
        print(f"角色资源ID: {resource_id}")
        
        # 等待3秒后开始生成视频
        print("等待3秒后开始生成视频...")
        await asyncio.sleep(3)
        
        # 第四步：生成数字人视频
        print("步骤4: 生成数字人视频...")
        generate_video_form = {
            "req_key": "realman_avatar_picture_loopyb",
            "resource_id": resource_id,
            "audio_url": audio_url
        }
        
        video_resp = visual_service.cv_submit_task(generate_video_form)
        print(f"生成视频响应: {video_resp}")
        
        if video_resp.get("code") != 10000:
            error_msg = video_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"生成视频失败: {error_msg}", "code": video_resp.get("code")}
        
        video_task_id = video_resp.get("data", {}).get("task_id")
        if not video_task_id:
            return {"success": False, "error": "未收到视频生成任务ID"}
        
        print(f"视频生成任务ID: {video_task_id}")
        
        # 等待10秒后查询视频生成结果
        print("等待10秒后查询视频生成结果...")
        await asyncio.sleep(10)
        
        # 第五步：查询视频生成结果
        print("步骤5: 查询视频生成结果...")
        for i in range(30):  # 最多查30次
            query_form = {
                "req_key": "realman_avatar_picture_loopyb",
                "task_id": video_task_id
            }
            
            result_resp = visual_service.cv_get_result(query_form)
            print(f"查询结果 {i+1}: {result_resp}")
            
            status = result_resp.get("data", {}).get("status")
            if status == "done" or status == 2:  # 成功
                video_url = result_resp["data"].get("video_url")
                return {
                    "success": True,
                    "task_id": video_task_id,
                    "video_url": video_url,
                    "resource_id": resource_id,
                    "shot_content": shot_content,
                    "dialogue": dialogue,
                    "image_url": image_url,
                    "audio_url": audio_url,
                    "audio_filename": audio_filename
                }
            elif status == "failed" or status == 3:  # 失败
                return {"success": False, "error": "数字人视频生成失败"}
            else:
                # 还在生成中，等待5秒
                print("视频生成中，等待5秒...")
                await asyncio.sleep(5)
        
        return {"success": False, "error": "数字人视频生成超时"}
        
    except Exception as e:
        error_str = str(e)
        print(f"数字人视频生成错误: {error_str}")
        return {"success": False, "error": f"数字人视频生成API错误: {error_str}"}

async def generate_digital_human_video(image_url: str, audio_url: str, shot_content: str = "") -> dict:
    """使用火山引擎数字人API生成视频 - 基于分镜图片和音频"""
    if not BYTEDANCE_AVAILABLE:
        return {"success": False, "error": "ByteDance SDK not available"}
    
    try:
        # 初始化火山引擎服务
        visual_service = VisualService()
        visual_service.set_ak(BYTEDANCE_ACCESS_KEY_ID)
        visual_service.set_sk(BYTEDANCE_SECRET_ACCESS_KEY)
        
        print(f"开始数字人视频生成流程:")
        print(f"  图片URL: {image_url}")
        print(f"  音频URL: {audio_url}")
        print(f"  分镜内容: {shot_content[:50]}...")
        
        # 第一步：创建数字人角色
        print("步骤1: 创建数字人角色...")
        create_role_form = {
            "req_key": "realman_avatar_picture_create_role",
            "image_url": image_url
        }
        
        create_resp = visual_service.cv_submit_task(create_role_form)
        print(f"创建角色响应: {create_resp}")
        
        if create_resp.get("code") != 10000:
            error_msg = create_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"创建角色失败: {error_msg}", "code": create_resp.get("code")}
        
        task_id = create_resp.get("data", {}).get("task_id")
        if not task_id:
            return {"success": False, "error": "未收到创建角色的task_id"}
        
        print(f"创建角色任务ID: {task_id}")
        
        # 等待角色创建完成
        print("等待角色创建完成...")
        await asyncio.sleep(10)
        
        # 第二步：获取角色资源ID
        print("步骤2: 获取角色资源ID...")
        get_role_form = {
            "req_key": "realman_avatar_picture_create_role",
            "task_id": task_id
        }
        
        get_role_resp = visual_service.cv_get_result(get_role_form)
        print(f"获取角色响应: {get_role_resp}")
        
        if get_role_resp.get("code") != 10000:
            error_msg = get_role_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"获取角色失败: {error_msg}", "code": get_role_resp.get("code")}
        
        resp_data = json.loads(get_role_resp["data"]["resp_data"])
        resource_id = resp_data.get("resource_id")
        if not resource_id:
            return {"success": False, "error": "未收到角色资源ID"}
        
        print(f"角色资源ID: {resource_id}")
        
        # 等待一下再生成视频
        print("等待10秒后开始生成视频...")
        await asyncio.sleep(10)
        
        # 第三步：生成数字人视频
        print("步骤3: 生成数字人视频...")
        generate_video_form = {
            "req_key": "realman_avatar_picture_loopyb",
            "resource_id": resource_id,
            "audio_url": audio_url
        }
        
        video_resp = visual_service.cv_submit_task(generate_video_form)
        print(f"生成视频响应: {video_resp}")
        
        if video_resp.get("code") != 10000:
            error_msg = video_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"生成视频失败: {error_msg}", "code": video_resp.get("code")}
        
        video_task_id = video_resp.get("data", {}).get("task_id")
        if not video_task_id:
            return {"success": False, "error": "未收到视频生成任务ID"}
        
        print(f"视频生成任务ID: {video_task_id}")
        
        # 轮询查询视频生成结果
        print("轮询查询视频生成结果...")
        for i in range(30):  # 最多查30次
            query_form = {
                "req_key": "realman_avatar_picture_loopyb",
                "task_id": video_task_id
            }
            
            result_resp = visual_service.cv_get_result(query_form)
            print(f"查询结果 {i+1}: {result_resp}")
            
            status = result_resp.get("data", {}).get("status")
            if status == "done" or status == 2:  # 成功
                video_url = result_resp["data"].get("video_url")
                return {
                    "success": True,
                    "task_id": video_task_id,
                    "video_url": video_url,
                    "resource_id": resource_id,
                    "shot_content": shot_content,
                    "image_url": image_url,
                    "audio_url": audio_url
                }
            elif status == "failed" or status == 3:  # 失败
                return {"success": False, "error": "数字人视频生成失败"}
            else:
                # 还在生成中，等待5秒
                print("视频生成中，等待5秒...")
                await asyncio.sleep(5)
        
        return {"success": False, "error": "数字人视频生成超时"}
        
    except Exception as e:
        error_str = str(e)
        print(f"数字人视频生成错误: {error_str}")
        return {"success": False, "error": f"数字人视频生成API错误: {error_str}"}

async def generate_bytedance_video(shot: str, style: str = "Realistic", aspect_ratio: str = "16:9"):
    """使用字节即梦AI生成视频 - 基于文本提示词"""
    if not BYTEDANCE_AVAILABLE:
        return {"success": False, "error": "ByteDance SDK not available"}
    
    try:
        # 初始化字节AI服务
        vs = VisualService()
        vs.set_ak(BYTEDANCE_ACCESS_KEY_ID)
        vs.set_sk(BYTEDANCE_SECRET_ACCESS_KEY)
        vs.set_host("visual.volcengineapi.com")
        
        # 构建请求体
        body = {
            "req_key": "jimeng_vgfm_t2v_l20",
            "prompt": shot,
            "aspect_ratio": aspect_ratio
        }
        
        # 提交任务
        submit_resp = vs.cv_sync2async_submit_task(body)
        print("ByteDance submit response:", submit_resp)
        
        if submit_resp.get("code") != 10000:
            error_msg = submit_resp.get('message', 'Unknown error')
            return {"success": False, "error": f"Submit failed: {error_msg}", "code": submit_resp.get("code")}
        
        task_id = submit_resp.get("data", {}).get("task_id")
        if not task_id:
            return {"success": False, "error": "No task_id received"}
        
        # 轮询查询结果
        import time
        for i in range(30):  # 最多查30次
            result = vs.cv_sync2async_get_result({
                "task_id": task_id,
                "req_key": "jimeng_vgfm_t2v_l20"
            })
            print(f"ByteDance query {i+1}:", result)
            
            status = result.get("data", {}).get("status")
            if status == "done" or status == 2:  # 成功
                video_url = result["data"].get("video_url")
                return {
                    "success": True,
                    "task_id": task_id,
                    "video_url": video_url,
                    "shot": shot
                }
            elif status == "failed" or status == 3:  # 失败
                return {"success": False, "error": "Video generation failed"}
            else:
                # 还在生成中，等待5秒
                await asyncio.sleep(5)
        
        return {"success": False, "error": "Generation timeout"}
        
    except Exception as e:
        error_str = str(e)
        # 检查是否是并发限制错误
        if "50430" in error_str or "Concurrent Limit" in error_str:
            return {"success": False, "error": f"Concurrent limit reached: {error_str}", "code": 50430}
        else:
            return {"success": False, "error": f"ByteDance API error: {error_str}"}



class ShotVideoGenerationRequest(BaseModel):
    shot_number: int
    style: str = "Realistic"
    aspect_ratio: str = "16:9"

@app.post("/api/video/generate-shot-video")
async def generate_shot_video(data: ShotVideoGenerationRequest):
    """基于分镜图片生成视频"""
    try:
        async with async_session() as session:
            # 获取对应的分镜图片
            result = await session.execute(
                select(ShotImage).where(
                    ShotImage.shot_number == data.shot_number,
                    ShotImage.status == "success"
                ).order_by(ShotImage.id.desc()).limit(1)
            )
            shot_image = result.scalar_one_or_none()
            
            if not shot_image:
                return {"success": False, "error": f"分镜 {data.shot_number} 的图片未找到或生成失败"}
            
            print(f"基于分镜图片生成视频:")
            print(f"  分镜编号: {data.shot_number}")
            print(f"  图片URL: {shot_image.image_url}")
            print(f"  分镜内容: {shot_image.shot_content[:50]}...")
            print(f"  风格: {data.style}")
            print(f"  比例: {data.aspect_ratio}")
            
            # 调用图生视频API
            result = await generate_bytedance_video_from_image(
                shot_image.image_url,
                shot_image.shot_content,
                data.style,
                data.aspect_ratio
            )
            
            print(f"图生视频结果: {result}")
            
            if result["success"]:
                # 保存到数据库
                generated_video = GeneratedVideo(
                    shot_number=data.shot_number,
                    shot_content=shot_image.shot_content,
                    style=data.style,
                    aspect_ratio=data.aspect_ratio,
                    task_id=result.get("task_id", ""),
                    video_url=result.get("video_url", ""),
                    status="success"
                )
                
                session.add(generated_video)
                await session.commit()
                
                return {
                    "success": True,
                    "shot_number": data.shot_number,
                    "video_url": result.get("video_url"),
                    "task_id": result.get("task_id"),
                    "image_url": shot_image.image_url
                }
            else:
                # 保存失败记录
                generated_video = GeneratedVideo(
                    shot_number=data.shot_number,
                    shot_content=shot_image.shot_content,
                    style=data.style,
                    aspect_ratio=data.aspect_ratio,
                    task_id="",
                    video_url="",
                    status="failed",
                    error_message=result.get("error", "Unknown error")
                )
                
                session.add(generated_video)
                await session.commit()
                
                return {"success": False, "error": result.get("error", "Unknown error")}
                
    except Exception as e:
        print(f"生成分镜视频错误: {str(e)}")
        return {"success": False, "error": f"Shot video generation error: {str(e)}"}

@app.post("/api/video/generate-video")
async def generate_video(data: VideoGenerationRequest):
    """生成单个分镜的视频 - 基于文本提示词"""
    try:
        # 获取用户选择的风格和比例
        style = data.style
        aspect_ratio = data.aspect_ratio
        shot = data.shot
        
        print(f"Received video generation request:")
        print(f"  Shot: {shot[:50]}...")
        print(f"  Style: {style}")
        print(f"  Aspect Ratio: {aspect_ratio}")
        
        # 调用字节AI生成视频
        result = await generate_bytedance_video(shot, style, aspect_ratio)
        
        print(f"ByteDance result: {result}")
        
        # 保存到数据库
        async with async_session() as session:
            # 获取当前最大的shot_number，用于确定新分镜的编号
            result_query = await session.execute(select(GeneratedVideo.shot_number))
            existing_numbers = result_query.scalars().all()
            shot_number = max(existing_numbers) + 1 if existing_numbers else 1
            
            # 创建新的GeneratedVideo记录
            generated_video = GeneratedVideo(
                shot_number=shot_number,
                shot_content=shot,
                style=style,
                aspect_ratio=aspect_ratio,
                task_id=result.get("task_id", ""),
                video_url=result.get("video_url", ""),
                status="success" if result.get("success") else "failed",
                error_message=result.get("error", "") if not result.get("success") else None
            )
            
            session.add(generated_video)
            await session.commit()
            await session.refresh(generated_video)
            
            print(f"Saved to database with ID: {generated_video.id}")
        
        return result
        
    except Exception as e:
        print(f"Video generation error: {str(e)}")
        
        # 即使出错也要保存到数据库
        try:
            async with async_session() as session:
                result_query = await session.execute(select(GeneratedVideo.shot_number))
                existing_numbers = result_query.scalars().all()
                shot_number = max(existing_numbers) + 1 if existing_numbers else 1
                
                generated_video = GeneratedVideo(
                    shot_number=shot_number,
                    shot_content=shot,
                    style=style,
                    aspect_ratio=aspect_ratio,
                    task_id="",
                    video_url="",
                    status="failed",
                    error_message=str(e)
                )
                
                session.add(generated_video)
                await session.commit()
                print(f"Saved error to database with ID: {generated_video.id}")
        except Exception as db_error:
            print(f"Database save error: {str(db_error)}")
        
        return {"success": False, "error": f"Video generation error: {str(e)}"}



@app.post("/api/video/generate-all-shot-videos")
async def generate_all_shot_videos():
    """为所有分镜生成视频 - 基于分镜第一帧图片生成"""
    try:
        async with async_session() as session:
            # 获取所有成功的分镜图片
            result = await session.execute(
                select(ShotImage).where(ShotImage.status == "success").order_by(ShotImage.shot_number)
            )
            shot_images = result.scalars().all()
            
            if not shot_images:
                return {"success": False, "error": "没有找到成功的分镜图片，请先生成分镜图片"}
            
            print(f"找到 {len(shot_images)} 个分镜图片需要生成视频")
            
            success_count = 0
            total_count = len(shot_images)
            
            # 为每个分镜生成视频
            for i, shot_image in enumerate(shot_images):
                print(f"正在处理第 {i+1}/{total_count} 个分镜视频: {shot_image.shot_number}")
                
                # 检查是否已经生成过
                existing_result = await session.execute(
                    select(GeneratedVideo).where(
                        GeneratedVideo.shot_number == shot_image.shot_number,
                        GeneratedVideo.status == "success"
                    ).order_by(GeneratedVideo.id.desc()).limit(1)
                )
                existing_video = existing_result.scalar_one_or_none()
                
                if existing_video:
                    print(f"分镜 {shot_image.shot_number} 已有视频，跳过生成")
                    success_count += 1
                    continue
                
                # 基于分镜图片生成视频
                video_result = await generate_bytedance_video_from_image(
                    shot_image.image_url,
                    shot_image.shot_content,
                    shot_image.style,
                    shot_image.aspect_ratio
                )
                
                # 保存到数据库
                generated_video = GeneratedVideo(
                    shot_number=shot_image.shot_number,
                    shot_content=shot_image.shot_content,
                    style=shot_image.style,
                    aspect_ratio=shot_image.aspect_ratio,
                    task_id=video_result.get("task_id", ""),
                    video_url=video_result.get("video_url", ""),
                    status="success" if video_result["success"] else "failed",
                    error_message=video_result.get("error", "") if not video_result["success"] else None
                )
                
                session.add(generated_video)
                await session.commit()
                
                if video_result["success"]:
                    success_count += 1
                    print(f"✅ 分镜 {shot_image.shot_number} 视频生成成功")
                else:
                    print(f"❌ 分镜 {shot_image.shot_number} 视频生成失败: {video_result.get('error', 'Unknown error')}")
                
                # 等待5秒再生成下一个
                if i < total_count - 1:
                    print("等待5秒后继续...")
                    await asyncio.sleep(5)
            
            print(f"所有分镜视频生成完成，成功: {success_count}/{total_count}")
            return {
                "success": True,
                "total_shots": total_count,
                "successful_videos": success_count,
                "failed_videos": total_count - success_count
            }
            
    except Exception as e:
        print(f"生成分镜视频错误: {str(e)}")
        return {"success": False, "error": f"All shot videos generation error: {str(e)}"}

@app.get("/api/video/generated-videos")
async def list_generated_videos():
    """获取所有生成的视频列表"""
    async with async_session() as session:
        result = await session.execute(select(GeneratedVideo).order_by(GeneratedVideo.created_at.desc()))
        videos = result.scalars().all()
        return [
            {
                "id": v.id,
                "shot_number": v.shot_number,
                "shot_content": v.shot_content,
                "style": v.style,
                "aspect_ratio": v.aspect_ratio,
                "task_id": v.task_id,
                "video_url": v.video_url,
                "status": v.status,
                "error_message": v.error_message,
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in videos
        ]

@app.delete("/api/video/generated-videos/{video_id}")
async def delete_generated_video(video_id: int):
    """删除指定的生成视频记录"""
    async with async_session() as session:
        result = await session.execute(select(GeneratedVideo).where(GeneratedVideo.id == video_id))
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        await session.delete(video)
        await session.commit()
        
        return {"success": True, "message": "Video deleted successfully"}

@app.delete("/api/video/generated-videos")
async def clear_all_generated_videos():
    """清空所有生成的视频记录"""
    async with async_session() as session:
        await session.execute(GeneratedVideo.__table__.delete())
        await session.commit()
        
        return {"success": True, "message": "All videos cleared successfully"}

@app.post("/api/video/clear-current-session")
async def clear_current_session():
    """清空当前会话的视频数据（保留其他数据）"""
    async with async_session() as session:
        # 只清空generated_videos表，保留其他数据
        await session.execute(GeneratedVideo.__table__.delete())
        await session.commit()
        
        return {
            "success": True, 
            "message": "Current session videos cleared successfully",
            "cleared_tables": ["generated_videos"]
        }

@app.post("/api/video/combine-videos")
async def combine_videos():
    """将所有成功的视频合并成一个完整视频"""
    try:
        async with async_session() as session:
            # 获取所有成功的视频，按shot_number排序
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 构建合并后的视频信息
            combined_video = {
                "success": True,
                "total_shots": len(videos),
                "videos": [
                    {
                        "shot_number": v.shot_number,
                        "shot_content": v.shot_content,
                        "video_url": v.video_url,
                        "style": v.style,
                        "aspect_ratio": v.aspect_ratio,
                        "duration": 5  # ByteDance生成的视频通常是5秒
                    }
                    for v in videos
                ],
                "total_duration": len(videos) * 5,  # 总时长（秒）
                "message": f"Successfully combined {len(videos)} video shots"
            }
            
            return combined_video
            
    except Exception as e:
        print(f"Combine videos error: {str(e)}")
        return {"success": False, "error": f"Combine videos error: {str(e)}"}

@app.get("/api/video/combine-status")
async def get_combine_status():
    """获取视频合并状态"""
    try:
        async with async_session() as session:
            # 获取统计信息
            total_result = await session.execute(select(GeneratedVideo))
            total_videos = len(total_result.scalars().all())
            
            success_result = await session.execute(
                select(GeneratedVideo).where(GeneratedVideo.status == "success")
            )
            success_videos = len(success_result.scalars().all())
            
            failed_result = await session.execute(
                select(GeneratedVideo).where(GeneratedVideo.status == "failed")
            )
            failed_videos = len(failed_result.scalars().all())
            
            return {
                "success": True,
                "total_videos": total_videos,
                "success_videos": success_videos,
                "failed_videos": failed_videos,
                "can_combine": success_videos > 0,
                "estimated_duration": success_videos * 5  # 每个视频5秒
            }
            
    except Exception as e:
        return {"success": False, "error": f"Status check error: {str(e)}"}

@app.get("/api/video/test-url/{video_id}")
async def test_video_url(video_id: int):
    """测试视频URL是否可访问"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(GeneratedVideo).where(GeneratedVideo.id == video_id)
            )
            video = result.scalar_one_or_none()
            
            if not video:
                return {"success": False, "error": "Video not found"}
            
            # 测试URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            
            response = requests.head(video.video_url, headers=headers, timeout=10)
            
            return {
                "success": True,
                "video_id": video_id,
                "shot_number": video.shot_number,
                "url": video.video_url,
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', 'Unknown'),
                "content_length": response.headers.get('Content-Length', 'Unknown'),
                "accessible": response.status_code == 200
            }
            
    except Exception as e:
        return {"success": False, "error": f"Test failed: {str(e)}"}

async def download_video(url: str, filename: str) -> str:
    """下载视频到临时文件"""
    try:
        print(f"Attempting to download: {url}")
        
        # 添加请求头，模拟浏览器请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://visual.volcengineapi.com/',  # 或者你实际访问的页面
        }
        
        response = requests.get(url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
        
        # 创建临时文件
        temp_dir = Path(tempfile.gettempdir()) / "aiva_videos"
        temp_dir.mkdir(exist_ok=True)
        
        file_path = temp_dir / filename
        
        # 检查文件大小
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded_size = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"Download progress: {progress:.1f}%")
        
        # 验证文件是否下载成功
        if file_path.exists() and file_path.stat().st_size > 0:
            print(f"Successfully downloaded: {filename} ({file_path.stat().st_size} bytes)")
            return str(file_path)
        else:
            raise Exception("Downloaded file is empty or doesn't exist")
            
    except Exception as e:
        print(f"Error downloading video {url}: {str(e)}")
        # 如果文件存在但下载失败，删除它
        temp_dir = Path(tempfile.gettempdir()) / "aiva_videos"
        file_path = temp_dir / filename
        if file_path.exists():
            file_path.unlink()
        raise

@app.post("/api/video/download-combined")
async def download_combined_video():
    """下载合并后的完整视频"""
    try:
        async with async_session() as session:
            # 获取所有成功的视频，按shot_number排序
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 创建临时目录
            temp_dir = Path(tempfile.gettempdir()) / "aiva_videos"
            temp_dir.mkdir(exist_ok=True)
            
            # 下载所有视频
            downloaded_files = []
            for i, video in enumerate(videos):
                try:
                    print(f"\n--- Downloading video {video.shot_number} ---")
                    print(f"URL: {video.video_url}")
                    print(f"Style: {video.style}")
                    print(f"Aspect Ratio: {video.aspect_ratio}")
                    
                    filename = f"shot_{video.shot_number:02d}.mp4"
                    file_path = await download_video(video.video_url, filename)
                    downloaded_files.append(file_path)
                    print(f"✅ Successfully downloaded: {filename}")
                except Exception as e:
                    error_msg = f"Failed to download video {video.shot_number}: {str(e)}"
                    print(f"❌ {error_msg}")
                    print(f"Video URL: {video.video_url}")
                    return {"success": False, "error": error_msg}
            
            # 创建合并后的视频信息
            combined_info = {
                "success": True,
                "total_shots": len(videos),
                "total_duration": len(videos) * 5,  # 每个视频5秒
                "downloaded_files": downloaded_files,
                "message": f"Successfully downloaded {len(videos)} video shots",
                "download_links": [
                    {
                        "shot_number": video.shot_number,
                        "video_url": video.video_url,
                        "local_file": downloaded_files[i]
                    }
                    for i, video in enumerate(videos)
                ]
            }
            
            return combined_info
            
    except Exception as e:
        print(f"Download combined video error: {str(e)}")
        return {"success": False, "error": f"Download error: {str(e)}"}

@app.get("/api/video/download-status")
async def get_download_status():
    """获取下载状态"""
    try:
        temp_dir = Path(tempfile.gettempdir()) / "aiva_videos"
        if temp_dir.exists():
            files = list(temp_dir.glob("*.mp4"))
            return {
                "success": True,
                "downloaded_files": len(files),
                "files": [f.name for f in files]
            }
        else:
            return {
                "success": True,
                "downloaded_files": 0,
                "files": []
            }
    except Exception as e:
        return {"success": False, "error": f"Status check error: {str(e)}"} 

@app.get("/api/video/download-urls")
async def get_video_download_urls():
    """获取所有成功视频的下载链接，用于手动下载"""
    try:
        async with async_session() as session:
            # 获取所有成功的视频，按shot_number排序
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 构建下载链接列表
            download_links = []
            for video in videos:
                download_links.append({
                    "shot_number": video.shot_number,
                    "shot_content": video.shot_content[:100] + "..." if len(video.shot_content) > 100 else video.shot_content,
                    "video_url": video.video_url,
                    "style": video.style,
                    "aspect_ratio": video.aspect_ratio,
                    "duration": 5  # ByteDance生成的视频通常是5秒
                })
            
            return {
                "success": True,
                "total_shots": len(videos),
                "total_duration": len(videos) * 5,
                "message": f"Found {len(videos)} video shots for manual download",
                "download_links": download_links,
                "instructions": [
                    "1. Click each video URL to download the individual video files",
                    "2. Use a video editing software (like FFmpeg, Adobe Premiere, etc.) to combine them",
                    "3. Or use online video combiners like:",
                    "   - https://www.onlinevideoconverter.com/",
                    "   - https://www.youcompress.com/",
                    "   - https://www.media.io/"
                ]
            }
            
    except Exception as e:
        print(f"Get download URLs error: {str(e)}")
        return {"success": False, "error": f"Get download URLs error: {str(e)}"} 

@app.post("/api/video/download-and-combine")
async def download_and_combine_videos():
    """下载所有视频并在后端合并"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 创建临时目录
            temp_dir = Path("temp_videos")
            temp_dir.mkdir(exist_ok=True)
            
            downloaded_files = []
            
            # 下载所有视频
            for i, video in enumerate(videos):
                try:
                    filename = f"shot_{video.shot_number:02d}.mp4"
                    filepath = temp_dir / filename
                    
                    # 使用 requests 下载视频，添加更多请求头
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': 'https://www.volcengine.com/',
                        'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'video',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'cross-site',
                    }
                    
                    response = requests.get(video.video_url, headers=headers, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    downloaded_files.append(str(filepath))
                    print(f"✅ Downloaded video {i+1}/{len(videos)}: {filename}")
                    
                except Exception as e:
                    print(f"❌ Failed to download video {i+1}: {str(e)}")
                    return {"success": False, "error": f"Failed to download video {i+1}: {str(e)}"}
            
            # 使用 ffmpeg 合并视频
            try:
                import subprocess
                
                # 创建视频列表文件
                list_file = temp_dir / "video_list.txt"
                with open(list_file, 'w') as f:
                    for filepath in downloaded_files:
                        f.write(f"file '{filepath}'\n")
                
                # 合并视频
                output_file = "combined_video.mp4"
                background_music = "Back-end/embrace-364091.mp3"
                
                # 先合并视频（不包含音频混合）
                temp_output = "temp_combined_video.mp4"
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0', 
                    '-i', str(list_file), '-c', 'copy', str(Path(temp_output).resolve()), '-y'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"FFmpeg error: {result.stderr}")
                    return {"success": False, "error": f"FFmpeg error: {result.stderr}"}
                
                # 验证临时输出文件
                if not Path(temp_output).exists():
                    return {"success": False, "error": "Combined video file was not created"}
                
                # 添加背景音乐
                if Path(background_music).exists():
                    print(f"Adding background music: {background_music}")
                    cmd_with_music = [
                        'ffmpeg',
                        '-i', temp_output,
                        '-i', background_music,
                        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:weights=0.7,0.3[out]',
                        '-map', '0:v',
                        '-map', '[out]',
                        '-c:v', 'copy',
                        str(Path(output_file).resolve()),
                        '-y'
                    ]
                    
                    result = subprocess.run(cmd_with_music, capture_output=True, text=True)
                    
                    # 删除临时文件
                    if Path(temp_output).exists():
                        os.remove(temp_output)
                    
                    if result.returncode != 0:
                        print(f"FFmpeg music error: {result.stderr}")
                        return {"success": False, "error": f"FFmpeg music error: {result.stderr}"}
                else:
                    # 如果没有背景音乐文件，直接重命名临时文件
                    print(f"Background music file not found: {background_music}, using video without background music")
                    os.rename(temp_output, output_file)
                
                # 清理临时文件
                for file_path in downloaded_files:
                    if Path(file_path).exists():
                        os.remove(file_path)
                if list_file.exists():
                    os.remove(list_file)
                if temp_dir.exists() and not any(temp_dir.iterdir()):
                    temp_dir.rmdir()
                
                # 获取输出文件的绝对路径
                output_path = Path(output_file).resolve()
                
                return {
                    "success": True,
                    "message": f"Successfully combined {len(videos)} videos",
                    "output_file": str(output_path),
                    "total_duration": len(videos) * 5,
                    "total_shots": len(videos),
                    "file_size": output_path.stat().st_size if output_path.exists() else 0
                }
                
            except Exception as e:
                print(f"FFmpeg error: {str(e)}")
                return {"success": False, "error": f"FFmpeg error: {str(e)}"}
            
    except Exception as e:
        print(f"Download and combine error: {str(e)}")
        return {"success": False, "error": f"Download and combine error: {str(e)}"}

@app.get("/api/video/download-combined-file")
async def download_combined_file():
    """下载合并后的视频文件"""
    try:
        combined_file = Path("temp_videos/combined_video.mp4")
        
        if not combined_file.exists():
            return {"success": False, "error": "Combined video file not found"}
        
        # 返回文件下载链接
        return {
            "success": True,
            "download_url": f"/download/combined_video.mp4",
            "file_size": combined_file.stat().st_size
        }
        
    except Exception as e:
        print(f"Download combined file error: {str(e)}")
        return {"success": False, "error": f"Download combined file error: {str(e)}"}

from fastapi.responses import FileResponse, StreamingResponse
from fastapi import HTTPException

@app.get("/download/combined_video.mp4")
async def serve_combined_video():
    """提供合并后的视频文件下载"""
    try:
        # 检查多个可能的位置
        possible_paths = [
            Path("combined_video.mp4"),
            Path("temp_videos/combined_video.mp4"),
            Path("./combined_video.mp4")
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            return {"error": "Combined video file not found"}
        
        return FileResponse(
            path=str(file_path),
            filename="combined_video.mp4",
            media_type="video/mp4",
            headers={
                "Content-Disposition": "attachment; filename=combined_video.mp4",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        print(f"Serve combined video error: {str(e)}")
        return {"error": f"Serve combined video error: {str(e)}"}

@app.get("/api/video/debug-files")
async def debug_files():
    """调试文件状态"""
    try:
        import os
        current_dir = Path.cwd()
        
        # 检查当前目录的文件
        current_files = [f.name for f in current_dir.iterdir() if f.is_file()]
        
        # 检查temp_videos目录
        temp_dir = Path("temp_videos")
        temp_files = []
        if temp_dir.exists():
            temp_files = [f.name for f in temp_dir.iterdir() if f.is_file()]
        
        # 检查combined_video.mp4是否存在
        combined_paths = [
            Path("combined_video.mp4"),
            Path("temp_videos/combined_video.mp4"),
            Path("./combined_video.mp4")
        ]
        
        combined_exists = []
        for path in combined_paths:
            combined_exists.append({
                "path": str(path),
                "exists": path.exists(),
                "size": path.stat().st_size if path.exists() else 0
            })
        
        return {
            "current_directory": str(current_dir),
            "current_files": current_files,
            "temp_videos_files": temp_files,
            "combined_video_status": combined_exists
        }
        
    except Exception as e:
        return {"error": f"Debug error: {str(e)}"}

@app.get("/api/video/proxy-download/{video_id}")
async def proxy_download_video(video_id: int):
    """代理下载单个视频文件，绕过CDN限制"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(GeneratedVideo).where(GeneratedVideo.id == video_id)
            )
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            if video.status != "success":
                raise HTTPException(status_code=400, detail="Video generation failed")
            
            # 使用requests下载视频（后端代理）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://visual.volcengineapi.com/',
                'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(video.video_url, headers=headers, stream=True)
            response.raise_for_status()
            
            # 返回视频流
            return StreamingResponse(
                response.iter_content(chunk_size=8192),
                media_type="video/mp4",
                headers={
                    "Content-Disposition": f"attachment; filename=video_{video.shot_number}.mp4",
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
    except Exception as e:
        print(f"Proxy download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.post("/api/video/proxy-combine")
async def proxy_combine_videos():
    """代理下载并合并所有视频 - 使用更强大的反爬虫策略"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(GeneratedVideo)
                .where(GeneratedVideo.status == "success")
                .order_by(GeneratedVideo.shot_number)
            )
            videos = result.scalars().all()
            
            if not videos:
                return {"success": False, "error": "No successful videos found"}
            
            # 创建临时目录
            temp_dir = Path("temp_videos")
            temp_dir.mkdir(exist_ok=True)
            
            downloaded_files = []
            
            # 下载所有视频 - 使用更强大的请求头
            for i, video in enumerate(videos):
                try:
                    # 使用更真实的浏览器头信息
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'video',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'cross-site',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'DNT': '1',
                        'Referer': 'https://visual.volcengineapi.com/',
                        'Origin': 'https://visual.volcengineapi.com',
                        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"macOS"'
                    }
                    
                    # 使用session来保持连接
                    session_requests = requests.Session()
                    session_requests.headers.update(headers)
                    
                    # 先访问主页面建立会话
                    session_requests.get('https://visual.volcengineapi.com/', timeout=10)
                    
                    # 然后下载视频
                    response = session_requests.get(video.video_url, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    file_path = temp_dir / f"video_{video.shot_number}.mp4"
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    downloaded_files.append(str(file_path))
                    print(f"✅ Downloaded video {video.shot_number}: {file_path}")
                    
                except Exception as e:
                    print(f"❌ Failed to download video {video.shot_number}: {e}")
                    # 尝试备用下载方法
                    try:
                        print(f"🔄 Trying alternative download method for video {video.shot_number}")
                        alt_headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': '*/*',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Connection': 'keep-alive',
                            'Referer': 'https://www.volcengine.com/',
                        }
                        
                        response = requests.get(video.video_url, headers=alt_headers, timeout=30)
                        response.raise_for_status()
                        
                        file_path = temp_dir / f"video_{video.shot_number}.mp4"
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        
                        downloaded_files.append(str(file_path))
                        print(f"✅ Alternative method succeeded for video {video.shot_number}")
                        
                    except Exception as alt_e:
                        print(f"❌ Alternative method also failed: {alt_e}")
                        return {"success": False, "error": f"Failed to download video {video.shot_number}: {str(e)}"}
            
            # 使用ffmpeg合并视频
            try:
                import subprocess
                
                # 创建文件列表
                list_file = temp_dir / "video_list.txt"
                with open(list_file, 'w') as f:
                    for file_path in downloaded_files:
                        # 使用绝对路径，避免路径重复问题
                        abs_path = Path(file_path).resolve()
                        f.write(f"file '{abs_path}'\n")
                
                # 合并视频
                output_file = "combined_video.mp4"
                background_music = "Back-end/embrace-364091.mp3"
                
                # 先合并视频（不包含音频混合）
                temp_output = "temp_combined_video.mp4"
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0', 
                    '-i', str(list_file), '-c', 'copy', str(Path(temp_output).resolve()), '-y'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"FFmpeg error: {result.stderr}")
                    return {"success": False, "error": f"FFmpeg error: {result.stderr}"}
                
                # 验证临时输出文件
                if not Path(temp_output).exists():
                    return {"success": False, "error": "Combined video file was not created"}
                
                # 添加背景音乐
                if Path(background_music).exists():
                    print(f"Adding background music: {background_music}")
                    cmd_with_music = [
                        'ffmpeg',
                        '-i', temp_output,
                        '-i', background_music,
                        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:weights=0.7,0.3[out]',
                        '-map', '0:v',
                        '-map', '[out]',
                        '-c:v', 'copy',
                        str(Path(output_file).resolve()),
                        '-y'
                    ]
                    
                    result = subprocess.run(cmd_with_music, capture_output=True, text=True)
                    
                    # 删除临时文件
                    if Path(temp_output).exists():
                        os.remove(temp_output)
                    
                    if result.returncode != 0:
                        print(f"FFmpeg music error: {result.stderr}")
                        return {"success": False, "error": f"FFmpeg music error: {result.stderr}"}
                else:
                    # 如果没有背景音乐文件，直接重命名临时文件
                    print(f"Background music file not found: {background_music}, using video without background music")
                    os.rename(temp_output, output_file)
                
                # 清理临时文件
                for file_path in downloaded_files:
                    if Path(file_path).exists():
                        os.remove(file_path)
                if list_file.exists():
                    os.remove(list_file)
                if temp_dir.exists() and not any(temp_dir.iterdir()):
                    temp_dir.rmdir()
                
                # 获取输出文件的绝对路径
                output_path = Path(output_file).resolve()
                
                return {
                    "success": True,
                    "message": f"Successfully combined {len(videos)} videos",
                    "output_file": str(output_path),
                    "total_duration": len(videos) * 5,
                    "total_shots": len(videos),
                    "file_size": output_path.stat().st_size if output_path.exists() else 0
                }
                
            except Exception as e:
                print(f"FFmpeg error: {str(e)}")
                return {"success": False, "error": f"FFmpeg error: {str(e)}"}
                
    except Exception as e:
        print(f"Proxy combine error: {str(e)}")
        return {"success": False, "error": f"Proxy combine error: {str(e)}"}

# 启动服务器
# ==================== 应用启动配置 ====================

if __name__ == "__main__":
    """
    应用启动入口
    
    当直接运行此文件时，启动FastAPI应用服务器。
    服务器配置：
    - 主机: 0.0.0.0 (允许所有网络接口访问)
    - 端口: 8000
    - 自动重载: 开发模式下启用
    """
    import uvicorn
    print("🚀 启动AI视频生成平台后端服务...")
    print("📍 服务地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("🔧 按 Ctrl+C 停止服务")
    uvicorn.run(app, host="0.0.0.0", port=8000) 

# ==================== 海螺AI语音合成配置 ====================

# 海螺AI语音合成API配置 - 用于文本转语音功能
HAILUO_API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLlrZnplKbmt7siLCJVc2VyTmFtZSI6IuWtmemUpua3uyIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTUxMTE2MDg5NTk3MzcxMDQ0IiwiUGhvbmUiOiIxMzcwMTE2NDgxNiIsIkdyb3VwSUQiOiIxOTUxMTE2MDg5NTg4OTgyNDM2IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMDgtMTEgMTA6MTQ6MDIiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.ce-7TXB4JC9R31woacWZFx_ZChK35h-KpGriEljduvaYg0Ws-1ECVUnI9SCY_9QX6DzHXFbjNsN2cg-WBPPMJPdUoI4Ynf4jx1XXW6IzgIM4swKNfwMWOTCDJ9_VNKvTpUnEDK9gX4mfSFwkdB62zdMOUgDQONh1GditOurfGsT9UMG4w6jczypl7I4PBG4uO5E-vjRuvV9Hr3g9CGXPMk3iJ-A6-3Y5uZMX1XKWo_l5mPxWls_O8YudULhUPeVq8CJSA5lpLAgkcpj6_Nx8827uKbKyjpjJ1CW1oBt3lk5RxR6JgwichJKZnt0oMEkAGW2FMbbJJl3KK4-pKu282w"

def extract_hailuo_group_id_from_token(token):
    """
    从海螺AI JWT token中提取GroupId
    
    海螺AI使用JWT token进行认证，其中包含了GroupId信息。
    此函数解析JWT token的payload部分，提取GroupId用于API调用。
    
    Args:
        token (str): 海螺AI的JWT token
        
    Returns:
        str: 提取到的GroupId，如果提取失败则返回空字符串
        
    Note:
        JWT token由三部分组成：header.payload.signature
        我们只需要解析payload部分来获取GroupId
    """
    try:
        import base64
        # JWT token由三部分组成，用.分隔
        parts = token.split('.')
        if len(parts) == 3:
            # 解码payload部分（第二部分）
            payload = parts[1]
            # 添加padding
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded.decode('utf-8'))
            return payload_data.get('GroupID', '')
    except Exception as e:
        print(f"提取海螺AI GroupId失败: {e}")
    return ''

async def generate_hailuo_audio(text: str, voice_id: str = "male-qn-qingse") -> dict:
    """
    使用海螺AI生成语音文件
    
    此函数调用海螺AI的文本转语音API，将文本内容转换为高质量的语音文件。
    支持多种音色和语音参数配置。
    
    Args:
        text (str): 要转换为语音的文本内容
        voice_id (str): 音色ID，默认为男性青涩音色
        
    Returns:
        dict: 包含生成结果的字典
            {
                "success": bool,           # 是否成功
                "filename": str,           # 生成的音频文件名
                "file_path": str,          # 音频文件完整路径
                "audio_size": int,         # 音频文件大小（字节）
                "audio_hex": str,          # 音频数据的十六进制表示
                "extra_info": dict,        # 额外信息
                "error": str               # 错误信息（如果失败）
            }
            
    Note:
        - 生成的音频文件保存在 audio_files 目录下
        - 文件名格式：hailuo_audio_{timestamp}.mp3
        - 支持MP3格式，采样率32kHz，比特率128kbps
    """
    try:
        # 提取GroupId
        group_id = extract_hailuo_group_id_from_token(HAILUO_API_KEY)
        if not group_id:
            return {"success": False, "error": "无法提取GroupId"}
        
        # API配置
        url = f"https://api.minimaxi.com/v1/t2a_v2?GroupId={group_id}"
        headers = {
            "Authorization": f"Bearer {HAILUO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 请求数据
        data = {
            "model": "speech-2.5-hd-preview",
            "text": text,
            "stream": False,
            "language_boost": "Chinese",
            "output_format": "hex",
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0,
                "emotion": "happy"
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            }
        }
        
        print(f"🎵 海螺AI语音合成: {text[:50]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and 'audio' in result['data']:
                    audio_hex = result['data']['audio']
                    audio_bytes = bytes.fromhex(audio_hex)
                    
                    # 保存音频文件
                    timestamp = int(time.time())
                    filename = f"hailuo_audio_{timestamp}.mp3"
                    
                    # 创建音频目录
                    audio_dir = Path("audio_files")
                    audio_dir.mkdir(exist_ok=True)
                    
                    file_path = audio_dir / filename
                    with open(file_path, 'wb') as f:
                        f.write(audio_bytes)
                    
                    print(f"✅ 海螺AI语音生成成功: {filename}")
                    
                    return {
                        "success": True,
                        "filename": filename,
                        "file_path": str(file_path),
                        "audio_size": len(audio_bytes),
                        "audio_hex": audio_hex,
                        "extra_info": result.get('extra_info', {})
                    }
                else:
                    return {"success": False, "error": "API响应中没有音频数据"}
            else:
                return {"success": False, "error": f"API请求失败: {response.status_code}"}
                
    except Exception as e:
        print(f"❌ 海螺AI语音合成错误: {e}")
        return {"success": False, "error": str(e)}

class AudioFile(Base):
    """音频文件表 - 存储海螺AI生成的语音文件信息"""
    __tablename__ = "audio_files"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)  # 原始文本内容
    voice_id = Column(String, nullable=False)  # 音色ID（如：male-qn-qingse）
    filename = Column(String, nullable=False)  # 生成的音频文件名
    file_path = Column(String, nullable=False)  # 音频文件在服务器上的路径
    audio_size = Column(Integer, nullable=False)  # 音频文件大小（字节）
    status = Column(String, nullable=False)  # 生成状态：success/failed
    error_message = Column(String)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

class AudioGenerationRequest(BaseModel):
    """音频生成请求模型 - 用于接收语音合成请求"""
    text: str  # 要转换为语音的文本内容
    voice_id: str = "male-qn-qingse"  # 音色ID，默认为男性青涩音色

@app.post("/api/audio/generate")
async def generate_audio(data: AudioGenerationRequest):
    """生成语音文件"""
    try:
        # 使用海螺AI生成语音
        result = await generate_hailuo_audio(data.text, data.voice_id)
        
        # 保存到数据库
        async with async_session() as session:
            audio_file = AudioFile(
                text=data.text,
                voice_id=data.voice_id,
                filename=result.get('filename', ''),
                file_path=result.get('file_path', ''),
                audio_size=result.get('audio_size', 0),
                status='success' if result['success'] else 'failed',
                error_message=result.get('error', '')
            )
            
            session.add(audio_file)
            await session.commit()
            await session.refresh(audio_file)
            
            return {
                "success": result['success'],
                "audio_file_id": audio_file.id,
                "filename": result.get('filename', ''),
                "file_path": result.get('file_path', ''),
                "audio_size": result.get('audio_size', 0),
                "error": result.get('error', '')
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/audio/files")
async def list_audio_files():
    """获取所有音频文件列表"""
    async with async_session() as session:
        result = await session.execute(select(AudioFile).order_by(AudioFile.created_at.desc()))
        files = result.scalars().all()
        return [
            {
                "id": f.id,
                "text": f.text,
                "voice_id": f.voice_id,
                "filename": f.filename,
                "file_path": f.file_path,
                "audio_size": f.audio_size,
                "status": f.status,
                "error_message": f.error_message,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in files
        ]

@app.get("/api/audio/files/{file_id}")
async def get_audio_file(file_id: int):
    """获取特定音频文件信息"""
    async with async_session() as session:
        result = await session.execute(select(AudioFile).where(AudioFile.id == file_id))
        audio_file = result.scalar_one_or_none()
        
        if audio_file:
            return {
                "success": True,
                "id": audio_file.id,
                "text": audio_file.text,
                "voice_id": audio_file.voice_id,
                "filename": audio_file.filename,
                "file_path": audio_file.file_path,
                "audio_size": audio_file.audio_size,
                "status": audio_file.status,
                "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None
            }
        else:
            return {"success": False, "error": "音频文件不存在"}

@app.get("/audio/{filename}")
async def serve_audio_file(filename: str):
    """提供音频文件下载"""
    try:
        audio_dir = Path("audio_files")
        file_path = audio_dir / filename
        
        if file_path.exists():
            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        else:
            raise HTTPException(status_code=404, detail="音频文件不存在")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件服务错误: {str(e)}")

# 为对话生成语音
@app.post("/api/audio/generate-for-dialogues")
async def generate_audio_for_dialogues():
    """为所有对话生成语音文件"""
    try:
        async with async_session() as session:
            # 获取最新的对话提取结果
            result = await session.execute(
                select(DialogueExtract).order_by(DialogueExtract.id.desc()).limit(1)
            )
            latest_extract = result.scalar_one_or_none()
            
            if not latest_extract:
                return {"success": False, "error": "没有找到对话提取结果"}
            
            dialogues = json.loads(latest_extract.dialogues)
            print(f"找到 {len(dialogues)} 个对话需要生成语音")
            
            results = []
            for i, dialogue in enumerate(dialogues):
                print(f"正在处理第 {i+1}/{len(dialogues)} 个对话: {dialogue[:50]}...")
                
                # 生成语音
                audio_result = await generate_hailuo_audio(dialogue, "male-qn-qingse")
                
                if audio_result['success']:
                    # 保存到数据库
                    audio_file = AudioFile(
                        text=dialogue,
                        voice_id="male-qn-qingse",
                        filename=audio_result.get('filename', ''),
                        file_path=audio_result.get('file_path', ''),
                        audio_size=audio_result.get('audio_size', 0),
                        status='success',
                        error_message=''
                    )
                    
                    session.add(audio_file)
                    await session.commit()
                    
                    results.append({
                        "dialogue": dialogue,
                        "status": "success",
                        "filename": audio_result.get('filename', ''),
                        "error": ""
                    })
                else:
                    results.append({
                        "dialogue": dialogue,
                        "status": "failed",
                        "filename": "",
                        "error": audio_result.get('error', '生成失败')
                    })
                
                # 等待一下再处理下一个
                await asyncio.sleep(1)
            
            print(f"所有对话语音生成完成，成功: {len([r for r in results if r['status'] == 'success'])}/{len(dialogues)}")
            return {
                "success": True,
                "results": results,
                "total_dialogues": len(dialogues)
            }
            
    except Exception as e:
        print(f"生成对话语音错误: {e}")
        return {"success": False, "error": str(e)}

# ... existing code ... 