from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.database.models import Camera, CameraStatus
from app.schemas import Camera as CameraSchema, CameraCreate, CameraUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[CameraSchema])
async def get_cameras(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all cameras"""
    cameras = db.query(Camera).offset(skip).limit(limit).all()
    return cameras


@router.get("/{camera_id}", response_model=CameraSchema)
async def get_camera(camera_id: int, db: Session = Depends(get_db)):
    """Get camera by ID"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )
    return camera


@router.post("/", response_model=CameraSchema, status_code=status.HTTP_201_CREATED)
async def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    """Create a new camera"""
    # Check if camera name already exists
    existing_camera = db.query(Camera).filter(Camera.name == camera.name).first()
    if existing_camera:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Camera with name '{camera.name}' already exists"
        )
    
    db_camera = Camera(**camera.model_dump())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    
    logger.info(f"Created camera: {db_camera.name} (ID: {db_camera.id})")
    return db_camera


@router.put("/{camera_id}", response_model=CameraSchema)
async def update_camera(
    camera_id: int,
    camera_update: CameraUpdate,
    db: Session = Depends(get_db)
):
    """Update camera"""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )
    
    # Update fields
    update_data = camera_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_camera, field, value)
    
    db.commit()
    db.refresh(db_camera)
    
    logger.info(f"Updated camera: {db_camera.name} (ID: {db_camera.id})")
    return db_camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    """Delete camera"""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )
    
    db.delete(db_camera)
    db.commit()
    
    logger.info(f"Deleted camera: {db_camera.name} (ID: {camera_id})")
    return None


@router.post("/{camera_id}/start")
async def start_camera(camera_id: int, db: Session = Depends(get_db)):
    """Start camera stream"""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )
    
    # TODO: Implement camera stream start logic
    db_camera.status = CameraStatus.CONNECTING
    db.commit()
    
    logger.info(f"Starting camera: {db_camera.name} (ID: {camera_id})")
    return {"message": f"Camera {db_camera.name} starting", "camera_id": camera_id}


@router.post("/{camera_id}/stop")
async def stop_camera(camera_id: int, db: Session = Depends(get_db)):
    """Stop camera stream"""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )
    
    # TODO: Implement camera stream stop logic
    db_camera.status = CameraStatus.INACTIVE
    db.commit()
    
    logger.info(f"Stopping camera: {db_camera.name} (ID: {camera_id})")
    return {"message": f"Camera {db_camera.name} stopped", "camera_id": camera_id}
