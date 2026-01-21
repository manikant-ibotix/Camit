from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.database.models import Alert, Camera, AlertType
from app.schemas import Alert as AlertSchema, AlertWithCamera
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[AlertWithCamera])
async def get_alerts(
    skip: int = 0,
    limit: int = 100,
    camera_id: Optional[int] = None,
    alert_type: Optional[AlertType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get alerts with filtering options"""
    query = db.query(Alert).join(Camera)
    
    # Apply filters
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if start_date:
        query = query.filter(Alert.created_at >= start_date)
    if end_date:
        query = query.filter(Alert.created_at <= end_date)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    
    # Order by most recent first
    query = query.order_by(desc(Alert.created_at))
    
    alerts = query.offset(skip).limit(limit).all()
    return alerts


@router.get("/{alert_id}", response_model=AlertWithCamera)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get alert by ID"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert with id {alert_id} not found")
    return alert


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert with id {alert_id} not found")
    
    alert.acknowledged = True
    db.commit()
    
    logger.info(f"Alert {alert_id} acknowledged")
    return {"message": "Alert acknowledged", "alert_id": alert_id}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert with id {alert_id} not found")
    
    db.delete(alert)
    db.commit()
    
    logger.info(f"Alert {alert_id} deleted")
    return {"message": "Alert deleted", "alert_id": alert_id}


@router.get("/stats/summary")
async def get_alert_stats(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get alert statistics for the past N days"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total alerts
    total_alerts = db.query(func.count(Alert.id)).filter(
        Alert.created_at >= start_date
    ).scalar()
    
    # Alerts by type
    alerts_by_type = {}
    for alert_type in AlertType:
        count = db.query(func.count(Alert.id)).filter(
            Alert.created_at >= start_date,
            Alert.alert_type == alert_type
        ).scalar()
        alerts_by_type[alert_type.value] = count
    
    # Alerts by camera
    alerts_by_camera = db.query(
        Camera.name,
        func.count(Alert.id).label('count')
    ).join(Alert).filter(
        Alert.created_at >= start_date
    ).group_by(Camera.id).all()
    
    # Today's alerts
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_alerts = db.query(func.count(Alert.id)).filter(
        Alert.created_at >= today_start
    ).scalar()
    
    return {
        "total_alerts": total_alerts,
        "today_alerts": today_alerts,
        "alerts_by_type": alerts_by_type,
        "alerts_by_camera": [{"camera": name, "count": count} for name, count in alerts_by_camera],
        "period_days": days
    }
