from pydantic import BaseModel
from typing import Optional


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    user_id: Optional[str] = None
    country_code: Optional[str] = "US"  # ISO country code for phone validation
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "message": "What are your pricing plans?",
                "country_code": "US"
            }
        }


class ChatMessageResponse(BaseModel):
    response: str
    conversation_id: str
    ended: Optional[bool] = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "We offer three pricing plans...",
                "conversation_id": "conv_12345",
                "ended": False
            }
        }


class TranscribeRequest(BaseModel):
    audio: str  # base64 encoded
    mime_type: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio": "base64_encoded_audio_data",
                "mime_type": "audio/webm"
            }
        }


class TranscribeResponse(BaseModel):
    transcription: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "transcription": "What are your pricing plans?"
            }
        }
