"""
Rate Limiter for WebSocket connections

Implements token bucket algorithm for rate limiting WebSocket messages.
"""

import time
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket rate limiter implementation.
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens consumed, False if not enough tokens
        """
        # Refill tokens based on time passed
        now = time.time()
        time_passed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + time_passed * self.rate)
        self.last_update = now
        
        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_tokens(self) -> float:
        """Get current number of tokens."""
        now = time.time()
        time_passed = now - self.last_update
        return min(self.capacity, self.tokens + time_passed * self.rate)


class RateLimiter:
    """
    Rate limiter for WebSocket connections.
    """
    
    def __init__(
        self,
        messages_per_minute: int = 20,
        burst_size: int = 5
    ):
        """
        Initialize rate limiter.
        
        Args:
            messages_per_minute: Maximum messages per minute per user
            burst_size: Burst allowance (extra tokens)
        """
        self.messages_per_minute = messages_per_minute
        self.burst_size = burst_size
        
        # Calculate rate in tokens per second
        self.rate = messages_per_minute / 60.0
        self.capacity = burst_size
        
        # Track buckets per user: {user_id: TokenBucket}
        self.buckets: Dict[int, TokenBucket] = {}
        
        logger.info(
            f"RateLimiter initialized: {messages_per_minute} msgs/min, "
            f"burst={burst_size}"
        )
    
    def check_rate_limit(self, user_id: int) -> tuple[bool, float]:
        """
        Check if user can send a message.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (allowed: bool, retry_after: float)
            - allowed: True if message allowed, False if rate limited
            - retry_after: Seconds to wait before retry (0 if allowed)
        """
        # Create bucket for new user
        if user_id not in self.buckets:
            self.buckets[user_id] = TokenBucket(self.rate, self.capacity)
        
        bucket = self.buckets[user_id]
        
        # Try to consume a token
        if bucket.consume(1):
            return True, 0.0
        
        # Calculate retry time
        tokens_needed = 1 - bucket.get_tokens()
        retry_after = tokens_needed / self.rate
        
        logger.warning(
            f"Rate limit exceeded for user {user_id}, "
            f"retry after {retry_after:.1f}s"
        )
        
        return False, retry_after
    
    def reset_user(self, user_id: int):
        """
        Reset rate limit for a user.
        
        Args:
            user_id: User ID
        """
        if user_id in self.buckets:
            del self.buckets[user_id]
            logger.info(f"Rate limit reset for user {user_id}")
    
    def get_stats(self, user_id: int) -> Dict:
        """
        Get rate limit stats for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with stats
        """
        if user_id not in self.buckets:
            return {
                "tokens": self.capacity,
                "capacity": self.capacity,
                "rate": self.messages_per_minute
            }
        
        bucket = self.buckets[user_id]
        return {
            "tokens": bucket.get_tokens(),
            "capacity": self.capacity,
            "rate": self.messages_per_minute
        }


# Global rate limiter instance
rate_limiter = RateLimiter(
    messages_per_minute=20,
    burst_size=5
)
