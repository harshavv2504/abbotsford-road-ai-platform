from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, TranscribeRequest, TranscribeResponse
from app.services.outbound.outbound_bot import outbound_bot
from app.services.stt_service import stt_service
from app.utils.helpers import generate_conversation_id, mask_email, mask_phone
from app.utils.logger import logger
from app.utils.log_capture import capture_logs
from app.config.database import get_database
from app.config.settings import settings

router = APIRouter()


@router.post("/outbound/message", response_model=ChatMessageResponse)
async def outbound_chat(request: ChatMessageRequest):
    """Handle outbound chatbot messages (guest/lead generation)"""
    try:
        db = get_database()
        
        # Find or create conversation
        # First try to find ongoing conversation
        conversation = await db.chat_conversations.find_one({
            "session_id": request.session_id,
            "status": "ongoing"
        })
        
        # If no ongoing conversation, check for recently closed one (within last 5 minutes)
        # This allows users to continue after "should_end" without losing state
        if not conversation:
            from datetime import timedelta
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            conversation = await db.chat_conversations.find_one({
                "session_id": request.session_id,
                "status": "closed",
                "ended_at": {"$gte": five_minutes_ago}
            })
            
            # If found a recent closed conversation, reopen it
            if conversation:
                logger.info(f"Reopening recently closed conversation for session {request.session_id}")
                await db.chat_conversations.update_one(
                    {"_id": conversation["_id"]},
                    {"$set": {"status": "ongoing"}}
                )
        
        if not conversation:
            # Create new conversation
            conversation_id = generate_conversation_id()
            conversation = {
                "session_id": request.session_id,
                "conversation_id": conversation_id,
                "chat_type": "outbound",
                "messages": [],
                "status": "ongoing",
                "summarized": False,
                "created_at": datetime.utcnow(),
                "last_message_at": datetime.utcnow()
            }
            await db.chat_conversations.insert_one(conversation)
        else:
            conversation_id = conversation["conversation_id"]
        
        # Get conversation history
        conversation_history = conversation.get("messages", [])
        conversation_data = conversation.get("data", {})
        
        # Add user message to history
        user_message_obj = {
            "user": request.message,
            "timestamp": datetime.utcnow()
        }
        
        # Process message with outbound bot and capture logs
        with capture_logs() as log_capture:
            bot_result = await outbound_bot.process_message(
                user_message=request.message,
                conversation_history=conversation_history,
                conversation_data=conversation_data,
                country_code=request.country_code
            )
        
        response_text = bot_result["response"]
        should_end = bot_result.get("should_end", False)
        
        # Get captured backend logs as a single string
        backend_logs = log_capture.get_logs_as_string()
        
        # Add bot response to history
        bot_message_obj = {
            "bot": response_text,
            "timestamp": datetime.utcnow()
        }
        
        # Prepare debug info snapshot (masked)
        debug_snapshot = {
            "stage": conversation_data.get("intent_stage"),
            "customer_type": conversation_data.get("customer_type"),
            "is_qualified": conversation_data.get("is_qualified"),
            "collected": {
                "name": bool(conversation_data.get("name")),
                "phone": mask_phone(conversation_data.get("phone")) if conversation_data.get("phone") else None,
                "email": mask_email(conversation_data.get("email")) if conversation_data.get("email") else None,
            },
            "flags": {
                "wants_to_place_order": conversation_data.get("wants_to_place_order"),
                "frustration_detected": conversation_data.get("frustration_detected"),
            }
        }

        # Get existing backend logs and append new ones
        existing_logs = conversation.get("backend_logs", "")
        if existing_logs:
            combined_logs = existing_logs + "\n" + backend_logs
        else:
            combined_logs = backend_logs
        
        # Get API key suffix for tracking
        api_key = settings.OPENAI_API_KEY
        key_suffix = api_key[-8:] if api_key and len(api_key) >= 8 else "unknown"

        # Prepare update data
        update_data = {
            "$push": {
                "messages": {
                    "$each": [user_message_obj, bot_message_obj]
                }
            },
            "$set": {
                "last_message_at": datetime.utcnow(),
                "data": conversation_data,
                "last_debug": debug_snapshot,
                "backend_logs": combined_logs,  # Append logs as string
                "openai_key_suffix": key_suffix
            }
        }
        
        # If chat should end, update status
        if should_end:
            update_data["$set"]["status"] = "closed"
            update_data["$set"]["ended_at"] = datetime.utcnow()
            update_data["$set"]["closed_reason"] = "user_ended"
        
        # Update conversation in database (use conversation_id to handle reopened conversations)
        await db.chat_conversations.update_one(
            {"conversation_id": conversation_id},
            update_data
        )
        # Also keep a rolling debug history (capped to last 50 entries)
        await db.chat_conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$push": {
                    "debug_events": {
                        "$each": [{
                            "ts": datetime.utcnow(),
                            "user": request.message,
                            "bot": response_text,
                            "snapshot": debug_snapshot
                        }],
                        "$slice": -50
                    }
                }
            }
        )
        
        return ChatMessageResponse(
            response=response_text,
            conversation_id=conversation_id,
            ended=should_end
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Error in outbound chat: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inbound/message", response_model=ChatMessageResponse)
async def inbound_chat(request: ChatMessageRequest):
    """Handle inbound chatbot messages (authenticated customer support)"""
    try:
        # Verify user is authenticated
        if not request.user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        
        # Find or create conversation in inbound_conversations collection
        conversation = await db.inbound_conversations.find_one({
            "session_id": request.session_id,
            "user_id": request.user_id,
            "status": "ongoing"
        })
        
        if not conversation:
            # Create new conversation
            conversation_id = generate_conversation_id()
            conversation = {
                "session_id": request.session_id,
                "conversation_id": conversation_id,
                "user_id": request.user_id,
                "chat_type": "inbound",
                "messages": [],
                "status": "ongoing",
                "summarized": False,
                "created_at": datetime.utcnow(),
                "last_message_at": datetime.utcnow(),
                "data": {}
            }
            await db.inbound_conversations.insert_one(conversation)
        else:
            conversation_id = conversation["conversation_id"]
        
        # Get conversation history
        conversation_history = conversation.get("messages", [])
        conversation_data = conversation.get("data", {})
        
        # Add user message to history
        user_message_obj = {
            "user": request.message,
            "timestamp": datetime.utcnow()
        }
        
        # Process message with inbound bot
        from app.services.inbound.inbound_bot import InboundBot
        inbound_bot = InboundBot()
        
        response_text = await inbound_bot.process_message(
            user_message=request.message,
            conversation_history=conversation_history,
            user_id=request.user_id,
            conversation_data=conversation_data
        )
        
        # Add bot response to history
        bot_message_obj = {
            "bot": response_text,
            "timestamp": datetime.utcnow()
        }
        
        # Check if conversation should be closed
        should_close = conversation_data.get("should_close", False)
        
        # Get API key suffix for tracking
        api_key = settings.OPENAI_API_KEY
        key_suffix = api_key[-8:] if api_key and len(api_key) >= 8 else "unknown"

        # Prepare update data
        update_data = {
            "$push": {
                "messages": {
                    "$each": [user_message_obj, bot_message_obj]
                }
            },
            "$set": {
                "last_message_at": datetime.utcnow(),
                "data": conversation_data,
                "openai_key_suffix": key_suffix
            }
        }
        
        # If closing, update status
        if should_close:
            update_data["$set"]["status"] = "closed"
            update_data["$set"]["ended_at"] = datetime.utcnow()
            update_data["$set"]["closed_reason"] = "user_ended"
        
        # Update conversation in inbound_conversations collection
        await db.inbound_conversations.update_one(
            {"session_id": request.session_id, "user_id": request.user_id, "status": "ongoing"},
            update_data
        )
        
        return ChatMessageResponse(
            response=response_text,
            conversation_id=conversation_id,
            ended=should_close
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in inbound chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    """Transcribe audio to text"""
    try:
        transcription = await stt_service.transcribe_audio(
            request.audio,
            request.mime_type
        )
        
        return TranscribeResponse(transcription=transcription)
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
