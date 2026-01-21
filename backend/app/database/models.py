from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class CameraStatus(str, enum.Enum):
    """Camera connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"


class AlertType(str, enum.Enum):
    """Types of alerts that can be detected"""
    FALL = "fall"
    LYING = "lying"
    PUSHING = "pushing"
    CROWD = "crowd"
    NORMAL = "normal"


class Camera(Base):
    """Camera model - stores camera configuration"""
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    location = Column(String(200), nullable=True)
    ip_address = Column(String(50), nullable=False)
    rtsp_url = Column(String(500), nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(String(100), nullable=True)
    status = Column(Enum(CameraStatus), default=CameraStatus.INACTIVE)
    crowd_threshold = Column(Integer, default=10)  # Custom threshold per camera
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alerts = relationship("Alert", back_populates="camera", cascade="all, delete-orphan")
    detection_logs = relationship("DetectionLog", back_populates="camera", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Camera(id={self.id}, name={self.name}, status={self.status})>"


class Alert(Base):
    """Alert model - stores triggered alerts"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    image_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    detection_metadata = Column(Text, nullable=True)  # JSON string for additional data
    acknowledged = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    camera = relationship("Camera", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, camera={self.camera_id})>"


class DetectionLog(Base):
    """Detection log - stores all detections for analytics"""
    __tablename__ = "detection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    detection_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    person_count = Column(Integer, default=0)  # For crowd detection
    detection_metadata = Column(Text, nullable=True)  # JSON string for pose data, bounding boxes, etc.
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    camera = relationship("Camera", back_populates="detection_logs")
    
    def __repr__(self):
        return f"<DetectionLog(id={self.id}, type={self.detection_type}, camera={self.camera_id})>"
