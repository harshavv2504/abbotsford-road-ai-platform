"""
Authentication utilities for JWT token generation and password hashing
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from app.config.settings import settings
from app.utils.logger import logger

# JWT settings
SECRET_KEY = settings.JWT_SECRET if hasattr(settings, 'JWT_SECRET') else "your-secret-key-change-this-in-production"
ALGORITHM = getattr(settings, 'JWT_ALGORITHM', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, 'JWT_EXPIRATION_MINUTES', 1440)  # 24 hours


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly"""
    # Convert to bytes and truncate to 72 bytes for bcrypt
    password_bytes = password.encode('utf-8')[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly"""
    try:
        # Convert to bytes and truncate to 72 bytes
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing user data (user_id, email)
        expires_delta: Optional custom expiration time
    
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Dictionary containing token payload
    
    Raises:
        jwt.InvalidTokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise
