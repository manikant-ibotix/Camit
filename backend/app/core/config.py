from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./camit.db"
    
    # Email Configuration
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    ALERT_RECIPIENTS: str = ""
    
    # Detection Thresholds
    FALL_CONFIDENCE_THRESHOLD: float = 0.75
    LYING_CONFIDENCE_THRESHOLD: float = 0.80
    LYING_TIME_THRESHOLD: int = 5  # seconds
    PUSHING_CONFIDENCE_THRESHOLD: float = 0.65
    CROWD_THRESHOLD: int = 10
    
    # Alert Settings
    ALERT_COOLDOWN_SECONDS: int = 60
    VIDEO_CLIP_DURATION: int = 15
    VIDEO_PRE_BUFFER: int = 5
    
    # Processing
    PROCESS_EVERY_N_FRAMES: int = 3
    MAX_CAMERAS: int = 6
    
    # Storage
    STORAGE_PATH: str = "./storage"
    ALERT_RETENTION_DAYS: int = 30
    
    # Application
    APP_NAME: str = "School CCTV Safety Monitoring System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def alert_recipients_list(self) -> List[str]:
        """Parse comma-separated alert recipients"""
        if not self.ALERT_RECIPIENTS:
            return []
        return [email.strip() for email in self.ALERT_RECIPIENTS.split(",")]
    
    @property
    def alerts_storage_path(self) -> str:
        """Get alerts storage directory path"""
        path = os.path.join(self.STORAGE_PATH, "alerts")
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def videos_storage_path(self) -> str:
        """Get videos storage directory path"""
        path = os.path.join(self.STORAGE_PATH, "videos")
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def images_storage_path(self) -> str:
        """Get images storage directory path"""
        path = os.path.join(self.STORAGE_PATH, "images")
        os.makedirs(path, exist_ok=True)
        return path


settings = Settings()
