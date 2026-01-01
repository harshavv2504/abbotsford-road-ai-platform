"""
Authentication routes for login, register, and user management
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from datetime import datetime
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.utils.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.config.database import get_database
from app.utils.logger import logger
from typing import Optional
import jwt

router = APIRouter()


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        db = get_database()
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": request.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Create user document
        user_doc = {
            "email": request.email,
            "password": hashed_password,
            "name": request.name,
            "role": "user",
            "created_at": datetime.utcnow(),
            "last_login": None,
            # Additional customer details
            "phone": request.phone,
            "country": request.country,
            "city": request.city,
            "coffee_style": request.coffee_style,
            "current_serving_capacity": request.current_serving_capacity
        }
        
        # Insert user
        result = await db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        # Create access token
        access_token = create_access_token(
            data={"user_id": user_id, "email": request.email}
        )
        
        logger.info(f"New user registered: {request.email}")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user_id,
                "email": request.email,
                "name": request.name,
                "role": "user"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    try:
        db = get_database()
        
        # Find user by email
        user = await db.users.find_one({"email": request.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(request.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Update last login
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create access token
        user_id = str(user["_id"])
        access_token = create_access_token(
            data={"user_id": user_id, "email": user["email"]}
        )
        
        logger.info(f"User logged in: {user['email']}")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user_id,
                "email": user["email"],
                "name": user["name"],
                "role": user.get("role", "user")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout():
    """Logout (client should delete token)"""
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user info from token"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = authorization.split(" ")[1]
        
        # Decode token
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        db = get_database()
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user.get("role", "user")
        }
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
