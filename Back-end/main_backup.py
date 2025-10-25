import httpx
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime
import asyncio
from sqlalchemy.future import select
from fastapi import Body
import json
import re
from datetime import datetime
import aiofiles
import os
import tempfile
import requests
from pathlib import Path
import hashlib
import hmac
import base64
from urllib.parse import quote
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite+aiosqlite:///./prompts.db"
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String, nullable=False)
    style = Column(String, nullable=False)
    aspect_ratio = Column(String, nullable=False)

class Step1Request(BaseModel):
    prompt: str
    style: str
    aspect_ratio: str

class AIScript(Base):
    __tablename__ = "ai_scripts"
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer)  # Reference to Prompt.id
    prompt = Column(String, nullable=False)
    style = Column(String, nullable=False)
    aspect_ratio = Column(String, nullable=False)
    script = Column(String, nullable=False)

class ShotBreakdown(Base):
    __tablename__ = "shot_breakdowns"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)  # 原始 script
    shots = Column(String, nullable=False)   # 用 JSON 字符串存所有分镜

class DialogueExtract(Base):
    __tablename__ = "dialogue_extracts"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)
    dialogues = Column(String, nullable=False)

class CharacterExtract(Base):
    __tablename__ = "character_extracts"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)
    characters = Column(String, nullable=False)  # JSON格式存储人物信息

class CharacterImage(Base):
    __tablename__ = "character_images"
    id = Column(Integer, primary_key=True, index=True)
    character_name = Column(String, nullable=False)
    character_info = Column(String, nullable=False)  # JSON格式存储人物信息
    image_url = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    status = Column(String, nullable=False)  # success/failed
    error_message = Column(String)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

class ShotImage(Base):
    __tablename__ = "shot_images"
    id = Column(Integer, primary_key=True, index=True)
    shot_number = Column(Integer, nullable=False)  # 分镜编号
    shot_content = Column(String, nullable=False)  # 分镜内容
    image_url = Column(String, nullable=False)  # 生成的图片URL
    task_id = Column(String, nullable=False)  # 任务ID
    status = Column(String, nullable=False)  # success/failed
    error_message = Column(String)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

class GeneratedVideo(Base):
    __tablename__ = "generated_videos"
    id = Column(Integer, primary_key=True, index=True)
    shot_number = Column(Integer, nullable=False)  # 分镜编号
    shot_content = Column(String, nullable=False)  # 分镜内容
    style = Column(String, nullable=False)  # 使用的风格
    aspect_ratio = Column(String, nullable=False)  # 使用的比例
    task_id = Column(String, nullable=False)  # ByteDance任务ID
    video_url = Column(String, nullable=False)  # 生成的视频URL
    status = Column(String, nullable=False)  # 状态：success/failed
    error_message = Column(String)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 添加启动事件处理
@app.on_event("shutdown")
async def on_shutdown():
    pass

DEEPSEEK_API_KEY = "sk-eef721b513bc408e9cd14d16e92e5091"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Replace with actual endpoint if different

async def get_deepseek_script(prompt: str) -> str:
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

@app.post("/api/video/step1")
async def video_step1(data: Step1Request):
    # 1. 清空之前的视频数据，确保只合并当前剧本的视频
    async with async_session() as session:
        # 清空generated_videos表
        await session.execute(GeneratedVideo.__table__.delete())
        await session.commit()
        print("🧹 Cleared previous video data for new script")

        # 2. Save user prompt
        new_prompt = Prompt(
            prompt=data.prompt,
            style=data.style,
            aspect_ratio=data.aspect_ratio
        )
        session.add(new_prompt)
        await session.commit()
        await session.refresh(new_prompt)

        # 3. Call DeepSeek AI
        try:
            script = await get_deepseek_script(data.prompt)
        except Exception as e:
            return {"success": False, "error": f"DeepSeek AI error: {str(e)}"}

        # 4. Save AI script
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

        # 5. Return both
        return {
            "success": True,
            "id": new_prompt.id,
            "data": data.dict(),
            "script": script,
            "ai_script_id": ai_script.id,
            "message": "Previous video data cleared for new script"
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
    script: str

async def get_deepseek_breakdown(script: str) -> dict:
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
            
            # 自动开始生成分镜图片
            print(f"分镜拆解完成，开始生成 {len(shots)} 个分镜的图片...")
            
            return {
                "success": True,
                "shots": shots,
                "breakdown_id": breakdown.id,
                "message": f"分镜拆解完成，共 {len(shots)} 个分镜，开始生成图片..."
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

async def generate_shot_image(shot_number: int, shot_content: str) -> dict:
    """为单个分镜生成图片"""
    try:
        # 构建文生图提示词
        prompt = f"电影分镜画面，{shot_content}，高清摄影，电影质感，专业摄影"
        
        print(f"生成分镜图片提示词: {prompt}")
        
        # 使用火山引擎官方SDK
        try:
            from volcengine.visual.VisualService import VisualService
            
            # 初始化视觉服务
            vs = VisualService()
            vs.set_ak(JIMENG_ACCESS_KEY_ID)
            vs.set_sk(JIMENG_SECRET_ACCESS_KEY)
            vs.set_host("visual.volcengineapi.com")
            
            # 构建请求体
            body = {
                "req_key": "jimeng_high_aes_general_v21_L",
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "seed": 42,
                "use_pre_llm": True,
                "use_sr": True,
                "req_json": "{\"logo_info\":{\"add_logo\":false,\"position\":0,\"language\":0,\"opacity\":0.3,\"logo_text_content\":\"\"},\"return_url\":true}"
            }
            
            print(f"调用即梦API生成分镜图片: 分镜 {shot_number}")
            print(f"请求数据: {body}")
            
            # 提交任务
            submit_resp = vs.cv_sync2async_submit_task(body)
            print(f"即梦API提交响应: {submit_resp}")
            
            # 检查submit_resp是否为None
            if submit_resp is None:
                return {
                    "success": False,
                    "error": "API提交任务返回None",
                    "response": None
                }
            
            # 检查submit_resp是否为字典
            if not isinstance(submit_resp, dict):
                return {
                    "success": False,
                    "error": f"API提交任务返回非字典类型: {type(submit_resp)}",
                    "response": submit_resp
                }
            
            if submit_resp.get("code") != 10000:
                error_msg = submit_resp.get('message', 'Unknown error')
                return {
                    "success": False,
                    "error": f"提交失败: {error_msg}",
                    "code": submit_resp.get("code")
                }
            
            task_id = submit_resp.get("data", {}).get("task_id")
            if not task_id:
                return {"success": False, "error": "未收到task_id"}
            
            # 轮询查询结果
            for i in range(30):  # 最多查30次
                result = vs.cv_sync2async_get_result({
                    "task_id": task_id,
                    "req_key": "jimeng_high_aes_general_v21_L"
                })
                print(f"即梦API查询 {i+1}: {result}")
                
                # 检查result是否为None
                if result is None:
                    print(f"API查询返回None，等待后重试...")
                    await asyncio.sleep(5)
                    continue
                
                # 检查result是否为字典
                if not isinstance(result, dict):
                    print(f"API查询返回非字典类型: {type(result)}, 值: {result}")
                    await asyncio.sleep(5)
                    continue
                
                status = result.get("data", {}).get("status")
                if status == "done" or status == 2:  # 成功
                    image_url = result["data"].get("image_url")
                    if image_url:
                        return {
                            "success": True,
                            "task_id": task_id,
                            "image_url": image_url,
                            "shot_number": shot_number
                        }
                    else:
                        return {"success": False, "error": "API响应中没有图片URL"}
                elif status == "failed" or status == 3:  # 失败
                    return {"success": False, "error": "图片生成失败"}
                else:
                    await asyncio.sleep(5)
            
            return {"success": False, "error": "查询超时"}
            
        except ImportError:
            return {"success": False, "error": "volcengine SDK未安装"}
        except Exception as e:
            return {"success": False, "error": f"API调用失败: {str(e)}"}
            
    except Exception as e:
        return {"success": False, "error": f"生成分镜图片错误: {str(e)}"}

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
        prompt = f"一个{age_cn}的{gender_cn}，{appearance}，{personality}，白色背景，高清照片，正面角度，自然表情，专业人像摄影"
        
        print(f"生成人物图片提示词: {prompt}")
        
        # 使用火山引擎官方SDK
        try:
            from volcengine.visual.VisualService import VisualService
            
            # 初始化视觉服务
            vs = VisualService()
            vs.set_ak(JIMENG_ACCESS_KEY_ID)
            vs.set_sk(JIMENG_SECRET_ACCESS_KEY)
            vs.set_host("visual.volcengineapi.com")
            
            # 构建请求体 - 根据火山引擎技术支持解决方案
            body = {
                "req_key": "jimeng_high_aes_general_v21_L",
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "seed": 42,
                "use_pre_llm": True,
                "use_sr": True,
                "req_json": "{\"logo_info\":{\"add_logo\":false,\"position\":0,\"language\":0,\"opacity\":0.3,\"logo_text_content\":\"\"},\"return_url\":true}"
            }
            
            print(f"调用即梦API: 使用官方SDK")
            print(f"请求数据: {body}")
            
            # 提交任务
            submit_resp = vs.cv_sync2async_submit_task(body)
            print(f"即梦API提交响应: {submit_resp}")
            
            # 检查submit_resp是否为None
            if submit_resp is None:
                return {
                    "success": False,
                    "error": "API提交任务返回None",
                    "response": None
                }
            
            # 检查submit_resp是否为字典
            if not isinstance(submit_resp, dict):
                return {
                    "success": False,
                    "error": f"API提交任务返回非字典类型: {type(submit_resp)}",
                    "response": submit_resp
                }
            
            if submit_resp.get("code") != 10000:
                error_msg = submit_resp.get('message', 'Unknown error')
                return {
                    "success": False,
                    "error": f"提交失败: {error_msg}",
                    "code": submit_resp.get("code")
                }
            
            task_id = submit_resp.get("data", {}).get("task_id")
            if not task_id:
                return {"success": False, "error": "未收到task_id"}
            
            # 轮询查询结果
            for i in range(30):  # 最多查30次
                result = vs.cv_sync2async_get_result({
                    "task_id": task_id,
                    "req_key": "jimeng_high_aes_general_v21_L"
                })
                print(f"即梦API查询 {i+1}: {result}")
                
                # 检查result是否为None
                if result is None:
                    print(f"API查询返回None，等待后重试...")
                    await asyncio.sleep(5)
                    continue
                
                # 检查result是否为字典
                if not isinstance(result, dict):
                    print(f"API查询返回非字典类型: {type(result)}, 值: {result}")
                    await asyncio.sleep(5)
                    continue
                
                status = result.get("data", {}).get("status")
                if status == "done" or status == 2:  # 成功
                    data = result.get("data", {})
                    if data and "image_urls" in data and data["image_urls"]:
                        image_url = data["image_urls"][0]
                        if image_url:
                            return {
                                "success": True,
                                "image_url": image_url,
                                "task_id": task_id,
                                "prompt": prompt
                            }
                        else:
                            return {
                                "success": False,
                                "error": "API响应中图片URL为空",
                                "response": result
                            }
                    else:
                        return {
                            "success": False,
                            "error": "API响应中没有图片URL",
                            "response": result
                        }
                elif status == "failed" or status == 3:  # 失败
                    return {
                        "success": False,
                        "error": "图片生成失败",
                        "response": result
                    }
                else:
                    # 还在生成中，等待5秒
                    await asyncio.sleep(5)
            
            return {"success": False, "error": "生成超时"}
            
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
    """为所有分镜生成图片"""
    try:
        # 获取最新的分镜数据
        async with async_session() as session:
            result = await session.execute(
                select(ShotBreakdown).order_by(ShotBreakdown.id.desc()).limit(1)
            )
            breakdown = result.scalar_one_or_none()
            
            if not breakdown:
                return {"success": False, "error": "未找到分镜数据"}
            
            shots = json.loads(breakdown.shots)
            print(f"找到 {len(shots)} 个分镜需要生成图片")
            
            # 检查是否已经有成功的图片
            for i, shot in enumerate(shots, 1):
                existing_result = await session.execute(
                    select(ShotImage).where(
                        ShotImage.shot_number == i,
                        ShotImage.status == "success"
                    ).order_by(ShotImage.id.desc()).limit(1)
                )
                existing = existing_result.scalar_one_or_none()
                
                if existing:
                    print(f"分镜 {i} 已有成功图片，跳过")
                    continue
                
                print(f"正在处理第 {i}/{len(shots)} 个分镜: {shot[:50]}...")
                
                # 生成图片
                image_result = await generate_shot_image(i, shot)
                
                # 保存到数据库
                shot_image = ShotImage(
                    shot_number=i,
                    shot_content=shot,
                    image_url=image_result.get("image_url", ""),
                    task_id=image_result.get("task_id", ""),
                    status="success" if image_result["success"] else "failed",
                    error_message=image_result.get("error", "")
                )
                
                session.add(shot_image)
                await session.commit()
                
                if image_result["success"]:
                    print(f"✅ 分镜 {i} 图片生成成功")
                else:
                    print(f"❌ 分镜 {i} 图片生成失败: {image_result.get('error')}")
                
                # 等待5秒再生成下一个
                if i < len(shots):
                    print("等待5秒后生成下一个分镜图片...")
                    await asyncio.sleep(5)
            
            # 统计结果
            success_count = await session.execute(
                select(ShotImage).where(ShotImage.status == "success")
            )
            success_images = success_count.scalars().all()
            
            return {
                "success": True,
                "total_shots": len(shots),
                "success_count": len(success_images),
                "message": f"分镜图片生成完成，成功: {len(success_images)}/{len(shots)}"
            }
            
    except Exception as e:
        return {"success": False, "error": f"生成分镜图片错误: {str(e)}"}

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

@app.post("/api/video/generate-shot-images")
async def generate_shot_images():
    """为所有分镜生成图片"""
    try:
        result = await generate_all_shot_images()
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
                "image_url": img.image_url,
                "task_id": img.task_id,
                "status": img.status,
                "error_message": img.error_message,
                "created_at": img.created_at.isoformat() if img.created_at else None
            }
            for img in images
        ]

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
        
        # 获取每个分镜的最新图片
        latest_images = []
        for i, shot in enumerate(shots, 1):
            result = await session.execute(
                select(ShotImage)
                .where(ShotImage.shot_number == i)
                .order_by(ShotImage.id.desc())
                .limit(1)
            )
            latest_image = result.scalar_one_or_none()
            
            if latest_image:
                latest_images.append({
                    "shot_number": i,
                    "shot_content": shot,
                    "status": latest_image.status,
                    "image_url": latest_image.image_url,
                    "error_message": latest_image.error_message,
                    "created_at": latest_image.created_at.isoformat() if latest_image.created_at else None
                })
            else:
                latest_images.append({
                    "shot_number": i,
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
            "total_shots": len(shots),
            "completed": len([img for img in latest_images if img['status'] == 'success']),
            "failed": len([img for img in latest_images if img['status'] == 'failed']),
            "pending": len([img for img in latest_images if img['status'] == 'not_started'])
        }

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

# ByteDance 即梦AI API 配置
BYTEDANCE_ACCESS_KEY_ID = "AKLTMTE0YWY5OTI3YThjNDNiMDlmNGRmNWY5YWY1Y2M5MDI"
BYTEDANCE_SECRET_ACCESS_KEY = "WlRobU9UaGlPREl6WlRNMk5HVmlZV0prWlRGa01tTXhOR1JsTURZNFpHRQ=="

# 即梦文生图API 配置
JIMENG_ACCESS_KEY_ID = "AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU"
JIMENG_SECRET_ACCESS_KEY = "TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ=="

def generate_volc_signature(access_key_id, secret_access_key, http_method, canonical_uri, canonical_querystring, canonical_headers, signed_headers, payload_hash):
    """生成火山引擎API签名 - 基于官方文档"""
    # 1. 创建规范请求
    canonical_request = http_method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
    
    # 2. 创建待签名字符串
    algorithm = 'HMAC-SHA256'
    timestamp = str(int(datetime.utcnow().timestamp()))
    date = datetime.utcnow().strftime('%Y%m%d')
    credential_scope = date + '/cn-north-1/cv/aws4_request'
    
    string_to_sign = algorithm + '\n' + timestamp + '\n' + credential_scope + '\n' + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    
    # 3. 计算签名 - 使用火山引擎的方式
    k_date = hmac.new(('AWS4' + secret_access_key).encode('utf-8'), date.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, 'cn-north-1'.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, 'cv'.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, 'aws4_request'.encode('utf-8'), hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 4. 创建授权头
    authorization_header = algorithm + ' ' + 'Credential=' + access_key_id + '/' + credential_scope + ', ' + 'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
    
    return authorization_header, timestamp

# 导入字节AI SDK
try:
    from volcengine.visual.VisualService import VisualService
    BYTEDANCE_AVAILABLE = True
except ImportError:
    BYTEDANCE_AVAILABLE = False
    print("Warning: volcengine SDK not installed. ByteDance AI features will be disabled.")

class VideoGenerationRequest(BaseModel):
    shot: str
    style: str = "Realistic"  # 默认风格
    aspect_ratio: str = "16:9"  # 默认比例

async def generate_bytedance_video(shot: str, style: str = "Realistic", aspect_ratio: str = "16:9"):
    """使用字节即梦AI生成视频"""
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

@app.post("/api/video/generate-video")
async def generate_video(data: VideoGenerationRequest):
    """生成单个分镜的视频"""
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
                output_file = temp_dir / "combined_video.mp4"
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0', 
                    '-i', str(list_file), '-c', 'copy', str(output_file)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"FFmpeg error: {result.stderr}")
                    return {"success": False, "error": f"FFmpeg error: {result.stderr}"}
                
                # 检查输出文件是否存在
                if not output_file.exists():
                    return {"success": False, "error": "Combined video file not created"}
                
                # 返回合并后的视频文件路径
                return {
                    "success": True,
                    "message": f"Successfully combined {len(videos)} videos",
                    "total_shots": len(videos),
                    "total_duration": len(videos) * 5,
                    "combined_video_path": str(output_file),
                    "file_size": output_file.stat().st_size
                }
                
            except Exception as e:
                print(f"Video combination error: {str(e)}")
                return {"success": False, "error": f"Video combination error: {str(e)}"}
            
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
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0', 
                    '-i', str(list_file), '-c', 'copy', str(Path(output_file).resolve()), '-y'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"FFmpeg error: {result.stderr}")
                    return {"success": False, "error": f"FFmpeg error: {result.stderr}"}
                
                # 验证输出文件
                if not Path(output_file).exists():
                    return {"success": False, "error": "Combined video file was not created"}
                
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
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 

# 海螺AI语音合成API配置
HAILUO_API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLlrZnplKbmt7siLCJVc2VyTmFtZSI6IuWtmemUpua3uyIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTUxMTE2MDg5NTk3MzcxMDQ0IiwiUGhvbmUiOiIxMzcwMTE2NDgxNiIsIkdyb3VwSUQiOiIxOTUxMTE2MDg5NTg4OTgyNDM2IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMDgtMTEgMTA6MTQ6MDIiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.ce-7TXB4JC9R31woacWZFx_ZChK35h-KpGriEljduvaYg0Ws-1ECVUnI9SCY_9QX6DzHXFbjNsN2cg-WBPPMJPdUoI4Ynf4jx1XXW6IzgIM4swKNfwMWOTCDJ9_VNKvTpUnEDK9gX4mfSFwkdB62zdMOUgDQONh1GditOurfGsT9UMG4w6jczypl7I4PBG4uO5E-vjRuvV9Hr3g9CGXPMk3iJ-A6-3Y5uZMX1XKWo_l5mPxWls_O8YudULhUPeVq8CJSA5lpLAgkcpj6_Nx8827uKbKyjpjJ1CW1oBt3lk5RxR6JgwichJKZnt0oMEkAGW2FMbbJJl3KK4-pKu282w"

def extract_hailuo_group_id_from_token(token):
    """从海螺AI JWT token中提取GroupId"""
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
    """使用海螺AI生成语音"""
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

# 语音合成相关的数据库模型
class AudioFile(Base):
    __tablename__ = "audio_files"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)  # 原始文本
    voice_id = Column(String, nullable=False)  # 音色ID
    filename = Column(String, nullable=False)  # 文件名
    file_path = Column(String, nullable=False)  # 文件路径
    audio_size = Column(Integer, nullable=False)  # 文件大小
    status = Column(String, nullable=False)  # success/failed
    error_message = Column(String)  # 错误信息
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

# 语音合成请求模型
class AudioGenerationRequest(BaseModel):
    text: str
    voice_id: str = "male-qn-qingse"

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