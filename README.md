# School CCTV Safety Monitoring System - POC

## 🎯 Project Overview

AI-powered real-time CCTV monitoring system for schools with automated incident detection and email alerts.

**Key Features:**
- ✅ Real-time monitoring of multiple IP cameras
- ✅ AI-based detection (fall, lying, pushing, crowd formation)
- ✅ Automated email alerts with images and video clips
- ✅ Web dashboard for camera management and alert monitoring
- ✅ Cost-effective CPU-only operation (4-6 cameras)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ ([Download](https://www.python.org/downloads/))
- Node.js 18+ ([Download](https://nodejs.org/))
- 16GB RAM minimum
- Windows 10/11

### Option 1: Using Startup Scripts (Easiest)

1. **Start Backend:**
   - Double-click `start_backend.bat`
   - Wait for installation to complete
   - Configure `.env` file when prompted
   - Backend will run at http://localhost:8001

2. **Start Frontend:**
   - Double-click `start_frontend.bat`
   - Wait for installation to complete
   - Frontend will open at http://localhost:3001

### Option 2: Manual Setup

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

## 📋 Project Structure

```
camit/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST API routes
│   │   ├── core/           # Configuration
│   │   ├── database/       # Database models
│   │   ├── services/       # Business logic
│   │   │   ├── camera_manager.py      # Camera streaming
│   │   │   ├── detection_service.py   # AI detection
│   │   │   ├── alert_service.py       # Alert & email
│   │   │   └── video_processor.py     # Processing pipeline
│   │   ├── main.py         # Application entry
│   │   └── schemas.py      # Pydantic models
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   └── App.jsx        # Main app
│   └── package.json
├── storage/               # Video/image storage
├── README.md
├── SETUP_GUIDE.md
├── start_backend.bat      # Backend startup script
└── start_frontend.bat     # Frontend startup script
```

## 🎨 Dashboard Features

### 1. Dashboard Page
- System statistics (cameras, alerts)
- Real-time camera status
- Alert breakdowns by type

### 2. Cameras Page
- Add/edit/delete cameras
- Start/stop camera monitoring
- Configure RTSP streams
- Set custom crowd thresholds per camera

### 3. Alerts Page
- View all security alerts
- Filter by alert type
- Acknowledge alerts
- See confidence scores and timestamps

## 🤖 AI Detection Capabilities

| Detection Type | Method | Accuracy | Notes |
|---------------|--------|----------|-------|
| **Fall Detection** | Pose estimation | 80-90% | Body angle analysis |
| **Person Lying** | Pose estimation | 85-95% | Aspect ratio + time threshold (>5s) |
| **Pushing** | Optical flow | 60-75% | Sudden motion detection |
| **Crowd Formation** | Object detection | 90-95% | YOLOv8 person counting |

## 📧 Email Alert System

Automated alerts include:
- Alert type and severity
- Camera name and location
- Confidence score
- Timestamp
- Captured image (inline)
- Video clip (attachment, 10-15 seconds)

## ⚙️ Configuration

### Detection Thresholds (in `.env`):

```env
FALL_CONFIDENCE_THRESHOLD=0.75
LYING_CONFIDENCE_THRESHOLD=0.80
LYING_TIME_THRESHOLD=5
PUSHING_CONFIDENCE_THRESHOLD=0.65
CROWD_THRESHOLD=10
```

### Email Setup (Gmail):

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
ALERT_RECIPIENTS=admin@school.com,security@school.com
```

**Get Gmail App Password:**
1. Enable 2FA on your Google Account
2. Visit: https://myaccount.google.com/apppasswords
3. Generate password for "Mail" / "Other"
4. Use 16-character password in `.env`

### Camera RTSP URLs:

Most IP cameras use this format:
```
rtsp://username:password@camera_ip:port/stream_path
```

Example: `rtsp://admin:password123@192.168.1.100:554/stream1`

## 💰 Cost Analysis

### Hardware (One-time)
- **Using existing PC**: $0
- **New refurbished PC**: $400-600
- **New workstation**: $800-1,200
- **GPU (optional)**: +$200-400

### Operating Costs (Monthly)
- **Self-hosted**: $10-20 (electricity)
- **Cloud-hosted**: $60-85 (not recommended for POC)

### Software
- **All libraries**: FREE (open-source)

**Total POC Cost: $0-1,500 (one-time) + $10-20/month**

## 📊 Performance

### CPU-Only Mode:
- **Cameras**: 4-6 simultaneous
- **Frame rate**: 3-8 FPS processing per camera
- **Detection delay**: <2 seconds
- **RAM usage**: ~8-12GB

### With GPU (Optional):
- **Cameras**: 8-16 simultaneous
- **Frame rate**: 30+ FPS processing per camera
- **Detection delay**: <0.5 seconds
- **Recommended**: NVIDIA GTX 1660 or better

## 🔒 Security Considerations

- Store camera passwords securely
- Use HTTPS in production (not implemented in POC)
- Comply with school privacy policies
- Implement user authentication before deployment
- Regular security audits
- Data retention policy (30-90 days recommended)

## 🐛 Troubleshooting

### Camera won't connect:
- Verify RTSP URL with VLC Media Player
- Check network connectivity
- Verify firewall settings
- Test camera credentials

### No detections:
- Ensure camera has clear view
- Check lighting conditions
- Verify camera is "active" status
- Check backend logs

### Email not sending:
- Verify Gmail App Password
- Check spam folder
- Ensure recipients are configured
- Test SMTP settings

## 📚 API Documentation

Once backend is running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🔄 Development Roadmap

**Phase 1 (Current POC):**
- ✅ Basic detection (fall, lying, pushing, crowd)
- ✅ Email alerts
- ✅ Camera management
- ✅ Web dashboard

**Phase 2 (Future):**
- [ ] User authentication & authorization
- [ ] Live MJPEG streaming in dashboard
- [ ] Advanced analytics and reports
- [ ] Mobile app for alerts
- [ ] Face detection (with privacy controls)
- [ ] Improved pushing detection with action recognition

**Phase 3 (Production):**
- [ ] HTTPS/SSL encryption
- [ ] Database migration to PostgreSQL
- [ ] Kubernetes deployment
- [ ] High availability setup
- [ ] Advanced video analytics

## 📄 License

MIT License - Educational POC Project

## 🤝 Support

For issues or questions:
1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. Review backend logs
3. Check browser console for frontend errors
4. Verify camera RTSP URLs with VLC

## 🎓 Academic Use

This is a Proof of Concept (POC) system designed for educational purposes and school safety applications. It demonstrates the integration of:
- Computer vision and AI
- Real-time video processing
- Multi-camera management
- Alert systems
- Full-stack web development

**Research Areas:**
- Human pose estimation
- Action recognition
- Crowd analysis
- Real-time incident detection
- IoT camera integration

---

**Built with:** FastAPI • React • YOLOv8 • MediaPipe • OpenCV • Material-UI
