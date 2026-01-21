import cv2
import numpy as np
import mediapipe as mp
from ultralytics import YOLO
import logging
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


class PoseDetector:
    """Pose detection using MediaPipe for fall and lying detection"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,  # 0=lite, 1=full, 2=heavy
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        logger.info("MediaPipe Pose detector initialized")
    
    def detect_fall(self, frame: np.ndarray) -> Tuple[bool, float, dict]:
        """
        Detect if a person has fallen
        Returns: (is_fall, confidence, metadata)
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)
            
            if not results.pose_landmarks:
                return False, 0.0, {}
            
            landmarks = results.pose_landmarks.landmark
            
            # Get key points
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            
            # Calculate average hip and shoulder positions
            avg_hip_y = (left_hip.y + right_hip.y) / 2
            avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
            
            # Calculate body angle (0 = horizontal, 90 = vertical)
            body_height = abs(avg_hip_y - nose.y)
            body_width = abs(left_hip.x - right_hip.x)
            
            # Angle calculation
            if body_height > 0:
                angle = np.arctan(body_height / max(body_width, 0.01)) * (180 / np.pi)
            else:
                angle = 0
            
            # Fall detected if:
            # 1. Body angle < 45 degrees (more horizontal than vertical)
            # 2. Hip is high in frame (person down)
            is_fall = angle < 45 and avg_hip_y > 0.6
            
            confidence = 1.0 - (angle / 90.0) if is_fall else 0.0
            confidence = max(0.0, min(1.0, confidence))
            
            metadata = {
                'body_angle': float(angle),
                'hip_position': float(avg_hip_y),
                'detection_method': 'pose_estimation'
            }
            
            return is_fall, confidence, metadata
        
        except Exception as e:
            logger.error(f"Fall detection error: {e}")
            return False, 0.0, {}
    
    def detect_lying(self, frame: np.ndarray) -> Tuple[bool, float, dict]:
        """
        Detect if a person is lying on the floor
        Returns: (is_lying, confidence, metadata)
        """
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)
            
            if not results.pose_landmarks:
                return False, 0.0, {}
            
            landmarks = results.pose_landmarks.landmark
            
            # Get key points
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
            right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            
            # Calculate aspect ratio (width/height of pose)
            min_x = min(nose.x, left_hip.x, right_hip.x, left_ankle.x, right_ankle.x)
            max_x = max(nose.x, left_hip.x, right_hip.x, left_ankle.x, right_ankle.x)
            min_y = min(nose.y, left_hip.y, right_hip.y, left_ankle.y, right_ankle.y)
            max_y = max(nose.y, left_hip.y, right_hip.y, left_ankle.y, right_ankle.y)
            
            width = max_x - min_x
            height = max_y - min_y
            
            aspect_ratio = width / max(height, 0.01)
            
            # Person is lying if aspect ratio > 1.5 (wider than tall)
            # and nose is low in frame (close to ground)
            is_lying = aspect_ratio > 1.5 and nose.y > 0.5
            
            confidence = min(aspect_ratio / 3.0, 1.0) if is_lying else 0.0
            
            metadata = {
                'aspect_ratio': float(aspect_ratio),
                'nose_height': float(nose.y),
                'detection_method': 'pose_estimation'
            }
            
            return is_lying, confidence, metadata
        
        except Exception as e:
            logger.error(f"Lying detection error: {e}")
            return False, 0.0, {}
    
    def close(self):
        """Clean up resources"""
        self.pose.close()


class ObjectDetector:
    """Object detection using YOLOv8 for person counting and crowd detection"""
    
    def __init__(self):
        try:
            # Load YOLOv8 nano model (fastest, good for CPU)
            self.model = YOLO('yolov8n.pt')
            logger.info("YOLOv8 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    def detect_persons(self, frame: np.ndarray) -> Tuple[int, List[dict], float]:
        """
        Detect persons in frame
        Returns: (person_count, detections, avg_confidence)
        """
        try:
            # Run inference
            results = self.model(frame, classes=[0], verbose=False)  # class 0 = person
            
            detections = []
            confidences = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    
                    detections.append({
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': confidence
                    })
                    confidences.append(confidence)
            
            person_count = len(detections)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return person_count, detections, avg_confidence
        
        except Exception as e:
            logger.error(f"Person detection error: {e}")
            return 0, [], 0.0
    
    def detect_crowd(self, frame: np.ndarray, threshold: int = 10) -> Tuple[bool, int, float, dict]:
        """
        Detect crowd formation
        Returns: (is_crowd, person_count, confidence, metadata)
        """
        person_count, detections, avg_confidence = self.detect_persons(frame)
        
        is_crowd = person_count >= threshold
        
        # Calculate density (persons per area)
        frame_area = frame.shape[0] * frame.shape[1]
        density = person_count / (frame_area / 1000000)  # persons per megapixel
        
        metadata = {
            'person_count': person_count,
            'threshold': threshold,
            'density': float(density),
            'detections': detections[:5]  # Store only first 5 to save space
        }
        
        return is_crowd, person_count, avg_confidence, metadata


class PushingDetector:
    """Detect pushing/aggressive behavior using pose and motion analysis"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.prev_frame = None
        self.prev_poses = []
        logger.info("Pushing detector initialized")
    
    def detect_pushing(self, frame: np.ndarray) -> Tuple[bool, float, dict]:
        """
        Detect pushing behavior
        Returns: (is_pushing, confidence, metadata)
        
        Note: This is a basic implementation. More sophisticated methods
        would use temporal information and action recognition models.
        """
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)
            
            # Need at least 2 people to detect pushing
            # This is a simplified version - would need multi-person pose detection
            # For now, detect sudden motion which could indicate pushing
            
            if self.prev_frame is not None:
                # Calculate optical flow
                prev_gray = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
                curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, curr_gray, None,
                    0.5, 3, 15, 3, 5, 1.2, 0
                )
                
                # Calculate magnitude of motion
                magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
                mean_motion = np.mean(magnitude)
                max_motion = np.max(magnitude)
                
                # Detect sudden strong motion (potential pushing)
                is_pushing = max_motion > 15 and mean_motion > 3
                confidence = min(max_motion / 30.0, 1.0) if is_pushing else 0.0
                
                metadata = {
                    'mean_motion': float(mean_motion),
                    'max_motion': float(max_motion),
                    'detection_method': 'optical_flow'
                }
                
                self.prev_frame = frame.copy()
                return is_pushing, confidence, metadata
            
            self.prev_frame = frame.copy()
            return False, 0.0, {}
        
        except Exception as e:
            logger.error(f"Pushing detection error: {e}")
            return False, 0.0, {}
    
    def close(self):
        """Clean up resources"""
        self.pose.close()


class DetectionService:
    """Main detection service that coordinates all detectors"""
    
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.object_detector = ObjectDetector()
        self.pushing_detector = PushingDetector()
        
        # Track lying detections for time threshold
        self.lying_tracker: Dict[int, datetime] = {}
        
        logger.info("Detection service initialized")
    
    def process_frame(self, camera_id: int, frame: np.ndarray, crowd_threshold: int = 10) -> dict:
        """
        Process a frame and return all detections
        """
        detections = {
            'camera_id': camera_id,
            'timestamp': datetime.utcnow().isoformat(),
            'fall': {'detected': False, 'confidence': 0.0, 'metadata': {}},
            'lying': {'detected': False, 'confidence': 0.0, 'metadata': {}},
            'pushing': {'detected': False, 'confidence': 0.0, 'metadata': {}},
            'crowd': {'detected': False, 'person_count': 0, 'confidence': 0.0, 'metadata': {}}
        }
        
        try:
            # Fall detection
            is_fall, fall_conf, fall_meta = self.pose_detector.detect_fall(frame)
            detections['fall'] = {
                'detected': is_fall and fall_conf >= settings.FALL_CONFIDENCE_THRESHOLD,
                'confidence': fall_conf,
                'metadata': fall_meta
            }
            
            # Lying detection with time threshold
            is_lying, lying_conf, lying_meta = self.pose_detector.detect_lying(frame)
            
            if is_lying and lying_conf >= settings.LYING_CONFIDENCE_THRESHOLD:
                if camera_id not in self.lying_tracker:
                    self.lying_tracker[camera_id] = datetime.utcnow()
                
                time_lying = (datetime.utcnow() - self.lying_tracker[camera_id]).total_seconds()
                
                detections['lying'] = {
                    'detected': time_lying >= settings.LYING_TIME_THRESHOLD,
                    'confidence': lying_conf,
                    'metadata': {**lying_meta, 'time_lying': time_lying}
                }
            else:
                # Reset tracker if not lying
                if camera_id in self.lying_tracker:
                    del self.lying_tracker[camera_id]
                detections['lying'] = {
                    'detected': False,
                    'confidence': lying_conf,
                    'metadata': lying_meta
                }
            
            # Crowd detection
            is_crowd, person_count, crowd_conf, crowd_meta = self.object_detector.detect_crowd(
                frame, threshold=crowd_threshold
            )
            detections['crowd'] = {
                'detected': is_crowd,
                'person_count': person_count,
                'confidence': crowd_conf,
                'metadata': crowd_meta
            }
            
            # Pushing detection
            is_pushing, push_conf, push_meta = self.pushing_detector.detect_pushing(frame)
            detections['pushing'] = {
                'detected': is_pushing and push_conf >= settings.PUSHING_CONFIDENCE_THRESHOLD,
                'confidence': push_conf,
                'metadata': push_meta
            }
        
        except Exception as e:
            logger.error(f"Error processing frame for camera {camera_id}: {e}")
        
        return detections
    
    def close(self):
        """Clean up all detectors"""
        self.pose_detector.close()
        self.pushing_detector.close()


# Global detection service instance
detection_service = DetectionService()
