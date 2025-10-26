"""
API Route Handlers

All API endpoints from the main.py file organized by functionality
"""
import json
import httpx
import secrets
from datetime import datetime, timedelta
from fastapi import FastAPI
from sqlalchemy.future import select
from backend import app, async_session
from backend.auth import verify_password, get_password_hash, create_access_token
from backend.models import *
from backend.services import *

# ==================== Authentication Routes ====================

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

# ==================== Video Generation Routes ====================

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
    """List all AI-generated scripts"""
    async with async_session() as session:
        result = await session.execute(select(AIScript))
        scripts = result.scalars().all()
        return [{
            "id": s.id,
            "prompt": s.prompt,
            "script": s.script,
            "style": s.style,
            "aspect_ratio": s.aspect_ratio
        } for s in scripts]

@app.post("/api/video/breakdown")
async def breakdown_script(data: BreakdownRequest):
    """Break down script into scenes with dialogue"""
    try:
        result = await get_deepseek_breakdown(data.script)
        breakdown = ShotBreakdown(script=data.script, shots=json.dumps(result["shots"], ensure_ascii=False))

        async with async_session() as session:
            session.add(breakdown)
            await session.commit()
            await session.refresh(breakdown)

        dialogues = []
        for shot in result["shots"]:
            if "dialogue" in shot and shot["dialogue"]:
                dialogues.append(shot["dialogue"])

        if dialogues:
            dialogue_extract = DialogueExtract(
                script=data.script,
                dialogues=json.dumps(dialogues, ensure_ascii=False)
            )
            async with async_session() as session:
                session.add(dialogue_extract)
                await session.commit()

        return {
            "success": True,
            "shots": result["shots"],
            "dialogues": dialogues,
            "breakdown_id": breakdown.id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/video/breakdown-shots")
async def breakdown_shots(data: BreakdownOnlyRequest):
    """Break down script into shots only (alternative endpoint)"""
    try:
        result = await get_deepseek_breakdown(data.script)
        shots = result["shots"]
        # Save to database
        async with async_session() as session:
            breakdown = ShotBreakdown(script=data.script, shots=json.dumps(shots, ensure_ascii=False))
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
    """List all character extracts"""
    async with async_session() as session:
        result = await session.execute(select(CharacterExtract))
        extracts = result.scalars().all()
        return [{
            "id": e.id,
            "characters": json.loads(e.characters) if e.characters else []
        } for e in extracts]

@app.get("/api/video/shot-breakdowns")
async def list_shot_breakdowns():
    """List all shot breakdowns"""
    async with async_session() as session:
        result = await session.execute(select(ShotBreakdown))
        breakdowns = result.scalars().all()
        return [{
            "id": b.id,
            "shots": json.loads(b.shots) if b.shots else []
        } for b in breakdowns]

@app.post("/api/video/generate-character-images")
async def generate_character_images():
    """为所有识别出的人物生成白色背景图片"""
    try:
        result = await generate_all_character_images()

        # Check if the operation was actually successful
        if not result.get("success", False):
            # Return 500 Internal Server Error for failures
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=result.get("error", "Character image generation failed"))

        # Check if any characters were successfully generated
        results = result.get("results", [])
        successful_generations = [r for r in results if r.get("status") == "success"]

        if len(successful_generations) == 0 and len(results) > 0:
            # No images were successfully generated, but operation completed
            # Return 500 as this indicates a failure to generate any images
            from fastapi import HTTPException
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate images for {len(results)} characters. Check logs for details."
            )

        return result
    except Exception as e:
        # Return 500 Internal Server Error for any exceptions
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            raise  # Re-raise HTTPExceptions as-is
        raise HTTPException(status_code=500, detail=str(e))

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
                "character_info": json.loads(img.character_info) if img.character_info else {},
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
    """获取最新的人物图片"""
    async with async_session() as session:
        result = await session.execute(
            select(CharacterImage).order_by(CharacterImage.created_at.desc()).limit(10)
        )
        images = result.scalars().all()
        return [
            {
                "id": img.id,
                "character_name": img.character_name,
                "character_info": json.loads(img.character_info) if img.character_info else {},
                "image_url": img.image_url,
                "task_id": img.task_id,
                "status": img.status,
                "error_message": img.error_message,
                "created_at": img.created_at.isoformat() if img.created_at else None
            }
            for img in images
        ]

@app.post("/api/video/shot-images")
async def generate_shot_images():
    """Generate shot images"""
    try:
        # Placeholder implementation
        return {
            "success": True,
            "message": "Shot images generation would happen here"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/video/shot-images")
async def list_shot_images():
    """List shot images"""
    async with async_session() as session:
        result = await session.execute(select(ShotImage))
        images = result.scalars().all()
        return [{
            "id": img.id,
            "shot_number": img.shot_number,
            "shot_content": img.shot_content,
            "image_url": img.image_url,
            "status": img.status
        } for img in images]

@app.get("/api/video/shot-images/latest")
async def get_latest_shot_images():
    """Get latest shot images"""
    async with async_session() as session:
        result = await session.execute(
            select(ShotImage).order_by(ShotImage.created_at.desc()).limit(10)
        )
        images = result.scalars().all()
        return [{
            "id": img.id,
            "shot_number": img.shot_number,
            "shot_content": img.shot_content,
            "image_url": img.image_url,
            "status": img.status
        } for img in images]

@app.post("/api/video/shot-videos")
async def generate_shot_videos():
    """Generate shot videos"""
    try:
        # Placeholder implementation
        return {
            "success": True,
            "message": "Shot videos generation would happen here"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/video/digital-human")
async def generate_digital_human():
    """Generate digital human videos"""
    try:
        # Placeholder implementation
        return {
            "success": True,
            "message": "Digital human generation would happen here"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/video/combine")
async def combine_videos():
    """Combine videos"""
    try:
        # Placeholder implementation
        return {
            "success": True,
            "message": "Video combination would happen here",
            "output_file": "combined_video.mp4"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/video/generate-all-shot-videos")
async def generate_all_shot_videos():
    """Generate all shot videos"""
    try:
        # Placeholder implementation
        return {
            "success": True,
            "message": "All shot videos generation would happen here",
            "results": []
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/video/generated-videos")
async def list_generated_videos():
    """List generated videos"""
    async with async_session() as session:
        result = await session.execute(select(GeneratedVideo))
        videos = result.scalars().all()
        return [{
            "id": v.id,
            "shot_number": v.shot_number,
            "video_url": v.video_url,
            "status": v.status
        } for v in videos]

@app.post("/api/video/generate-shot-images")
async def generate_shot_images_alt():
    """Alternative shot images generation endpoint"""
    try:
        # Placeholder implementation
        return {
            "success": True,
            "message": "Shot images generation (alternative) would happen here"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Additional routes will be added here as they are extracted from main.py
