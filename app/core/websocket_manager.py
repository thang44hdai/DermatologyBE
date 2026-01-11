"""
WebSocket Connection Manager

Manages WebSocket connections with heartbeat, timeout handling, and connection tracking.
"""

import asyncio
import time
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with heartbeat and cleanup.
    """
    
    def __init__(
        self,
        heartbeat_interval: int = 30,  # seconds
        connection_timeout: int = 60,  # seconds
        max_connections_per_user: int = 3
    ):
        """
        Initialize connection manager.
        
        Args:
            heartbeat_interval: Interval between heartbeat pings (seconds)
            connection_timeout: Timeout for inactive connections (seconds)
            max_connections_per_user: Maximum concurrent connections per user
        """
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        self.max_connections_per_user = max_connections_per_user
        
        # Track active connections: {user_id: {websocket: last_activity_time}}
        self.active_connections: Dict[int, Dict[WebSocket, float]] = {}
        
        # Track all websockets to user mapping
        self.websocket_to_user: Dict[WebSocket, int] = {}
        
        logger.info(
            f"ConnectionManager initialized: heartbeat={heartbeat_interval}s, "
            f"timeout={connection_timeout}s, max_per_user={max_connections_per_user}"
        )
    
    async def connect(self, websocket: WebSocket, user_id: int) -> bool:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            
        Returns:
            True if connection accepted, False if rejected (too many connections)
        """
        # Check connection limit
        if user_id in self.active_connections:
            if len(self.active_connections[user_id]) >= self.max_connections_per_user:
                logger.warning(
                    f"Connection limit reached for user {user_id}: "
                    f"{len(self.active_connections[user_id])}/{self.max_connections_per_user}"
                )
                return False
        
        # Initialize user's connection dict if needed
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        # Add connection
        current_time = time.time()
        self.active_connections[user_id][websocket] = current_time
        self.websocket_to_user[websocket] = user_id
        
        logger.info(
            f"WebSocket connected: user_id={user_id}, "
            f"total_connections={len(self.active_connections[user_id])}"
        )
        
        return True
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        user_id = self.websocket_to_user.get(websocket)
        
        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                del self.active_connections[user_id][websocket]
                
                # Clean up empty user dict
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                
                logger.info(f"WebSocket disconnected: user_id={user_id}")
        
        if websocket in self.websocket_to_user:
            del self.websocket_to_user[websocket]
    
    def update_activity(self, websocket: WebSocket):
        """
        Update last activity time for a connection.
        
        Args:
            websocket: WebSocket connection
        """
        user_id = self.websocket_to_user.get(websocket)
        
        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id][websocket] = time.time()
    
    def get_user_connections(self, user_id: int) -> int:
        """
        Get number of active connections for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of active connections
        """
        if user_id in self.active_connections:
            return len(self.active_connections[user_id])
        return 0
    
    def get_total_connections(self) -> int:
        """
        Get total number of active connections.
        
        Returns:
            Total connection count
        """
        return sum(len(conns) for conns in self.active_connections.values())
    
    async def send_heartbeat(self, websocket: WebSocket) -> bool:
        """
        Send heartbeat ping to a connection.
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            True if successful, False if failed
        """
        try:
            await websocket.send_json({"type": "ping"})
            return True
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False
    
    async def cleanup_stale_connections(self):
        """
        Remove connections that haven't responded to heartbeat.
        Should be called periodically.
        """
        current_time = time.time()
        stale_connections = []
        
        for user_id, connections in self.active_connections.items():
            for websocket, last_activity in connections.items():
                if current_time - last_activity > self.connection_timeout:
                    stale_connections.append((websocket, user_id))
        
        # Close stale connections
        for websocket, user_id in stale_connections:
            logger.warning(f"Closing stale connection: user_id={user_id}")
            try:
                await websocket.close(code=1000, reason="Connection timeout")
            except:
                pass
            self.disconnect(websocket)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")
    
    async def heartbeat_task(self):
        """
        Background task to send heartbeats and cleanup stale connections.
        """
        logger.info("Heartbeat task started")
        
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            
            # Send heartbeats to all connections
            all_websockets = list(self.websocket_to_user.keys())
            
            for websocket in all_websockets:
                success = await self.send_heartbeat(websocket)
                if not success:
                    self.disconnect(websocket)
            
            # Cleanup stale connections
            await self.cleanup_stale_connections()
            
            # Log stats
            logger.info(
                f"Heartbeat: {self.get_total_connections()} active connections, "
                f"{len(self.active_connections)} users"
            )


# Global connection manager instance
def get_connection_manager():
    """Get connection manager with settings from environment."""
    from app.config.settings import settings
    return ConnectionManager(
        heartbeat_interval=settings.WS_HEARTBEAT_INTERVAL,
        connection_timeout=settings.WS_CONNECTION_TIMEOUT,
        max_connections_per_user=settings.WS_MAX_CONNECTIONS_PER_USER
    )


connection_manager = get_connection_manager()
