import threading
import time
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.camera_manager import camera_manager
from app.services.detection_service import detection_service
from app.services.alert_service import alert_service
from app.database.models import Camera, AlertType, CameraStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Orchestrates video processing pipeline:
    1. Get frames from camera manager
    2. Run AI detection
    3. Create alerts when incidents detected
    4. Maintain frame buffers for video clips
    """
    
    def __init__(self):
        self.running = False
        self.processing_thread = None
        self.frame_counter = {}
    
    def start(self):
        """Start video processing thread"""
        if self.running:
            logger.warning("Video processor already running")
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        logger.info("Video processor started")
    
    def stop(self):
        """Stop video processing thread"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        logger.info("Video processor stopped")
    
    def _processing_loop(self):
        """Main processing loop"""
        logger.info("Video processing loop started")
        
        while self.running:
            try:
                db = SessionLocal()
                
                # Get all running cameras
                running_cameras = camera_manager.get_running_cameras()
                
                for camera_id in running_cameras:
                    self._process_camera(db, camera_id)
                
                db.close()
                
                # Small sleep to prevent CPU overload
                time.sleep(0.01)
            
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(1)
    
    def _process_camera(self, db: Session, camera_id: int):
        """Process frames from a single camera"""
        try:
            # Get latest frame
            frame_data = camera_manager.get_frame(camera_id)
            
            if not frame_data:
                return
            
            frame = frame_data['frame']
            timestamp = frame_data['timestamp']
            frame_number = frame_data['frame_number']
            
            # Initialize frame counter for this camera
            if camera_id not in self.frame_counter:
                self.frame_counter[camera_id] = 0
            
            # Add frame to alert service buffer (for video clip generation)
            alert_service.add_frame_to_buffer(camera_id, frame, timestamp)
            
            # Process every Nth frame to save CPU
            if frame_number % settings.PROCESS_EVERY_N_FRAMES != 0:
                return
            
            # Get camera configuration
            camera = db.query(Camera).filter(Camera.id == camera_id).first()
            if not camera:
                return
            
            # Run AI detection
            detections = detection_service.process_frame(
                camera_id=camera_id,
                frame=frame,
                crowd_threshold=camera.crowd_threshold
            )
            
            # Check for alerts
            self._handle_detections(db, camera_id, frame, detections)
            
            self.frame_counter[camera_id] += 1
        
        except Exception as e:
            logger.error(f"Error processing camera {camera_id}: {e}")
    
    def _handle_detections(self, db: Session, camera_id: int, frame, detections: dict):
        """Handle detection results and create alerts if needed"""
        
        # Fall detection
        if detections['fall']['detected']:
            alert_service.create_alert(
                db=db,
                camera_id=camera_id,
                alert_type=AlertType.FALL,
                confidence=detections['fall']['confidence'],
                frame=frame,
                metadata=detections['fall']['metadata']
            )
        
        # Lying detection
        if detections['lying']['detected']:
            alert_service.create_alert(
                db=db,
                camera_id=camera_id,
                alert_type=AlertType.LYING,
                confidence=detections['lying']['confidence'],
                frame=frame,
                metadata=detections['lying']['metadata']
            )
        
        # Pushing detection
        if detections['pushing']['detected']:
            alert_service.create_alert(
                db=db,
                camera_id=camera_id,
                alert_type=AlertType.PUSHING,
                confidence=detections['pushing']['confidence'],
                frame=frame,
                metadata=detections['pushing']['metadata']
            )
        
        # Crowd detection
        if detections['crowd']['detected']:
            alert_service.create_alert(
                db=db,
                camera_id=camera_id,
                alert_type=AlertType.CROWD,
                confidence=detections['crowd']['confidence'],
                frame=frame,
                metadata=detections['crowd']['metadata']
            )


# Global video processor instance
video_processor = VideoProcessor()
