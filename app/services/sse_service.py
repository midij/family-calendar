"""
Server-Sent Events (SSE) service for real-time updates.
Manages client connections and broadcasts version updates.
"""
import asyncio
import json
from typing import Set, Dict, Any
from fastapi import Request
from fastapi.responses import StreamingResponse
from app.services.version_service import VersionService


class SSEService:
    """Service for managing SSE connections and broadcasting updates"""
    
    _connections: Set[asyncio.Queue] = set()
    _lock = asyncio.Lock()
    
    @classmethod
    async def add_connection(cls, queue: asyncio.Queue):
        """Add a new SSE connection"""
        async with cls._lock:
            cls._connections.add(queue)
    
    @classmethod
    async def remove_connection(cls, queue: asyncio.Queue):
        """Remove an SSE connection"""
        async with cls._lock:
            cls._connections.discard(queue)
    
    @classmethod
    async def broadcast_update(cls, version_info: Dict[str, Any]):
        """Broadcast version update to all connected clients"""
        message = f"data: {json.dumps(version_info)}\n\n"
        
        async with cls._lock:
            # Create a copy of connections to avoid modification during iteration
            connections_to_remove = set()
            
            for queue in cls._connections.copy():
                try:
                    await queue.put(message)
                except Exception:
                    # Connection is broken, mark for removal
                    connections_to_remove.add(queue)
            
            # Remove broken connections
            cls._connections -= connections_to_remove
    
    @classmethod
    async def get_connection_count(cls) -> int:
        """Get the number of active connections"""
        async with cls._lock:
            return len(cls._connections)
    
    @classmethod
    async def create_sse_stream(cls, request: Request) -> StreamingResponse:
        """Create an SSE stream for a client"""
        async def event_generator():
            # Create a queue for this connection
            queue = asyncio.Queue()
            
            try:
                # Add connection
                await cls.add_connection(queue)
                
                # Send initial version info
                initial_version = VersionService.get_version_info()
                yield f"data: {json.dumps(initial_version)}\n\n"
                
                # Keep connection alive and send updates
                while True:
                    # Check if client disconnected
                    if await request.is_disconnected():
                        break
                    
                    try:
                        # Wait for updates with timeout
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield message
                    except asyncio.TimeoutError:
                        # Send heartbeat to keep connection alive
                        heartbeat = {
                            "type": "heartbeat",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        yield f"data: {json.dumps(heartbeat)}\n\n"
                    except Exception as e:
                        # Connection error, break the loop
                        break
                        
            finally:
                # Remove connection when done
                await cls.remove_connection(queue)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )


# Import datetime here to avoid circular imports
from datetime import datetime, timezone

