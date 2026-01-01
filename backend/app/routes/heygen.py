"""
HeyGen Avatar API routes
"""
import requests
from fastapi import APIRouter, HTTPException
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter()


@router.post("/token")
async def get_heygen_token():
    """Get HeyGen access token for avatar streaming"""
    try:
        # Get HeyGen API key and avatar ID from settings
        api_key = settings.HEYGEN_API_KEY
        if not api_key:
            raise HTTPException(status_code=500, detail="HeyGen API key not configured")
        
        avatar_id = settings.HEYGEN_AVATAR_ID
        
        # Request token from HeyGen API
        response = requests.post(
            "https://api.heygen.com/v1/streaming.create_token",
            headers={"x-api-key": api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "token": data["data"]["token"],
                "avatarId": avatar_id
            }
        else:
            logger.error(f"HeyGen API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to get HeyGen token")
            
    except Exception as e:
        logger.error(f"Exception in get_heygen_token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))