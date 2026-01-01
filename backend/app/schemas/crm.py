from pydantic import BaseModel
from typing import Optional


class CrmDealCreate(BaseModel):
    company_name: str
    deal_value: float
    contact_person: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    summary: str
    priority: str = "Medium"
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Acme Corp",
                "deal_value": 50000,
                "contact_person": "John Doe",
                "email": "john@acme.com",
                "mobile": "+1-555-0123",
                "summary": "Interested in enterprise plan",
                "priority": "High"
            }
        }


class CrmDealUpdate(BaseModel):
    company_name: Optional[str] = None
    deal_value: Optional[float] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    meeting_notes: Optional[str] = None
    comments: Optional[str] = None


class ConvertLeadRequest(BaseModel):
    lead_id: str
    company_name: str
    deal_value: float = 0
    priority: str = "Medium"
    
    class Config:
        json_schema_extra = {
            "example": {
                "lead_id": "lead_abc123",
                "company_name": "Acme Corp",
                "deal_value": 50000,
                "priority": "High"
            }
        }
