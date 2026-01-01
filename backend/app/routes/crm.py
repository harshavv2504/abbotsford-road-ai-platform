"""
CRM routes for managing leads and deals
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from bson import ObjectId
from app.config.database import get_database
from app.utils.logger import logger
from app.utils.dependencies import require_admin

router = APIRouter()


# ============================================
# CHATBOT LEADS ENDPOINTS
# ============================================

@router.get("/leads")
async def get_chatbot_leads(user: dict = Depends(require_admin)):
    """Get all chatbot leads (Admin only)"""
    try:
        db = get_database()
        
        # Get all leads, sorted by created_at descending (newest first)
        leads_cursor = db.chatbot_leads.find().sort("created_at", -1)
        leads = await leads_cursor.to_list(length=1000)
        
        # Convert to frontend format (snake_case → camelCase)
        formatted_leads = []
        for lead in leads:
            formatted_leads.append({
                "id": str(lead["_id"]),
                "date": lead.get("date", lead.get("created_at")).isoformat() if lead.get("date") or lead.get("created_at") else None,
                "userName": lead.get("user_name", ""),
                "mobile": lead.get("mobile", ""),
                "email": lead.get("email", ""),
                "leadScore": lead.get("lead_score", 0),
                "summary": lead.get("summary", ""),
                "conversationHistory": lead.get("conversation_history", [])
            })
        
        logger.info(f"Retrieved {len(formatted_leads)} chatbot leads")
        return formatted_leads
        
    except Exception as e:
        logger.error(f"Error fetching chatbot leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/{lead_id}")
async def get_chatbot_lead(lead_id: str, user: dict = Depends(require_admin)):
    """Get a single chatbot lead by ID (Admin only)"""
    try:
        db = get_database()
        
        lead = await db.chatbot_leads.find_one({"_id": ObjectId(lead_id)})
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Convert to frontend format
        formatted_lead = {
            "id": str(lead["_id"]),
            "date": lead.get("date", lead.get("created_at")).isoformat() if lead.get("date") or lead.get("created_at") else None,
            "userName": lead.get("user_name", ""),
            "mobile": lead.get("mobile", ""),
            "email": lead.get("email", ""),
            "leadScore": lead.get("lead_score", 0),
            "summary": lead.get("summary", ""),
            "conversationHistory": lead.get("conversation_history", []),
            "qualificationData": lead.get("qualification_data", {}),
            "status": lead.get("status", "new")
        }
        
        return formatted_lead
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/leads/{lead_id}")
async def delete_chatbot_lead(lead_id: str, user: dict = Depends(require_admin)):
    """Delete a chatbot lead (Admin only)"""
    try:
        db = get_database()
        
        result = await db.chatbot_leads.delete_one({"_id": ObjectId(lead_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        logger.info(f"Deleted chatbot lead: {lead_id}")
        return {"message": "Lead deleted successfully", "id": lead_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CRM DEALS ENDPOINTS (Placeholder)
# ============================================

@router.get("/deals")
async def get_deals(user: dict = Depends(require_admin)):
    """Get all CRM deals grouped by status (Kanban view) (Admin only)"""
    try:
        db = get_database()
        
        # Get all deals
        deals_cursor = db.crm_deals.find()
        deals = await deals_cursor.to_list(length=1000)
        
        # Group by status for Kanban board
        kanban_data = [
            {"id": "new-lead", "title": "New Lead", "deals": []},
            {"id": "contacted", "title": "Contacted", "deals": []},
            {"id": "proposal-sent", "title": "Proposal Sent", "deals": []},
            {"id": "negotiation", "title": "Negotiation", "deals": []},
            {"id": "won", "title": "Won", "deals": []}
        ]
        
        # Convert and group deals
        for deal in deals:
            formatted_deal = {
                "id": str(deal["_id"]),
                "companyName": deal.get("company_name", ""),
                "dealValue": deal.get("deal_value", 0),
                "contactPerson": deal.get("contact_person", ""),
                "email": deal.get("email", ""),
                "mobile": deal.get("mobile", ""),
                "summary": deal.get("summary", ""),
                "priority": deal.get("priority", "Medium"),
                "meetingNotes": deal.get("meeting_notes", ""),
                "comments": deal.get("comments", "")
            }
            
            # Add to appropriate column
            status = deal.get("status", "new-lead")
            for column in kanban_data:
                if column["id"] == status:
                    column["deals"].append(formatted_deal)
                    break
        
        logger.info(f"Retrieved {len(deals)} CRM deals")
        return kanban_data
        
    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals")
async def create_deal(deal_data: dict, user: dict = Depends(require_admin)):
    """Create a new CRM deal (Admin only)"""
    try:
        db = get_database()
        
        # Convert from camelCase to snake_case
        deal_doc = {
            "company_name": deal_data.get("companyName", ""),
            "deal_value": deal_data.get("dealValue", 0),
            "contact_person": deal_data.get("contactPerson", ""),
            "email": deal_data.get("email", ""),
            "mobile": deal_data.get("mobile", ""),
            "summary": deal_data.get("summary", ""),
            "priority": deal_data.get("priority", "Medium"),
            "status": "new-lead",
            "meeting_notes": deal_data.get("meetingNotes", ""),
            "comments": deal_data.get("comments", ""),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.crm_deals.insert_one(deal_doc)
        
        logger.info(f"Created CRM deal: {result.inserted_id}")
        return {"message": "Deal created successfully", "id": str(result.inserted_id)}
        
    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/deals/{deal_id}")
async def update_deal(deal_id: str, deal_data: dict, user: dict = Depends(require_admin)):
    """Update a CRM deal (Admin only)"""
    try:
        db = get_database()
        
        # Convert from camelCase to snake_case
        update_doc = {
            "$set": {
                "company_name": deal_data.get("companyName"),
                "deal_value": deal_data.get("dealValue"),
                "contact_person": deal_data.get("contactPerson"),
                "email": deal_data.get("email"),
                "mobile": deal_data.get("mobile"),
                "summary": deal_data.get("summary"),
                "priority": deal_data.get("priority"),
                "meeting_notes": deal_data.get("meetingNotes"),
                "comments": deal_data.get("comments"),
                "updated_at": datetime.utcnow()
            }
        }
        
        # Remove None values
        update_doc["$set"] = {k: v for k, v in update_doc["$set"].items() if v is not None}
        
        result = await db.crm_deals.update_one(
            {"_id": ObjectId(deal_id)},
            update_doc
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        logger.info(f"Updated CRM deal: {deal_id}")
        return {"message": "Deal updated successfully", "id": deal_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/deals/{deal_id}/stage")
async def update_deal_stage(deal_id: str, stage_data: dict, user: dict = Depends(require_admin)):
    """Update deal stage (for Kanban drag & drop) (Admin only)"""
    try:
        db = get_database()
        
        new_status = stage_data.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        result = await db.crm_deals.update_one(
            {"_id": ObjectId(deal_id)},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        logger.info(f"Updated deal {deal_id} stage to {new_status}")
        return {"message": "Deal stage updated successfully", "id": deal_id, "status": new_status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating deal stage {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/deals/{deal_id}")
async def delete_deal(deal_id: str, user: dict = Depends(require_admin)):
    """Delete a CRM deal (Admin only)"""
    try:
        db = get_database()
        
        result = await db.crm_deals.delete_one({"_id": ObjectId(deal_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        logger.info(f"Deleted CRM deal: {deal_id}")
        return {"message": "Deal deleted successfully", "id": deal_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
