from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from app.core.database import get_db
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to specific client: {e}")


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial connection success message
        await manager.send_to_client(websocket, {
            "type": "connection",
            "status": "connected",
            "message": "Connected to CCTV monitoring system"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await manager.send_to_client(websocket, {
                    "type": "pong",
                    "timestamp": str(json.dumps({"time": "now"}))
                })
            else:
                # Echo back for testing
                await manager.send_to_client(websocket, {
                    "type": "echo",
                    "data": data
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_alert(alert_data: dict):
    """
    Broadcast alert to all connected clients
    Called by alert service when new alert is created
    """
    message = {
        "type": "alert",
        "data": alert_data
    }
    await manager.broadcast(message)


async def broadcast_detection(detection_data: dict):
    """
    Broadcast detection to all connected clients
    Called by detection service for real-time updates
    """
    message = {
        "type": "detection",
        "data": detection_data
    }
    await manager.broadcast(message)


async def broadcast_camera_status(camera_id: int, status: str):
    """
    Broadcast camera status change
    """
    message = {
        "type": "camera_status",
        "data": {
            "camera_id": camera_id,
            "status": status
        }
    }
    await manager.broadcast(message)
