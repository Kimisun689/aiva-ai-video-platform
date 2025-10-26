"""
Authentication utilities for password hashing and JWT tokens
"""
import time
from jose import jwt
from passlib.context import CryptContext
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, password_hash)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire_ts = int(time.time()) + expires_minutes * 60
    to_encode.update({"exp": expire_ts})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
