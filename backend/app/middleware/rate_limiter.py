"""
Rate Limiting Middleware for Outbound Bot

Implements token bucket algorithm for rate limiting:
- Per-user rate limiting based on session ID
- Configurable limits for different endpoints
- Automatic cleanup of old buckets
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app.utils.logger import logger


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    capacity: int  # Maximum tokens
    tokens: float  # Current tokens
    refill_rate: float  # Tokens per second
    last_refill: float = field(default_factory=time.time)
    
    def refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens
        
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        self.refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get time to wait until tokens are available
        
        Returns:
            Seconds to wait
        """
        self.refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # Cleanup every hour
        
        # Rate limit configurations
        self.configs = {
            "outbound_message": {
                "capacity": 20,  # 20 messages
                "refill_rate": 0.33,  # ~20 messages per minute (1 every 3 seconds)
            },
            "outbound_message_burst": {
                "capacity": 5,  # 5 messages
                "refill_rate": 0.083,  # ~5 messages per minute (1 every 12 seconds)
            },
            "rag_question": {
                "capacity": 10,  # 10 questions
                "refill_rate": 0.17,  # ~10 questions per minute
            }
        }
    
    def _get_bucket_key(self, user_id: str, endpoint: str) -> str:
        """Generate bucket key from user ID and endpoint"""
        return f"{user_id}:{endpoint}"
    
    def _get_or_create_bucket(self, user_id: str, endpoint: str) -> TokenBucket:
        """Get existing bucket or create new one"""
        key = self._get_bucket_key(user_id, endpoint)
        
        if key not in self.buckets:
            config = self.configs.get(endpoint, self.configs["outbound_message"])
            self.buckets[key] = TokenBucket(
                capacity=config["capacity"],
                tokens=config["capacity"],  # Start with full bucket
                refill_rate=config["refill_rate"]
            )
        
        return self.buckets[key]
    
    def _cleanup_old_buckets(self):
        """Remove buckets that haven't been used in a while"""
        now = time.time()
        
        # Only cleanup every hour
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove buckets older than 1 hour
        max_age = 3600
        keys_to_remove = []
        
        for key, bucket in self.buckets.items():
            if now - bucket.last_refill > max_age:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.buckets[key]
        
        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} old rate limit buckets")
        
        self.last_cleanup = now
    
    def check_rate_limit(
        self,
        user_id: str,
        endpoint: str = "outbound_message",
        tokens: int = 1
    ) -> Dict:
        """
        Check if request is within rate limit
        
        Args:
            user_id: User/session identifier
            endpoint: Endpoint being accessed
            tokens: Number of tokens to consume
        
        Returns:
            Dict with:
                - allowed: bool - Whether request is allowed
                - wait_time: float - Seconds to wait if not allowed
                - remaining: int - Remaining tokens
        """
        # Cleanup old buckets periodically
        self._cleanup_old_buckets()
        
        # Get or create bucket
        bucket = self._get_or_create_bucket(user_id, endpoint)
        
        # Try to consume tokens
        allowed = bucket.consume(tokens)
        
        result = {
            "allowed": allowed,
            "wait_time": 0.0 if allowed else bucket.get_wait_time(tokens),
            "remaining": int(bucket.tokens),
            "limit": bucket.capacity
        }
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for user {user_id} on {endpoint}. "
                f"Wait time: {result['wait_time']:.1f}s"
            )
        
        return result
    
    def get_rate_limit_info(self, user_id: str, endpoint: str = "outbound_message") -> Dict:
        """
        Get current rate limit info without consuming tokens
        
        Returns:
            Dict with remaining tokens and limit
        """
        bucket = self._get_or_create_bucket(user_id, endpoint)
        bucket.refill()
        
        return {
            "remaining": int(bucket.tokens),
            "limit": bucket.capacity,
            "refill_rate": bucket.refill_rate
        }
    
    def reset_user_limits(self, user_id: str):
        """Reset all rate limits for a user"""
        keys_to_remove = [key for key in self.buckets.keys() if key.startswith(f"{user_id}:")]
        
        for key in keys_to_remove:
            del self.buckets[key]
        
        logger.info(f"Reset rate limits for user {user_id}")


# Singleton instance
rate_limiter = RateLimiter()


# FastAPI dependency for rate limiting
def check_outbound_rate_limit(session_id: str) -> Dict:
    """
    FastAPI dependency to check rate limit for outbound messages
    
    Usage:
        @app.post("/api/outbound/message")
        async def send_message(
            request: MessageRequest,
            rate_limit: Dict = Depends(check_outbound_rate_limit)
        ):
            if not rate_limit["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {rate_limit['wait_time']:.0f} seconds."
                )
    """
    return rate_limiter.check_rate_limit(session_id, "outbound_message")
