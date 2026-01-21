import cv2
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
from app.services.detection_service import detection_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoAnalysisService:
    """Service for analyzing uploaded video files"""
    
    def __init__(self):
        self.results_storage = os.path.join(settings.STORAGE_PATH, "analysis_results")
        os.makedirs(self.results_storage, exist_ok=True)
    
    def analyze_video(
        self,
        video_path: str,
        analysis_id: str,
        crowd_threshold: int = 10,
        frame_skip: int = 3
    ) -> Dict:
        """
        Analyze a video file and return detection results
        
        Args:
            video_path: Path to uploaded video file
            analysis_id: Unique identifier for this analysis
            crowd_threshold: Threshold for crowd detection
            frame_skip: Process every Nth frame (1 = every frame)
        
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Starting analysis for video: {video_path}")
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error(f"Failed to open video: {video_path}")
                return {
                    "status": "error",
                    "message": "Failed to open video file"
                }
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Video properties: {width}x{height}, {fps} fps, {total_frames} frames, {duration:.2f}s")
            
            # Analysis results
            results = {
                "analysis_id": analysis_id,
                "video_info": {
                    "filename": os.path.basename(video_path),
                    "duration": duration,
                    "fps": fps,
                    "total_frames": total_frames,
                    "resolution": f"{width}x{height}"
                },
                "detections": {
                    "fall": [],
                    "lying": [],
                    "pushing": [],
                    "crowd": []
                },
                "statistics": {
                    "total_fall_detections": 0,
                    "total_lying_detections": 0,
                    "total_pushing_detections": 0,
                    "total_crowd_detections": 0,
                    "max_people_detected": 0,
                    "frames_processed": 0
                },
                "status": "processing",
                "progress": 0,
                "created_at": datetime.utcnow().isoformat()
            }
            
            frame_count = 0
            processed_count = 0
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Process every Nth frame
                if frame_count % frame_skip == 0:
                    timestamp = frame_count / fps if fps > 0 else frame_count
                    
                    # Run detection
                    detections = detection_service.process_frame(
                        camera_id=0,  # Use 0 for uploaded videos
                        frame=frame,
                        crowd_threshold=crowd_threshold
                    )
                    
                    # Store fall detections
                    if detections['fall']['detected']:
                        results['detections']['fall'].append({
                            "timestamp": timestamp,
                            "frame": frame_count,
                            "confidence": detections['fall']['confidence'],
                            "metadata": detections['fall']['metadata']
                        })
                        results['statistics']['total_fall_detections'] += 1
                    
                    # Store lying detections
                    if detections['lying']['detected']:
                        results['detections']['lying'].append({
                            "timestamp": timestamp,
                            "frame": frame_count,
                            "confidence": detections['lying']['confidence'],
                            "metadata": detections['lying']['metadata']
                        })
                        results['statistics']['total_lying_detections'] += 1
                    
                    # Store pushing detections
                    if detections['pushing']['detected']:
                        results['detections']['pushing'].append({
                            "timestamp": timestamp,
                            "frame": frame_count,
                            "confidence": detections['pushing']['confidence'],
                            "metadata": detections['pushing']['metadata']
                        })
                        results['statistics']['total_pushing_detections'] += 1
                    
                    # Store crowd detections
                    if detections['crowd']['detected']:
                        results['detections']['crowd'].append({
                            "timestamp": timestamp,
                            "frame": frame_count,
                            "person_count": detections['crowd']['person_count'],
                            "confidence": detections['crowd']['confidence'],
                            "metadata": detections['crowd']['metadata']
                        })
                        results['statistics']['total_crowd_detections'] += 1
                    
                    # Track max people
                    if detections['crowd']['person_count'] > results['statistics']['max_people_detected']:
                        results['statistics']['max_people_detected'] = detections['crowd']['person_count']
                    
                    processed_count += 1
                    results['statistics']['frames_processed'] = processed_count
                    
                    # Update progress
                    progress = int((frame_count / total_frames) * 100)
                    results['progress'] = progress
                    
                    if processed_count % 30 == 0:
                        logger.info(f"Progress: {progress}% ({processed_count} frames processed)")
                
                frame_count += 1
            
            cap.release()
            
            # Mark as completed
            results['status'] = "completed"
            results['progress'] = 100
            results['completed_at'] = datetime.utcnow().isoformat()
            
            # Save results to JSON file
            results_file = os.path.join(self.results_storage, f"{analysis_id}.json")
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Analysis completed: {analysis_id}")
            logger.info(f"Falls: {results['statistics']['total_fall_detections']}, "
                       f"Lying: {results['statistics']['total_lying_detections']}, "
                       f"Pushing: {results['statistics']['total_pushing_detections']}, "
                       f"Crowd: {results['statistics']['total_crowd_detections']}")
            
            return results
        
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            return {
                "status": "error",
                "message": str(e),
                "analysis_id": analysis_id
            }
    
    def get_analysis_results(self, analysis_id: str) -> Optional[Dict]:
        """Get saved analysis results"""
        results_file = os.path.join(self.results_storage, f"{analysis_id}.json")
        
        if not os.path.exists(results_file):
            return None
        
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading analysis results: {e}")
            return None
    
    def list_analyses(self) -> List[Dict]:
        """List all saved analyses"""
        analyses = []
        
        try:
            for filename in os.listdir(self.results_storage):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.results_storage, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        analyses.append({
                            "analysis_id": data.get("analysis_id"),
                            "filename": data.get("video_info", {}).get("filename"),
                            "duration": data.get("video_info", {}).get("duration"),
                            "status": data.get("status"),
                            "created_at": data.get("created_at"),
                            "total_detections": (
                                data.get("statistics", {}).get("total_fall_detections", 0) +
                                data.get("statistics", {}).get("total_lying_detections", 0) +
                                data.get("statistics", {}).get("total_pushing_detections", 0) +
                                data.get("statistics", {}).get("total_crowd_detections", 0)
                            )
                        })
        except Exception as e:
            logger.error(f"Error listing analyses: {e}")
        
        # Sort by created_at descending
        analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return analyses
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete analysis results"""
        results_file = os.path.join(self.results_storage, f"{analysis_id}.json")
        
        try:
            if os.path.exists(results_file):
                os.remove(results_file)
                logger.info(f"Deleted analysis: {analysis_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting analysis: {e}")
            return False


# Global instance
video_analysis_service = VideoAnalysisService()
