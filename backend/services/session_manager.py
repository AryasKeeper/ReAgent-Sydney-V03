"""Session management for tracking user interactions"""
from typing import Dict, Set, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions and interaction tracking"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.greetings_shown: Set[str] = set()
        self.conversation_history: Dict[str, List] = {}
    
    def should_introduce(self, session_id: str) -> bool:
        """Check if we should introduce ourselves to this session"""
        return session_id not in self.greetings_shown
    
    def mark_introduced(self, session_id: str):
        """Mark that we've introduced ourselves to this session"""
        self.greetings_shown.add(session_id)
        logger.info(f"Marked session {session_id} as introduced")
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
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

# Global session manager instance
session_manager = SessionManager()