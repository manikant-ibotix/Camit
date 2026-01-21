import cv2
import numpy as np
from multiprocessing import Process, Queue, Event
import logging
import time
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CameraStreamProcess:
    """Individual camera stream process"""
    
    def __init__(self, camera_id: int, rtsp_url: str, frame_queue: Queue, stop_event: Event):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.frame_queue = frame_queue
        self.stop_event = stop_event
        self.cap = None
        
    def run(self):
        """Main process loop for capturing frames"""
        logger.info(f"Starting camera stream process for camera {self.camera_id}")
        
        try:
            # Open video stream
            self.cap = cv2.VideoCapture(self.rtsp_url)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id}: {self.rtsp_url}")
                return
            
            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            frame_count = 0
            last_log_time = time.time()
            
            while not self.stop_event.is_set():
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning(f"Failed to read frame from camera {self.camera_id}, attempting reconnect...")
                    self.reconnect()
                    continue
                
                # Put frame in queue (non-blocking)
                try:
                    # Add timestamp and camera info
                    frame_data = {
                        'camera_id': self.camera_id,
                        'frame': frame,
                        'timestamp': datetime.utcnow(),
                        'frame_number': frame_count
                    }
                    
                    # Use put_nowait to avoid blocking
                    if self.frame_queue.full():
                        # Remove oldest frame if queue is full
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            pass
                    
                    self.frame_queue.put_nowait(frame_data)
                    frame_count += 1
                    
                    # Log status every 30 seconds
                    if time.time() - last_log_time > 30:
                        logger.debug(f"Camera {self.camera_id}: Processed {frame_count} frames")
                        last_log_time = time.time()
                
                except Exception as e:
                    logger.error(f"Error queuing frame from camera {self.camera_id}: {e}")
                
                # Small sleep to control frame rate
                time.sleep(0.01)
        
        except Exception as e:
            logger.error(f"Camera {self.camera_id} stream process error: {e}")
        
        finally:
            if self.cap:
                self.cap.release()
            logger.info(f"Camera {self.camera_id} stream process stopped")
    
    def reconnect(self):
        """Attempt to reconnect to camera"""
        if self.cap:
            self.cap.release()
        
        logger.info(f"Reconnecting to camera {self.camera_id}...")
        time.sleep(2)  # Wait before reconnect
        
        self.cap = cv2.VideoCapture(self.rtsp_url)
        if self.cap.isOpened():
            logger.info(f"Successfully reconnected to camera {self.camera_id}")
        else:
            logger.error(f"Reconnection failed for camera {self.camera_id}")


class CameraManager:
    """Manages multiple camera streams"""
    
    def __init__(self):
        self.processes: Dict[int, Process] = {}
        self.stop_events: Dict[int, Event] = {}
        self.frame_queues: Dict[int, Queue] = {}
        self.camera_info: Dict[int, dict] = {}
    
    def start_camera(self, camera_id: int, rtsp_url: str, camera_name: str = ""):
        """Start a camera stream process"""
        if camera_id in self.processes:
            logger.warning(f"Camera {camera_id} already running")
            return False
        
        try:
            # Create queue and stop event
            frame_queue = Queue(maxsize=10)
            stop_event = Event()
            
            # Create camera process
            camera_process = CameraStreamProcess(
                camera_id=camera_id,
                rtsp_url=rtsp_url,
                frame_queue=frame_queue,
                stop_event=stop_event
            )
            
            # Start process
            process = Process(target=camera_process.run)
            process.start()
            
            # Store references
            self.processes[camera_id] = process
            self.stop_events[camera_id] = stop_event
            self.frame_queues[camera_id] = frame_queue
            self.camera_info[camera_id] = {
                'name': camera_name,
                'rtsp_url': rtsp_url,
                'started_at': datetime.utcnow()
            }
            
            logger.info(f"Started camera {camera_id} ({camera_name})")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start camera {camera_id}: {e}")
            return False
    
    def stop_camera(self, camera_id: int):
        """Stop a camera stream process"""
        if camera_id not in self.processes:
            logger.warning(f"Camera {camera_id} not running")
            return False
        
        try:
            # Signal process to stop
            self.stop_events[camera_id].set()
            
            # Wait for process to finish (with timeout)
            self.processes[camera_id].join(timeout=5)
            
            # Force terminate if still alive
            if self.processes[camera_id].is_alive():
                self.processes[camera_id].terminate()
                self.processes[camera_id].join(timeout=2)
            
            # Cleanup
            del self.processes[camera_id]
            del self.stop_events[camera_id]
            del self.frame_queues[camera_id]
            del self.camera_info[camera_id]
            
            logger.info(f"Stopped camera {camera_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to stop camera {camera_id}: {e}")
            return False
    
    def get_frame(self, camera_id: int) -> Optional[dict]:
        """Get latest frame from camera"""
        if camera_id not in self.frame_queues:
            return None
        
        try:
            # Get most recent frame (non-blocking)
            frame_data = self.frame_queues[camera_id].get_nowait()
            return frame_data
        except:
            return None
    
    def is_camera_running(self, camera_id: int) -> bool:
        """Check if camera is running"""
        if camera_id not in self.processes:
            return False
        return self.processes[camera_id].is_alive()
    
    def get_running_cameras(self) -> list:
        """Get list of running camera IDs"""
        return list(self.processes.keys())
    
    def stop_all(self):
        """Stop all camera streams"""
        camera_ids = list(self.processes.keys())
        for camera_id in camera_ids:
            self.stop_camera(camera_id)
        logger.info("All cameras stopped")


# Global camera manager instance
camera_manager = CameraManager()
