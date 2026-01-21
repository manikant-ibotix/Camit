from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import os
import uuid
import logging
from app.core.config import settings
from app.services.video_analysis import video_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()


def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to destination"""
    try:
        with open(destination, "wb") as buffer:
            content = upload_file.file.read()
            buffer.write(content)
        return destination
    except Exception as e:
        logger.error(f"Error saving upload file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")


def analyze_video_task(video_path: str, analysis_id: str, crowd_threshold: int, frame_skip: int):
    """Background task to analyze video"""
    try:
        video_analysis_service.analyze_video(
            video_path=video_path,
            analysis_id=analysis_id,
            crowd_threshold=crowd_threshold,
            frame_skip=frame_skip
        )
    except Exception as e:
        logger.error(f"Error in video analysis task: {e}")


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    crowd_threshold: int = 10,
    frame_skip: int = 3
):
    """
    Upload a video file for analysis
    
    - **file**: Video file (mp4, avi, mov, etc.)
    - **crowd_threshold**: Number of people to trigger crowd detection
    - **frame_skip**: Process every Nth frame (1=every frame, 3=every 3rd frame)
    """
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique analysis ID
    analysis_id = str(uuid.uuid4())
    
    # Create uploads directory
    uploads_dir = os.path.join(settings.STORAGE_PATH, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Save uploaded file
    file_path = os.path.join(uploads_dir, f"{analysis_id}{file_ext}")
    save_upload_file(file, file_path)
    
    logger.info(f"Video uploaded: {file.filename} -> {analysis_id}")
    
    # Start analysis in background
    background_tasks.add_task(
        analyze_video_task,
        video_path=file_path,
        analysis_id=analysis_id,
        crowd_threshold=crowd_threshold,
        frame_skip=frame_skip
    )
    
    return {
        "message": "Video uploaded successfully. Analysis started.",
        "analysis_id": analysis_id,
        "filename": file.filename,
        "status": "processing"
    }


@router.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """Get analysis results by ID"""
    results = video_analysis_service.get_analysis_results(analysis_id)
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with ID {analysis_id} not found"
        )
    
    return results


@router.get("/list")
async def list_analyses():
    """List all video analyses"""
    analyses = video_analysis_service.list_analyses()
    return {
        "total": len(analyses),
        "analyses": analyses
    }


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete analysis results"""
    success = video_analysis_service.delete_analysis(analysis_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with ID {analysis_id} not found"
        )
    
    return {
        "message": "Analysis deleted successfully",
        "analysis_id": analysis_id
    }


@router.get("/statistics/{analysis_id}")
async def get_analysis_statistics(analysis_id: str):
    """Get summary statistics for an analysis"""
    results = video_analysis_service.get_analysis_results(analysis_id)
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with ID {analysis_id} not found"
        )
    
    if results.get("status") == "error":
        return {
            "status": "error",
            "message": results.get("message", "Analysis failed")
        }
    
    stats = results.get("statistics", {})
    video_info = results.get("video_info", {})
    
    # Calculate incident timeline
    timeline = []
    for detection_type in ['fall', 'lying', 'pushing', 'crowd']:
        detections = results.get('detections', {}).get(detection_type, [])
        for detection in detections:
            timeline.append({
                "type": detection_type,
                "timestamp": detection.get("timestamp"),
                "frame": detection.get("frame"),
                "confidence": detection.get("confidence"),
                "person_count": detection.get("person_count")
            })
    
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x.get("timestamp", 0))
    
    return {
        "analysis_id": analysis_id,
        "status": results.get("status"),
        "video_info": video_info,
        "statistics": stats,
        "timeline": timeline[:50],  # Return first 50 incidents
        "total_incidents": len(timeline)
    }
