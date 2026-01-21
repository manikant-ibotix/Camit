from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CameraStatus(str, Enum):
    """Camera connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"


class AlertType(str, Enum):
    """Types of alerts"""
    FALL = "fall"
    LYING = "lying"
    PUSHING = "pushing"
    CROWD = "crowd"
    NORMAL = "normal"


# Camera Schemas
class CameraBase(BaseModel):
    """Base camera schema"""
    name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    ip_address: str = Field(..., min_length=7, max_length=50)
    rtsp_url: str = Field(..., min_length=10, max_length=500)
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, max_length=100)
    crowd_threshold: int = Field(10, ge=1, le=100)
    enabled: bool = True


class CameraCreate(CameraBase):
    """Schema for creating a camera"""
    pass


class CameraUpdate(BaseModel):
    """Schema for updating a camera"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    ip_address: Optional[str] = Field(None, min_length=7, max_length=50)
    rtsp_url: Optional[str] = Field(None, min_length=10, max_length=500)
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, max_length=100)
    crowd_threshold: Optional[int] = Field(None, ge=1, le=100)
    enabled: Optional[bool] = None
    status: Optional[CameraStatus] = None


class Camera(CameraBase):
    """Schema for camera response"""
    id: int
    status: CameraStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Alert Schemas
class AlertBase(BaseModel):
    """Base alert schema"""
    camera_id: int
    alert_type: AlertType
    confidence: float = Field(..., ge=0.0, le=1.0)
    detection_metadata: Optional[str] = None


class AlertCreate(AlertBase):
    """Schema for creating an alert"""
    image_path: Optional[str] = None
    video_path: Optional[str] = None


class Alert(AlertBase):
    """Schema for alert response"""
    id: int
    image_path: Optional[str]
    video_path: Optional[str]
    acknowledged: bool
    email_sent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertWithCamera(Alert):
    """Alert with camera details"""
    camera: Camera


# Detection Log Schemas
class DetectionLogBase(BaseModel):
    """Base detection log schema"""
    camera_id: int
    detection_type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    person_count: int = Field(0, ge=0)
    detection_metadata: Optional[str] = None


class DetectionLogCreate(DetectionLogBase):
    """Schema for creating a detection log"""
    pass


class DetectionLog(DetectionLogBase):
    """Schema for detection log response"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# WebSocket Messages
class WSMessage(BaseModel):
    """WebSocket message schema"""
    type: str  # "alert", "detection", "camera_status", "heartbeat"
    data: dict


# Statistics
class CameraStats(BaseModel):
    """Camera statistics"""
    camera_id: int
    camera_name: str
    total_alerts: int
    alerts_by_type: dict
    status: CameraStatus
    last_detection: Optional[datetime]


class SystemStats(BaseModel):
    """System-wide statistics"""
    total_cameras: int
    active_cameras: int
    total_alerts_today: int
    alerts_by_type_today: dict
    system_status: str
