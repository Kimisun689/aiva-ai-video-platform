"""
Database models and request/response models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from pydantic import BaseModel
from .config import Base

# ==================== User & Authentication Models ====================

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class EmailVerification(Base):
    """Email verification code model"""
    __tablename__ = "email_verifications"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, nullable=False)

# ==================== Video Generation Models ====================

class Prompt(Base):
    """User prompt table - stores user input prompts"""
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String, nullable=False)
    style = Column(String, nullable=False)
    aspect_ratio = Column(String, nullable=False)

class AIScript(Base):
    """AI-generated script table - stores DeepSeek generated scripts"""
    __tablename__ = "ai_scripts"
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer)
    prompt = Column(String, nullable=False)
    style = Column(String, nullable=False)
    aspect_ratio = Column(String, nullable=False)
    script = Column(String, nullable=False)

class ShotBreakdown(Base):
    """Shot breakdown table - stores shot lists"""
    __tablename__ = "shot_breakdowns"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)
    shots = Column(String, nullable=False)

class DialogueExtract(Base):
    """Dialogue extraction table - stores extracted dialogues"""
    __tablename__ = "dialogue_extracts"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)
    dialogues = Column(String, nullable=False)

class CharacterExtract(Base):
    """Character recognition table - stores character info"""
    __tablename__ = "character_extracts"
    id = Column(Integer, primary_key=True, index=True)
    script = Column(String, nullable=False)
    characters = Column(String, nullable=False)

class CharacterImage(Base):
    """Character image table - stores generated character images"""
    __tablename__ = "character_images"
    id = Column(Integer, primary_key=True, index=True)
    character_name = Column(String, nullable=False)
    character_info = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ShotImage(Base):
    """Shot image table - stores generated shot images"""
    __tablename__ = "shot_images"
    id = Column(Integer, primary_key=True, index=True)
    shot_number = Column(Integer, nullable=False)
    shot_content = Column(String, nullable=False)
    style = Column(String, nullable=False)
    aspect_ratio = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class GeneratedVideo(Base):
    """Generated video table - stores generated videos"""
    __tablename__ = "generated_videos"
    id = Column(Integer, primary_key=True, index=True)
    shot_number = Column(Integer, nullable=False)
    shot_content = Column(String, nullable=False)
    style = Column(String, nullable=False)
    aspect_ratio = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    video_url = Column(String, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AudioFile(Base):
    """Audio file table - stores generated audio files"""
    __tablename__ = "audio_files"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    voice_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    audio_size = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== Request Models ====================

class Step1Request(BaseModel):
    """Step 1 request model"""
    prompt: str
    style: str
    aspect_ratio: str

class BreakdownRequest(BaseModel):
    """Breakdown request model"""
    script: str

class BreakdownOnlyRequest(BaseModel):
    """Breakdown only request model"""
    script: str

class DialogueOnlyRequest(BaseModel):
    """Dialogue only request model"""
    script: str

class CharacterOnlyRequest(BaseModel):
    """Character only request model"""
    script: str

class CharacterImageRequest(BaseModel):
    """Character image request model"""
    character_name: str
    character_info: str

class VideoGenerationRequest(BaseModel):
    """Video generation request model"""
    shot: str
    style: str = "Realistic"
    aspect_ratio: str = "16:9"

class ShotVideoGenerationRequest(BaseModel):
    """Shot video generation request model"""
    shot_number: int
    shot_content: str
    style: str = "Realistic"
    aspect_ratio: str = "16:9"

class DigitalHumanVideoRequest(BaseModel):
    """Digital human video request model"""
    character_name: str
    audio_url: str
    image_url: str

class DialogueDigitalHumanRequest(BaseModel):
    """Dialogue digital human request model"""
    character_name: str
    dialogue: str
    voice_id: str = "male-qn-qingse"

class SendCodeRequest(BaseModel):
    """Send code request model"""
    email: str

class RegisterRequest(BaseModel):
    """Register request model"""
    email: str
    username: str
    password: str
    code: str

class LoginRequest(BaseModel):
    """Login request model"""
    username_or_email: str
    password: str

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    username: str
