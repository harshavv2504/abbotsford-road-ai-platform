from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    coffee_style: Optional[str] = None
    current_serving_capacity: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123",
                "name": "John Doe",
                "phone": "+1234567890",
                "country": "USA",
                "city": "New York",
                "coffee_style": "Bold",
                "current_serving_capacity": 100
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "user123",
                    "email": "user@example.com",
                    "name": "John Doe"
                }
            }
        }


class TokenData(BaseModel):
    user_id: str
    email: str
