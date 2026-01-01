"""
User service for fetching customer details in inbound chatbot
"""
from typing import Dict, Optional
from bson import ObjectId
from app.config.database import get_database
from app.utils.logger import logger


class UserService:
    """Service for fetching user/customer details"""
    
    async def get_user_details(self, user_id: str) -> Optional[Dict]:
        """
        Fetch user details from database
        
        Args:
            user_id: MongoDB ObjectId as string
        
        Returns:
            Dictionary with user details or None if not found
        """
        try:
            db = get_database()
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                logger.warning(f"User not found: {user_id}")
                return None
            
            # Format user details for bot context
            return {
                "name": user.get("name", "Customer"),
                "email": user.get("email", ""),
                "role": user.get("role", "user"),
                "customer_since": user.get("created_at"),
                "last_login": user.get("last_login"),
                # Additional customer details
                "phone": user.get("phone"),
                "country": user.get("country"),
                "city": user.get("city"),
                "coffee_style": user.get("coffee_style"),
                "current_serving_capacity": user.get("current_serving_capacity")
            }
            
        except Exception as e:
            logger.error(f"Error fetching user details: {e}")
            return None


# Singleton instance
user_service = UserService()
