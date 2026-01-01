from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class Message(BaseModel):
    user: Optional[str] = None
    bot: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatConversation(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str
    conversation_id: str
    chat_type: str  # "outbound" or "inbound"
    user_id: Optional[str] = None  # Only for inbound chats
    
    messages: List[Message] = []
    
    status: str = "ongoing"  # "ongoing" or "closed"
    closed_reason: Optional[str] = None  # "user_closed" or "auto_timeout"
    
    summarized: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "conversation_id": "conv_12345",
                "chat_type": "outbound",
                "messages": [
                    {"user": "Hello", "timestamp": "2025-10-17T18:44:21.338Z"},
                    {"bot": "Hi! How can I help?", "timestamp": "2025-10-17T18:44:23.931Z"}
                ]
            }
        }
