from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{camera_id}/mjpeg")
async def get_mjpeg_stream(camera_id: int):
    """Get MJPEG stream for a camera"""
    # TODO: Implement MJPEG stream from camera manager
    # This will be connected to the camera manager service
    raise HTTPException(
        status_code=501,
        detail="MJPEG streaming not yet implemented. Will be available after camera manager is complete."
    )


@router.get("/{camera_id}/snapshot")
async def get_snapshot(camera_id: int):
    """Get a single frame snapshot from camera"""
    # TODO: Implement snapshot capture
    raise HTTPException(
        status_code=501,
        detail="Snapshot feature not yet implemented"
    )
