"""Session management for tracking user interactions"""
from typing import Dict, Set, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions and interaction tracking"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.greetings_shown: Set[str] = set()
        self.conversation_history: Dict[str, List] = {}
        self.redis_enabled: bool = False
        try:
            from config import settings
            self.redis_enabled = bool(getattr(settings, "USE_REDIS_SESSIONS", False))
            if self.redis_enabled:
                from services.redis_store import redis_store  # noqa
        except Exception:
            self.redis_enabled = False
    
    def should_introduce(self, session_id: str) -> bool:
        """Check if we should introduce ourselves to this session"""
        return session_id not in self.greetings_shown
    
    def mark_introduced(self, session_id: str):
        """Mark that we've introduced ourselves to this session"""
        self.greetings_shown.add(session_id)
        logger.info(f"Marked session {session_id} as introduced")
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history"""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        if not self.redis_enabled:
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            self.conversation_history[session_id].append(entry)
            return
        # Redis-backed
        try:
            import json
            from services.redis_store import redis_store
            key = f"sess:{session_id}:hist"
            current = awaitable_get_json(redis_store, key)
            if current is None:
                data: List[Dict] = [entry]
            else:
                data = json.loads(current)
                data.append(entry)
            # TTL 2 hours
            asyncio_set_json(redis_store, key, json.dumps(data), 7200)
        except Exception:
            # Fallback to memory on error
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            self.conversation_history[session_id].append(entry)
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        if not self.redis_enabled:
            return self.conversation_history.get(session_id, [])
        try:
            import json
            from services.redis_store import redis_store
            # This is a synchronous facade around async get; for simplicity here we skip awaiting in FastAPI request
            data = sync_get_json(redis_store, f"sess:{session_id}:hist")
            return json.loads(data) if data else []
        except Exception:
            return self.conversation_history.get(session_id, [])
    
    def cleanup_old_sessions(self, timeout_minutes: int = 30):
        """Clean up old sessions to prevent memory bloat"""
        # This is a simplified version - in production, track timestamps
        if len(self.sessions) > 100:
            # Keep only the 50 most recent sessions
            sessions_to_keep = list(self.sessions.keys())[-50:]
            self.sessions = {k: v for k, v in self.sessions.items() if k in sessions_to_keep}
            self.greetings_shown = {s for s in self.greetings_shown if s in sessions_to_keep}
            logger.info(f"Cleaned up old sessions, kept {len(self.sessions)}")

    # Future: move to Redis-backed sessions

# Global session manager instance
session_manager = SessionManager()

# Helpers to bridge async redis calls in sync context
def sync_get_json(store, key: str) -> Optional[str]:
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(store.get_json(key))
    except Exception:
        return None

def awaitable_get_json(store, key: str) -> Optional[str]:
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(store.get_json(key))
    except Exception:
        return None

def asyncio_set_json(store, key: str, value: str, ttl: int) -> None:
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(store.set_json(key, value, ttl_seconds=ttl))
    except Exception:
        pass