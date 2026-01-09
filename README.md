# 🗑️ ESP32-CAM Waste Classification System

[![PlatformIO](https://img.shields.io/badge/PlatformIO-ESP32-orange.svg)](https://platformio.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Real-time waste classification system using **ESP32-CAM** with Edge Impulse machine learning, featuring live MJPEG streaming and a modern web dashboard for monitoring and analytics.

<div align="center">
  <img src="https://img.shields.io/badge/Status-Active-success" alt="Status">
  <img src="https://img.shields.io/badge/Hardware-ESP32--CAM-blue" alt="Hardware">
  <img src="https://img.shields.io/badge/ML-Edge%20Impulse-purple" alt="ML Framework">
</div>

---

## ✨ Features

### 🎯 Core Functionality
- ✅ **9-Category Waste Classification**
  - Battery, Biological, Cardboard, Clothes, Glass, Metal, Paper, Plastic, Shoe
- ✅ **Live MJPEG Video Streaming** from ESP32-CAM
- ✅ **Real-time Predictions** with confidence scores (>60% threshold)
- ✅ **Edge Computing** - AI inference runs directly on ESP32
- ✅ **2-Second Inference Interval** for responsive detection

### 🌐 Connectivity
- ✅ **WiFi Integration** with auto-reconnection
- ✅ **HTTP Backend Communication** for data logging
- ✅ **WebSocket Support** for real-time dashboard updates
- ✅ **REST API** for system integration

### 📊 Web Dashboard
- ✅ **Modern Dark Theme** with glass-morphism design
- ✅ **Live Camera Feed** with MJPEG streaming
- ✅ **Real-time Prediction Overlay** with animations
- ✅ **Prediction History** (last 10 items)
- ✅ **Statistics Dashboard** (totals, averages, distribution)
- ✅ **Color-Coded Categories** for quick identification
- ✅ **Fully Responsive** - works on desktop, tablet, and mobile

### 🛠️ Development Features
- ✅ **Serial Commands** (pause, resume, status, reset)
- ✅ **Status LED Indicators** for system state
- ✅ **CSV Data Logging** for analysis
- ✅ **Memory Efficient** with proper buffer management
- ✅ **Error Handling** with graceful degradation

---

## 🏗️ System Architecture

```
┌─────────────────┐
│   ESP32-CAM     │
│  - Camera       │
│  - AI Model     │──MJPEG──┐
│  - WiFi         │         │
└────────┬────────┘         │
         │ HTTP POST        │
         │ (Predictions)    │
         ▼                  ▼
┌─────────────────┐   ┌──────────────┐
│  Flask Backend  │   │ Web Browser  │
│  - REST API     │◄──┤ - Dashboard  │
│  - WebSocket    │   │ - Live View  │
│  - Data Logging │   └──────────────┘
└─────────────────┘
```

**Data Flow:**
1. ESP32-CAM captures image every 2 seconds
2. Edge Impulse model runs inference on-device
3. Predictions with >60% confidence sent to Flask backend via HTTP
4. Flask logs to CSV and broadcasts to connected clients via WebSocket
5. Web dashboard updates in real-time with prediction overlay

---

## 🚀 Quick Start

### Prerequisites
- ESP32-CAM module
- USB-to-Serial adapter (for programming)
- Python 3.8+
- PlatformIO (VSCode extension or CLI)

### 1. Clone Repository
```bash
git clone https://github.com/SarangPratap/Waste_Classification.git
cd Waste_Classification
```

### 2. Configure WiFi Settings
Edit `include/config.h`:
```cpp
#define WIFI_SSID "Your_WiFi_Name"
#define WIFI_PASSWORD "Your_WiFi_Password"
#define BACKEND_HOST "192.168.1.100"  // Your computer's IP
```

### 3. Flash ESP32-CAM
```bash
# Using PlatformIO CLI
pio run --target upload

# Or use VSCode PlatformIO extension: Click "Upload" button
```

### 4. Start Backend Server
```bash
cd server
pip install -r requirements.txt
python app.py
```

### 5. Open Dashboard
Open browser and navigate to:
```
http://localhost:5000
```

Enter ESP32-CAM IP address to connect video stream.

**🎉 That's it! Your system is now running!**

For detailed setup instructions, see [docs/SETUP.md](docs/SETUP.md)

---

## 📸 Screenshots

### Web Dashboard
<div align="center">
  <i>Coming soon - Modern dark theme with live predictions</i>
</div>

### Features Showcase
- **Live Video Feed** - Real-time MJPEG stream
- **Prediction Card** - Animated category display with confidence bar
- **History List** - Color-coded recent predictions
- **Statistics** - Total counts and category distribution

---

## 🎨 Waste Categories & Colors

| Category | Icon | Color | Use Case |
|----------|------|-------|----------|
| Battery | 🔋 | Gold (#FFD700) | Batteries, power cells |
| Biological | 🍎 | Lime Green (#32CD32) | Food waste, organic |
| Cardboard | 📦 | Brown (#8B4513) | Boxes, packaging |
| Clothes | 👕 | Purple (#9370DB) | Textiles, fabrics |
| Glass | 🫙 | Turquoise (#00CED1) | Bottles, jars |
| Metal | 🔩 | Gray (#808080) | Cans, metal objects |
| Paper | 📄 | Sky Blue (#87CEEB) | Documents, newspapers |
| Plastic | 🍾 | Blue (#1E90FF) | Bottles, containers |
| Shoe | 👟 | Orange (#FF8C00) | Footwear |

---

## 📁 Project Structure

```
Waste_Classification/
├── platformio.ini              # PlatformIO configuration
├── src/
│   └── main.cpp                # ESP32-CAM firmware
├── include/
│   ├── config.h                # WiFi & backend settings
│   ├── camera_pins.h           # ESP32-CAM pin definitions
│   └── README                  # Include directory info
├── server/
│   ├── app.py                  # Flask backend server
│   ├── requirements.txt        # Python dependencies
│   ├── static/
│   │   ├── index.html          # Web dashboard
│   │   ├── css/
│   │   │   └── style.css       # Modern dark theme styles
│   │   └── js/
│   │       └── app.js          # WebSocket & UI logic
│   ├── data/
│   │   └── predictions.csv     # Logged predictions
│   └── README.md               # Backend documentation
├── docs/
│   ├── SETUP.md                # Detailed setup guide
│   └── API.md                  # API documentation
├── lib/                        # PlatformIO libraries
├── test/                       # Test files
└── README.md                   # This file
```

---

## 🔧 Configuration

### ESP32-CAM Settings (`include/config.h`)

```cpp
// WiFi Configuration
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Backend Server
#define BACKEND_HOST "192.168.1.100"
#define BACKEND_PORT 5000

// Camera Settings
#define CAMERA_QUALITY 12          // 0-63 (lower = better quality)
#define INFERENCE_INTERVAL 2000     // Milliseconds

// Thresholds
#define CONFIDENCE_THRESHOLD 0.6    // Only send predictions >60%
```

### Serial Commands

Control ESP32-CAM via Serial Monitor (115200 baud):

| Command | Description |
|---------|-------------|
| `pause` | Pause inference temporarily |
| `resume` | Resume inference |
| `status` | Display system status |
| `reset` | Restart ESP32-CAM |

---

## 🌐 API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web dashboard |
| POST | `/api/prediction` | Receive prediction from ESP32 |
| GET | `/api/predictions` | Get recent predictions (last 50) |
| GET | `/api/stats` | Get statistics |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Connection established |
| `disconnect` | Client → Server | Connection closed |
| `new_prediction` | Server → Client | New prediction broadcast |

For detailed API documentation, see [docs/API.md](docs/API.md)

---

## 📊 Data Logging

Predictions are automatically logged to `server/data/predictions.csv`:

```csv
timestamp,category,confidence,device_id
2024-01-09T12:00:00.123456,plastic,0.87,ESP32-CAM-001
2024-01-09T12:00:02.456789,paper,0.92,ESP32-CAM-001
```

---

## 🧪 Testing

### Test ESP32-CAM
```bash
# Monitor serial output
pio device monitor -b 115200
```

### Test Backend
```bash
# Send test prediction
curl -X POST http://localhost:5000/api/prediction \
  -H "Content-Type: application/json" \
  -d '{"category":"plastic","confidence":0.87,"device_id":"test"}'

# Get statistics
curl http://localhost:5000/api/stats
```

### Test WebSocket
Open browser console on dashboard and check for WebSocket connection messages.

---

## 🔍 Troubleshooting

### Common Issues

**ESP32 won't connect to WiFi**
- Verify WiFi credentials in `config.h`
- Ensure 2.4GHz network (ESP32 doesn't support 5GHz)
- Check power supply (minimum 500mA)

**Camera initialization fails**
- Verify pin connections
- Check PSRAM availability
- Lower `CAMERA_QUALITY` value

**Dashboard not updating**
- Check Flask server is running
- Verify `BACKEND_HOST` matches computer IP
- Check browser console for errors
- Ensure devices on same WiFi network

For more troubleshooting, see [docs/SETUP.md](docs/SETUP.md#-troubleshooting)

---

## 🛠️ Hardware Requirements

### Required Components
- **ESP32-CAM** (AI Thinker model recommended)
- **USB-to-Serial adapter** (FTDI or CP2102)
- **5V Power supply** (minimum 500mA)
- **Computer** with WiFi

### Optional Components
- **Case/enclosure** for ESP32-CAM
- **External antenna** for better WiFi range
- **LED indicators** for status
- **Servo motors** for sorting mechanism (future)

---

## 🔮 Future Enhancements

Planned features (not yet implemented):

- [ ] Database integration (SQLite/PostgreSQL)
- [ ] User authentication system
- [ ] Multi-camera support
- [ ] Export data as CSV/JSON from dashboard
- [ ] Email/SMS alerts for specific waste types
- [ ] Integration with physical sorting mechanism
- [ ] Mobile app (iOS/Android)
- [ ] Voice announcements
- [ ] Advanced analytics and reporting
- [ ] Cloud deployment options

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Authors

- **Sarang Pratap** - [GitHub](https://github.com/SarangPratap)

---

## 🙏 Acknowledgments

- **Edge Impulse** - For ML model framework
- **Espressif** - For ESP32 platform
- **Flask** & **Socket.IO** - For backend infrastructure
- **PlatformIO** - For development environment

---

## 📧 Contact & Support

- **GitHub Issues:** [Report a bug](https://github.com/SarangPratap/Waste_Classification/issues)
- **Documentation:** [docs/](docs/)
- **Email:** [Your email if you want to add]

---

## ⭐ Show Your Support

If you find this project useful, please give it a ⭐ on GitHub!

---

<div align="center">
  Made with ❤️ for a cleaner planet 🌍
</div>
