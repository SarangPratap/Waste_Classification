# 🗑️ ESP32-CAM Waste Classification System

[![PlatformIO](https://img.shields.io/badge/PlatformIO-ESP32-orange.svg)](https://platformio.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Arcade](https://img.shields.io/badge/Arcade-3.0+-green.svg)](https://api.arcade.academy/)
[![Edge Impulse](https://img.shields.io/badge/Edge%20Impulse-ML-purple.svg)](https://edgeimpulse.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An **Edge AI-powered waste classification system** using ESP32-CAM with on-device machine learning inference. Features a retro-styled **Arcade dashboard** for real-time monitoring with live video streaming and prediction visualization.

<div align="center">
  <img src="https://img.shields.io/badge/Status-Active-success" alt="Status">
  <img src="https://img.shields.io/badge/Hardware-ESP32--CAM-blue" alt="Hardware">
  <img src="https://img.shields.io/badge/ML-Edge%20Impulse-purple" alt="ML Framework">
  <img src="https://img.shields.io/badge/Categories-9-brightgreen" alt="Categories">
</div>

---

## 📸 Dashboard Preview

<div align="center">
  
  <!-- TODO: Add your screenshot here -->
  <!-- Example: <img src="docs/images/dashboard_screenshot.png" alt="Arcade Dashboard" width="800"> -->
  
  *🎮 Retro Arcade-style Dashboard with live camera feed and real-time predictions*
  
  **[Add your dashboard screenshot here]**
  
</div>

---

## ✨ Features

### 🎯 Edge AI Classification
- **9 Waste Categories**: Battery, Biological, Cardboard, Clothes, Glass, Metal, Paper, Plastic, Shoe
- **On-Device Inference**: ML model runs directly on ESP32-CAM (no cloud required)
- **60% Confidence Threshold**: Only high-confidence predictions are reported
- **3-Second Inference Interval**: Balanced between responsiveness and performance

### 📹 Live Video Streaming
- **MJPEG Stream**: Real-time video from ESP32-CAM at 320x240
- **Snapshot Endpoint**: On-demand image capture
- **Low Latency**: Direct camera-to-dashboard streaming

### 🎮 Arcade Dashboard
- **Retro Gaming Aesthetic**: CRT scanline effects, neon colors, pixel-style fonts
- **Live Camera Feed**: Embedded video stream with overlay
- **Real-time Predictions**: Animated category display with confidence bars
- **Statistics Panel**: Total counts, category distribution, session stats
- **Prediction History**: Color-coded scrolling list of recent detections
- **Connection Status**: Visual indicators for ESP32 and stream connectivity

### 🌐 System Features
- **WiFi Auto-Reconnection**: Robust connectivity handling
- **HTTP API**: RESTful endpoints for predictions and status
- **CSV Logging**: Automatic prediction logging for analysis
- **Serial Commands**: Runtime control via serial monitor
- **Status LED**: Visual feedback on ESP32-CAM

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ESP32-CAM                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Camera    │→ │  Edge AI    │→ │   Async Web Server      │  │
│  │  OV2640     │  │  Inference  │  │  - /stream (MJPEG)      │  │
│  └─────────────┘  └─────────────┘  │  - /snapshot (JPEG)     │  │
│                                    │  - /status (JSON)       │  │
│                                    └───────────┬─────────────┘  │
└────────────────────────────────────────────────┼────────────────┘
                                                 │
                        WiFi Network             │
                                                 │
┌────────────────────────────────────────────────┼────────────────┐
│                   Arcade Dashboard (Python)    │                │
│  ┌─────────────────┐  ┌───────────────────────▼──────────────┐  │
│  │  HTTP Server    │  │      Video Thread                    │  │
│  │  (Port 5000)    │  │  - MJPEG Stream Consumer             │  │
│  │  - Predictions  │  │  - Frame Queue Management            │  │
│  └────────┬────────┘  └──────────────────────────────────────┘  │
│           │                                                     │
│  ┌────────▼────────────────────────────────────────────────┐    │
│  │              Arcade Game Window                          │    │
│  │  - Live Video Panel    - Stats Panel                     │    │
│  │  - Prediction Display  - History List                    │    │
│  │  - CRT Effects         - Connection Status               │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Component | Requirement |
|-----------|-------------|
| **Hardware** | ESP32-CAM (AI-Thinker), USB-to-Serial adapter |
| **Software** | Python 3.8+, PlatformIO (VS Code extension) |
| **Network** | 2.4GHz WiFi (ESP32 doesn't support 5GHz) |

### 1️⃣ Clone Repository

```bash
git clone https://github.com/SarangPratap/Waste_Classification.git
cd Waste_Classification
```

### 2️⃣ Configure ESP32-CAM

Edit WiFi and backend settings in `src/main.cpp`:

```cpp
#define WIFI_SSID "Your_WiFi_Name"
#define WIFI_PASSWORD "Your_WiFi_Password"
#define BACKEND_HOST "192.168.1.100"  // Your PC's IP address
#define BACKEND_PORT 5000
```

### 3️⃣ Flash ESP32-CAM

```bash
# Using PlatformIO CLI
pio run --target upload

# Monitor serial output (115200 baud)
pio device monitor -b 115200
```

> **Note:** After uploading, press the reset button on your ESP32-CAM.

### 4️⃣ Setup Dashboard

```bash
cd dashboard
pip install -r requirements_arcade.txt
```

### 5️⃣ Configure Dashboard

Edit `dashboard/config.json`:

```json
{
  "esp32_ip": "YOUR_ESP32_IP",
  "stream_port": 80,
  "http_port": 5000,
  "confidence_threshold": 0.6,
  "window_width": 1400,
  "window_height": 900,
  "enable_scanlines": true,
  "max_history": 20
}
```

> **Tip:** Find ESP32's IP from the Serial Monitor output after WiFi connects.

### 6️⃣ Run Dashboard

```bash
cd dashboard
python arcade_dashboard.py
```

**🎉 Done! The dashboard will open with live video and predictions.**

---

## 🎨 Waste Categories

| Category | Icon | Color | Examples |
|----------|:----:|-------|----------|
| **Battery** | 🔋 | Gold | AA/AAA batteries, power cells, lithium batteries |
| **Biological** | 🍎 | Lime Green | Food waste, fruit peels, organic matter |
| **Cardboard** | 📦 | Brown | Boxes, packaging, corrugated cardboard |
| **Clothes** | 👕 | Purple | Textiles, fabrics, garments |
| **Glass** | 🫙 | Turquoise | Bottles, jars, glass containers |
| **Metal** | 🔩 | Gray | Cans, foil, metal objects, screws |
| **Paper** | 📄 | Sky Blue | Documents, newspapers, notebooks |
| **Plastic** | 🍾 | Blue | Bottles, containers, plastic bags |
| **Shoe** | 👟 | Orange | Footwear, sneakers, sandals |

---

## 📁 Project Structure

```
Waste_Classification/
├── 📄 platformio.ini           # PlatformIO build configuration
├── 📄 README.md                # This file
│
├── 📂 src/
│   └── main.cpp                # ESP32-CAM firmware (WiFi, Camera, ML, Web Server)
│
├── 📂 include/
│   ├── config.h                # Hardware configuration
│   └── camera_pins.h           # ESP32-CAM pin definitions
│
├── 📂 lib/
│   └── Waste_classification_inferencing/  # Edge Impulse ML model
│       ├── src/
│       │   ├── edge-impulse-sdk/          # EI SDK
│       │   ├── model-parameters/          # Model config
│       │   └── tflite-model/              # TensorFlow Lite model
│       └── examples/                      # Platform examples
│
├── 📂 dashboard/
│   ├── arcade_dashboard.py     # Python Arcade dashboard application
│   ├── config.json             # Dashboard configuration
│   ├── requirements_arcade.txt # Python dependencies
│   ├── predictions_log.csv     # Logged predictions (auto-generated)
│   └── dashboard.log           # Application logs (auto-generated)
│
├── 📂 docs/
│   ├── SETUP.md                # Detailed setup guide
│   ├── API.md                  # API documentation
│   ├── EDGE_IMPULSE_INTEGRATION.md  # ML model integration guide
│   └── WIFI_SETUP.md           # WiFi troubleshooting
│
└── 📂 test/                    # Test files
```

---

## 🔌 API Reference

### ESP32-CAM Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stream` | GET | MJPEG video stream |
| `/snapshot` | GET | Single JPEG image |
| `/status` | GET | System status (JSON) |

### Dashboard HTTP Server (Port 5000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/prediction` | POST | Receive prediction from ESP32 |

### Example: Status Response

```json
{
  "status": "running",
  "wifi": true,
  "ip": "192.168.1.50",
  "category": "plastic",
  "confidence": 0.87
}
```

---

## ⚙️ Configuration Reference

### ESP32 Settings (`src/main.cpp`)

| Define | Default | Description |
|--------|---------|-------------|
| `WIFI_SSID` | - | Your WiFi network name |
| `WIFI_PASSWORD` | - | Your WiFi password |
| `BACKEND_HOST` | - | Dashboard PC's IP address |
| `BACKEND_PORT` | 5000 | Dashboard HTTP port |
| `CONFIDENCE_THRESHOLD` | 0.6 | Minimum confidence (0.0-1.0) |
| `INFERENCE_INTERVAL` | 3000 | Time between inferences (ms) |
| `CAMERA_QUALITY` | 12 | JPEG quality (0-63, lower=better) |

### Dashboard Settings (`dashboard/config.json`)

| Key | Default | Description |
|-----|---------|-------------|
| `esp32_ip` | - | ESP32-CAM's IP address |
| `stream_port` | 80 | ESP32 web server port |
| `http_port` | 5000 | Dashboard prediction server port |
| `confidence_threshold` | 0.6 | Display threshold |
| `window_width` | 1400 | Dashboard window width |
| `window_height` | 900 | Dashboard window height |
| `enable_scanlines` | true | CRT scanline effect |
| `max_history` | 20 | Prediction history length |

---

## 🔧 Serial Commands

Control ESP32-CAM via Serial Monitor (115200 baud):

| Command | Description |
|---------|-------------|
| `pause` | Pause ML inference |
| `resume` | Resume ML inference |
| `status` | Show system status |
| `reset` | Restart ESP32-CAM |

---

## 🐛 Troubleshooting

### ESP32-CAM Issues

| Problem | Solution |
|---------|----------|
| **WiFi won't connect** | Verify credentials, ensure 2.4GHz network, check power supply (500mA min) |
| **Camera init failed** | Check PSRAM, verify pin connections, try lower quality setting |
| **Brownout detected** | Use better power supply, add capacitor, reduce WiFi transmit power |
| **Upload fails** | Connect GPIO0 to GND during upload, use shorter USB cable |

### Dashboard Issues

| Problem | Solution |
|---------|----------|
| **Can't connect to stream** | Verify ESP32 IP in config.json, ensure same WiFi network |
| **Stream disconnects** | Check WiFi signal strength, reduce inference interval |
| **Window won't open** | Install/update graphics drivers, check arcade installation |
| **Unicode errors in logs** | Windows console issue, logs still work in file |

### Network Issues

| Problem | Solution |
|---------|----------|
| **Predictions not received** | Check `BACKEND_HOST` matches your PC's IP |
| **High latency** | Reduce `CAMERA_QUALITY`, increase `INFERENCE_INTERVAL` |
| **Connection refused** | Ensure dashboard is running before ESP32 sends predictions |

---

## 🛠️ Hardware Requirements

### Required
- **ESP32-CAM** (AI-Thinker module with OV2640 camera)
- **USB-to-Serial Adapter** (FTDI FT232RL or CP2102)




---

## 🔮 Future Enhancements

- [ ] Multi-camera support
- [ ] Cloud dashboard deployment
- [ ] Mobile app companion
- [ ] Physical sorting mechanism integration
- [ ] Voice announcements
- [ ] Advanced analytics & reporting
- [ ] Model retraining interface

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

## 👨‍💻 Author

**Sarang Pratap** - [GitHub](https://github.com/SarangPratap)

---

## 🙏 Acknowledgments

- **[Edge Impulse](https://edgeimpulse.com/)** - ML model training and deployment
- **[Espressif](https://www.espressif.com/)** - ESP32 platform
- **[PlatformIO](https://platformio.org/)** - Development environment
- **[Arcade Library](https://api.arcade.academy/)** - Python game framework for dashboard

---

## ⭐ Support

If you find this project useful, please give it a ⭐ on GitHub!

**Found a bug?** [Open an issue](https://github.com/SarangPratap/Waste_Classification/issues)

---

<div align="center">
  
  Made with ❤️ for a cleaner planet 🌍
  
  *Reduce • Reuse • Recycle • Classify*
  
</div>
