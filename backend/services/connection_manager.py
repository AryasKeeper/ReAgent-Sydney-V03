"""
Connection management service for ReAgent Sydney V03
Handles connection caps, session tracking, and resource cleanup
"""
import asyncio
import time
from typing import Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """Information about an active connection"""
    session_id: str
    user_id: Optional[str]
    start_time: float
    request_id: str
    endpoint: str
    protocol_version: str = "v3"

@dataclass 
class SessionStats:
    """Statistics for a session"""
    active_connections: Set[str] = field(default_factory=set)
    total_connections: int = 0
    last_activity: float = field(default_factory=time.time)
    
class ConnectionManager:
    """
    Manages connection caps and session tracking
    
    Features:
    - Per-session connection limits
    - Global connection limits  
    - Connection cleanup and resource management
    - Session activity tracking
    """
    
    def __init__(
        self,
        max_connections_per_session: int = 5,
        max_global_connections: int = 1000,
        session_timeout_seconds: int = 1800,  # 30 minutes
        cleanup_interval_seconds: int = 300   # 5 minutes
    ):
        self.max_connections_per_session = max_connections_per_session
        self.max_global_connections = max_global_connections
        self.session_timeout_seconds = session_timeout_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        # Connection tracking
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.session_stats: Dict[str, SessionStats] = {}
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the connection manager"""
        if self._running:
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Connection manager started")
    
    async def stop(self):
        """Stop the connection manager"""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Connection manager stopped")
    
    async def acquire_connection(
        self,
        session_id: str,
        request_id: str,
        endpoint: str,
        user_id: Optional[str] = None,
        protocol_version: str = "v3"
    ) -> bool:
        """
        Attempt to acquire a connection slot
        
        Returns:
            True if connection allowed, False if rejected due to limits
        """
        current_time = time.time()
        
        # Check global connection limit
        if len(self.active_connections) >= self.max_global_connections:
            logger.warning(f"Global connection limit reached: {len(self.active_connections)}/{self.max_global_connections}")
            return False
        
        # Get or create session stats
        if session_id not in self.session_stats:
            self.session_stats[session_id] = SessionStats()
        
        session_stats = self.session_stats[session_id]
        
        # Check per-session connection limit
        if len(session_stats.active_connections) >= self.max_connections_per_session:
            logger.warning(f"Session connection limit reached for {session_id}: {len(session_stats.active_connections)}/{self.max_connections_per_session}")
            return False
        
        # Create connection info
        connection_info = ConnectionInfo(
            session_id=session_id,
            user_id=user_id,
            start_time=current_time,
            request_id=request_id,
            endpoint=endpoint,
            protocol_version=protocol_version
        )
        
        # Track connection
        self.active_connections[request_id] = connection_info
        session_stats.active_connections.add(request_id)
        session_stats.total_connections += 1
        session_stats.last_activity = current_time
        
        logger.info(f"Connection acquired: {request_id} for session {session_id} ({len(session_stats.active_connections)}/{self.max_connections_per_session})")
        return True
    
    async def release_connection(self, request_id: str):
        """Release a connection slot"""
        
        if request_id not in self.active_connections:
            logger.warning(f"Attempted to release unknown connection: {request_id}")
            return
        
        connection_info = self.active_connections.pop(request_id)
        session_id = connection_info.session_id
        
        # Update session stats
        if session_id in self.session_stats:
            self.session_stats[session_id].active_connections.discard(request_id)
            self.session_stats[session_id].last_activity = time.time()
        
        duration = time.time() - connection_info.start_time
        logger.info(f"Connection released: {request_id} for session {session_id} (duration: {duration:.2f}s)")
    
    def get_connection_stats(self) -> Dict[str, any]:
        """Get current connection statistics"""
        current_time = time.time()
        
        # Count active sessions (with recent activity)
        active_sessions = 0
        for session_id, stats in self.session_stats.items():
            if current_time - stats.last_activity < self.session_timeout_seconds:
                active_sessions += 1
        
        return {
            "total_active_connections": len(self.active_connections),
            "max_global_connections": self.max_global_connections,
            "active_sessions": active_sessions,
            "max_connections_per_session": self.max_connections_per_session,
            "global_utilization": len(self.active_connections) / self.max_global_connections,
            "session_stats": {
                session_id: {
                    "active_connections": len(stats.active_connections),
                    "total_connections": stats.total_connections,
                    "last_activity": stats.last_activity,
                    "active": current_time - stats.last_activity < self.session_timeout_seconds
                }
                for session_id, stats in self.session_stats.items()
                if current_time - stats.last_activity < self.session_timeout_seconds
            }
        }
    
    def get_session_connections(self, session_id: str) -> int:
        """Get current connection count for a session"""
        if session_id not in self.session_stats:
            return 0
        return len(self.session_stats[session_id].active_connections)
    
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                await self._cleanup_stale_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_stale_sessions(self):
        """Clean up stale sessions and connections"""
        current_time = time.time()
        stale_sessions = []
        stale_connections = []
        
        # Find stale sessions
        for session_id, stats in self.session_stats.items():
            if current_time - stats.last_activity > self.session_timeout_seconds:
                stale_sessions.append(session_id)
                # Mark all connections for this session as stale
                stale_connections.extend(list(stats.active_connections))
        
        # Cleanup stale connections
        for request_id in stale_connections:
            if request_id in self.active_connections:
                logger.info(f"Cleaning up stale connection: {request_id}")
                await self.release_connection(request_id)
        
        # Cleanup stale sessions
        for session_id in stale_sessions:
            logger.info(f"Cleaning up stale session: {session_id}")
            del self.session_stats[session_id]
        
        if stale_sessions:
            logger.info(f"Cleaned up {len(stale_sessions)} stale sessions and {len(stale_connections)} stale connections")

# Global connection manager instance
connection_manager = ConnectionManager()