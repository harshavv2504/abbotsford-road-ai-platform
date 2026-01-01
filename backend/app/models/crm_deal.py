from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class CrmDeal(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    company_name: str
    deal_value: float
    contact_person: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    summary: str
    priority: str  # "Low", "Medium", "High"
    status: str = "new-lead"  # "new-lead", "contacted", "proposal-sent", "negotiation", "won"
    meeting_notes: Optional[str] = None
    comments: Optional[str] = None
    
    # Optional: track if converted from chatbot lead
    source_conversation_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "company_name": "Acme Corp",
                "deal_value": 50000,
                "contact_person": "John Doe",
                "email": "john@acme.com",
                "mobile": "+1-555-0123",
                "summary": "Interested in enterprise plan",
                "priority": "High",
                "status": "new-lead"
            }
        }
