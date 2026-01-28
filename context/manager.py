import json
import os
from typing import List, Dict, Any, Optional
import redis

class ContextManager:
    """
    Manages the context window for Nakari sessions using Redis for storage.
    Follows the strategy: Retrieval -> Assembly -> Compression.
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        # Use a separate Redis connection for context if needed, or share. 
        # Here we assume a standard Redis connection.
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        self.context_ttl = 3600 * 24  # 24 hours context retention for active caching
        self.max_history_len = 50     # Max messages before compression/truncation

    def _get_key(self, session_id: str) -> str:
        return f"nakari:context:{session_id}"

    def get_context(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the current context window for a session.
        """
        key = self._get_key(session_id)
        raw_data = self.redis.lrange(key, 0, -1)
        # Redis stores oldest first if we rpush, or newest first if we lpush.
        # Let's assume standard appending: RPUSH (new at end).
        # We process simple string JSONs.
        return [json.loads(msg) for msg in raw_data]

    def add_message(self, session_id: str, role: str, content: str, meta: Dict = None):
        """
        Adds a new message to the context window.
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": "TODO: timestamp", # Add real timestamp
            "meta": meta or {}
        }
        
        key = self._get_key(session_id)
        self.redis.rpush(key, json.dumps(message))
        self.redis.expire(key, self.context_ttl) # Refresh TTL
        
        # Check if compression is needed
        current_len = self.redis.llen(key)
        if current_len > self.max_history_len:
            self.compress_context(session_id)

    def save_insight(self, session_id: str, insight: str):
        """
        Stores a high-level reflection insight.
        For now, we store this in a separate Redis list 'nakari:insights:{session_id}'
        """
        key = f"nakari:insights:{session_id}"
        self.redis.rpush(key, insight)
        # Insights should last longer, maybe forever, but let's set a long TTL
        self.redis.expire(key, 3600 * 24 * 30) 

    def get_insights(self, session_id: str, limit: int = 3) -> List[str]:
        """
        Retrieves the most recent insights.
        """
        key = f"nakari:insights:{session_id}"
        # Get last 'limit' items
        return self.redis.lrange(key, -limit, -1)

    def compress_context(self, session_id: str):
        """
        Compresses the context window when it exceeds the limit.
        Strategy: Keep first system prompt (if any), summarize middle, keep last N.
        For now: Simple truncation (FIFO).
        """
        # TODO: Implement "Summary" strategy as per README using LLM
        # Current simplified implementation: Pop the oldest user/assistant exchanges
        # Keep distinct system prompt if we had one (not handled here specifically yet)
        key = self._get_key(session_id)
        while self.redis.llen(key) > self.max_history_len:
            self.redis.lpop(key)

    def set_active_persona(self, session_id: str, persona_name: str):
        """
        Sets the active persona for a session.
        """
        key = f"nakari:persona:{session_id}"
        self.redis.set(key, persona_name)
    
    def get_active_persona(self, session_id: str) -> str:
        """
        Gets the active persona name for a session. Defaults to 'default'.
        """
        key = f"nakari:persona:{session_id}"
        name = self.redis.get(key)
        return name if name else "default"

    def get_persona_template(self, name: str) -> Optional[Dict]:
        """
        Retrieves a persona template from Redis cache.
        """
        key = f"nakari:persona_template:{name}"
        data = self.redis.get(key)
        try:
            return json.loads(data) if data else None
        except json.JSONDecodeError:
            self.redis.delete(key)
            return None

    def set_persona_template(self, name: str, data: Dict):
        """
        Caches a persona template in Redis for unified management.
        TTL: 24 hours (or update manually).
        """
        key = f"nakari:persona_template:{name}"
        self.redis.set(key, json.dumps(data), ex=3600*24)

    def clear_context(self, session_id: str):
        key = self._get_key(session_id)
        self.redis.delete(key)

# Singleton or factory
context_manager = ContextManager()
