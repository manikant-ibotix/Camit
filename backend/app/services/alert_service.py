import smtplib
import cv2
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.models import Alert, AlertType, Camera
from app.schemas import AlertCreate
import numpy as np

logger = logging.getLogger(__name__)


class AlertDeduplicator:
    """Manages alert cooldown to prevent spam"""
    
    def __init__(self):
        self.last_alerts: Dict[tuple, datetime] = {}
    
    def should_send_alert(self, camera_id: int, alert_type: str) -> bool:
        """Check if enough time has passed since last alert of this type"""
        key = (camera_id, alert_type)
        
        if key not in self.last_alerts:
            self.last_alerts[key] = datetime.utcnow()
            return True
        
        time_since_last = (datetime.utcnow() - self.last_alerts[key]).total_seconds()
        
        if time_since_last >= settings.ALERT_COOLDOWN_SECONDS:
            self.last_alerts[key] = datetime.utcnow()
            return True
        
        return False
    
    def cleanup_old_entries(self):
        """Remove old entries to prevent memory buildup"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=settings.ALERT_COOLDOWN_SECONDS * 2)
        keys_to_remove = [
            key for key, timestamp in self.last_alerts.items()
            if timestamp < cutoff_time
        ]
        for key in keys_to_remove:
            del self.last_alerts[key]


class VideoClipGenerator:
    """Generates video clips from frame buffer"""
    
    def __init__(self):
        self.frame_buffers: Dict[int, list] = {}
        self.max_buffer_size = 300  # ~10 seconds at 30fps
    
    def add_frame(self, camera_id: int, frame: np.ndarray, timestamp: datetime):
        """Add frame to buffer"""
        if camera_id not in self.frame_buffers:
            self.frame_buffers[camera_id] = []
        
        self.frame_buffers[camera_id].append({
            'frame': frame.copy(),
            'timestamp': timestamp
        })
        
        # Keep buffer size limited
        if len(self.frame_buffers[camera_id]) > self.max_buffer_size:
            self.frame_buffers[camera_id].pop(0)
    
    def generate_clip(self, camera_id: int, output_path: str, duration: int = 15) -> bool:
        """Generate video clip from buffer"""
        if camera_id not in self.frame_buffers or not self.frame_buffers[camera_id]:
            logger.warning(f"No frames in buffer for camera {camera_id}")
            return False
        
        try:
            frames = self.frame_buffers[camera_id]
            
            # Get recent frames (based on duration)
            recent_frames = frames[-duration * 30:]  # Assuming ~30fps
            
            if not recent_frames:
                return False
            
            # Get frame dimensions
            height, width = recent_frames[0]['frame'].shape[:2]
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
            
            # Write frames
            for frame_data in recent_frames:
                out.write(frame_data['frame'])
            
            out.release()
            logger.info(f"Generated video clip: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error generating video clip: {e}")
            return False


class EmailService:
    """Handles email notifications for alerts"""
    
    def __init__(self):
        self.smtp_configured = self._check_smtp_config()
    
    def _check_smtp_config(self) -> bool:
        """Check if SMTP is properly configured"""
        if not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
            logger.warning("Email credentials not configured. Email alerts will be disabled.")
            return False
        return True
    
    def send_alert_email(
        self,
        alert_type: str,
        camera_name: str,
        camera_location: str,
        confidence: float,
        timestamp: datetime,
        image_path: Optional[str] = None,
        video_path: Optional[str] = None
    ) -> bool:
        """Send email alert with image and video attachments"""
        
        if not self.smtp_configured:
            logger.warning("Email not configured, skipping email send")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('related')
            msg['Subject'] = f"[ALERT] {alert_type.upper()} Detected - {camera_name}"
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = ", ".join(settings.alert_recipients_list)
            
            # Create HTML body
            html_body = self._create_html_body(
                alert_type, camera_name, camera_location, confidence, timestamp
            )
            
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)
            
            # Attach HTML
            msg_alternative.attach(MIMEText(html_body, 'html'))
            
            # Attach image inline if available
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', '<alert_image>')
                    img.add_header('Content-Disposition', 'inline', filename='alert.jpg')
                    msg.attach(img)
            
            # Attach video if available
            if video_path and os.path.exists(video_path):
                with open(video_path, 'rb') as f:
                    video = MIMEBase('video', 'mp4')
                    video.set_payload(f.read())
                    encoders.encode_base64(video)
                    video.add_header(
                        'Content-Disposition',
                        f'attachment; filename="alert_{timestamp.strftime("%Y%m%d_%H%M%S")}.mp4"'
                    )
                    msg.attach(video)
            
            # Send email
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Alert email sent for {alert_type} at {camera_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False
    
    def _create_html_body(
        self,
        alert_type: str,
        camera_name: str,
        camera_location: str,
        confidence: float,
        timestamp: datetime
    ) -> str:
        """Create HTML email body"""
        
        alert_descriptions = {
            'fall': 'A person has fallen down',
            'lying': 'A person has been lying on the floor',
            'pushing': 'Aggressive pushing behavior detected',
            'crowd': 'Unusual crowd formation detected'
        }
        
        description = alert_descriptions.get(alert_type, 'Incident detected')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f5f5f5; padding: 20px; border-radius: 0 0 5px 5px; }}
                .alert-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #d32f2f; }}
                .details {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #555; }}
                img {{ max-width: 100%; height: auto; margin: 15px 0; border: 2px solid #ddd; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ SECURITY ALERT</h1>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <h2>{alert_type.upper()} DETECTED</h2>
                        <p>{description}</p>
                    </div>
                    
                    <div class="details">
                        <p><span class="label">Camera:</span> {camera_name}</p>
                        <p><span class="label">Location:</span> {camera_location or 'Not specified'}</p>
                        <p><span class="label">Time:</span> {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        <p><span class="label">Confidence:</span> {confidence * 100:.1f}%</p>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <p class="label">Captured Image:</p>
                        <img src="cid:alert_image" alt="Alert Image">
                    </div>
                    
                    <div style="margin: 20px 0; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                        <p><strong>Action Required:</strong> Please review the incident and take appropriate action.</p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated alert from the School CCTV Safety Monitoring System</p>
                        <p>Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html


class AlertService:
    """Main alert service coordinating detection, storage, and notifications"""
    
    def __init__(self):
        self.deduplicator = AlertDeduplicator()
        self.video_generator = VideoClipGenerator()
        self.email_service = EmailService()
    
    def add_frame_to_buffer(self, camera_id: int, frame: np.ndarray, timestamp: datetime):
        """Add frame to video buffer for clip generation"""
        self.video_generator.add_frame(camera_id, frame, timestamp)
    
    def create_alert(
        self,
        db: Session,
        camera_id: int,
        alert_type: AlertType,
        confidence: float,
        frame: np.ndarray,
        metadata: dict = None
    ) -> Optional[Alert]:
        """Create and process a new alert"""
        
        # Check deduplication
        if not self.deduplicator.should_send_alert(camera_id, alert_type.value):
            logger.debug(f"Alert {alert_type.value} for camera {camera_id} suppressed (cooldown)")
            return None
        
        try:
            # Get camera info
            camera = db.query(Camera).filter(Camera.id == camera_id).first()
            if not camera:
                logger.error(f"Camera {camera_id} not found")
                return None
            
            timestamp = datetime.utcnow()
            
            # Generate file paths
            timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
            image_filename = f"alert_{camera_id}_{alert_type.value}_{timestamp_str}.jpg"
            video_filename = f"alert_{camera_id}_{alert_type.value}_{timestamp_str}.mp4"
            
            image_path = os.path.join(settings.images_storage_path, image_filename)
            video_path = os.path.join(settings.videos_storage_path, video_filename)
            
            # Save alert image
            cv2.imwrite(image_path, frame)
            logger.info(f"Saved alert image: {image_path}")
            
            # Generate video clip
            video_generated = self.video_generator.generate_clip(
                camera_id, video_path, duration=settings.VIDEO_CLIP_DURATION
            )
            
            if not video_generated:
                video_path = None
            
            # Create alert in database
            alert_data = AlertCreate(
                camera_id=camera_id,
                alert_type=alert_type,
                confidence=confidence,
                image_path=image_path,
                video_path=video_path,
                detection_metadata=str(metadata) if metadata else None
            )
            
            db_alert = Alert(**alert_data.model_dump())
            db.add(db_alert)
            db.commit()
            db.refresh(db_alert)
            
            logger.info(f"Created alert {db_alert.id}: {alert_type.value} at camera {camera.name}")
            
            # Send email notification
            email_sent = self.email_service.send_alert_email(
                alert_type=alert_type.value,
                camera_name=camera.name,
                camera_location=camera.location or "Unknown",
                confidence=confidence,
                timestamp=timestamp,
                image_path=image_path,
                video_path=video_path if video_generated else None
            )
            
            if email_sent:
                db_alert.email_sent = True
                db.commit()
            
            # Cleanup old deduplication entries periodically
            self.deduplicator.cleanup_old_entries()
            
            return db_alert
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            db.rollback()
            return None


# Global alert service instance
alert_service = AlertService()
