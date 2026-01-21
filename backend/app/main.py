from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.routes import cameras, alerts, streams, websocket, analysis
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered school CCTV safety monitoring system with real-time incident detection",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Create storage directories
    settings.alerts_storage_path
    settings.videos_storage_path
    settings.images_storage_path
    logger.info("Storage directories created")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "School CCTV Safety Monitoring System API",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


# Include routers
app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(streams.router, prefix="/api/streams", tags=["streams"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=settings.DEBUG)
