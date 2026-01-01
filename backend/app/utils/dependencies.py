"""
Authentication and authorization dependencies for FastAPI routes
"""
from fastapi import HTTPException, Header, Request
from typing import Optional
import jwt
from app.utils.auth import decode_access_token
from app.config.database import get_database
from bson import ObjectId
from app.utils.logger import logger


async def get_current_user(request: Request, authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify JWT token and return current user
    
    Args:
        request: FastAPI request object
        authorization: Bearer token from Authorization header
    
    Returns:
        User document from database
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Allow OPTIONS requests (CORS preflight) to pass through
    if request.method == "OPTIONS":
        return {}
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        db = get_database()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def require_admin(request: Request, authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify user is authenticated and has admin role
    
    Args:
        request: FastAPI request object
        authorization: Bearer token from Authorization header
    
    Returns:
        User document from database
    
    Raises:
        HTTPException: If not authenticated or not admin
    """
    # Allow OPTIONS requests (CORS preflight) to pass through
    if request.method == "OPTIONS":
        return {}
    
    user = await get_current_user(request, authorization)
    
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Admin access required. Only administrators can access this resource."
        )
    
    return user
