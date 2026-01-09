# 🗑️ Waste Classification System

AI-powered waste classification using ESP32-CAM with Edge Impulse machine learning and real-time web dashboard.

## ✨ Features

- ✅ **Real Edge Impulse ML Model Integration** - Uses your actual trained model (not simulated predictions)
- 📷 **ESP32-CAM Live Streaming** - MJPEG video stream over WiFi
- 🌐 **Web Dashboard Integration** - Sends predictions to backend server
- 🎯 **High Accuracy Classification** - Identifies waste types (cardboard, glass, metal, paper, plastic, trash)
- 🔌 **Offline Mode Support** - Works without WiFi for local inference
- 💻 **Serial Control Interface** - Pause, resume, status, reset commands

## 🚀 Quick Start

### Prerequisites

- ESP32-CAM board (AI Thinker model)
- USB-to-Serial adapter (FTDI, CP2102, etc.)
- PlatformIO or Arduino IDE
- Trained Edge Impulse model for waste classification
- WiFi network (2.4 GHz)

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/SarangPratap/Waste_Classification.git
cd Waste_Classification
```

#### 2. Install Edge Impulse Model
Follow the detailed guide: [docs/EDGE_IMPULSE_INTEGRATION.md](docs/EDGE_IMPULSE_INTEGRATION.md)

**Quick version:**
1. Download your trained model from [Edge Impulse Studio](https://studio.edgeimpulse.com)
2. Extract and copy to `lib/Waste_classification_inferencing/`

#### 3. Configure WiFi
```bash
# Copy template
cp include/config.h.example include/config.h

# Edit with your credentials
nano include/config.h
```

Update:
```cpp
#define WIFI_SSID "your_wifi_name"
#define WIFI_PASSWORD "your_password"
#define BACKEND_HOST "192.168.1.100"  // Your computer's IP
```

See detailed guide: [docs/WIFI_SETUP.md](docs/WIFI_SETUP.md)

#### 4. Build and Upload
```bash
# Using PlatformIO
pio run --target upload

# Monitor serial output
pio device monitor
```

### First Run

After uploading, you should see:
```
=================================
  Waste Classification System
  Edge Impulse + Web Dashboard
=================================

✓ Camera initialized
✓ WiFi connected!
IP address: 192.168.1.150
✓ Web server started
   Stream URL: http://192.168.1.150/stream

=================================
System ready! Place item in view.
=================================
```

## 📊 Usage

### Serial Commands

Send commands through serial monitor (115200 baud):

- `pause` - Pause inference
- `resume` - Resume inference  
- `status` - Show system status and WiFi info
- `reset` - Restart ESP32

### Web Interface

Access camera stream:
```
http://[ESP32_IP_ADDRESS]/stream
```

Example: `http://192.168.1.150/stream`

### Inference Output

Example serial output:
```
Predictions:
cardboard: 0.02
glass: 0.01
metal: 0.03
paper: 0.89
plastic: 0.04
trash: 0.01
>>> paper (89%)
---
Backend response: 200
```

## 🏗️ Architecture

```
┌─────────────────┐
│   ESP32-CAM     │
│  ┌───────────┐  │
│  │  Camera   │  │──┐
│  └───────────┘  │  │ Captures Image
│                 │  │
│  ┌───────────┐  │  │
│  │Edge Impulse│◄─┘
│  │   Model   │  │
│  └───────────┘  │
│       │         │
│       ▼         │
│  Classification │
└────────┬────────┘
         │
         ├──► Serial Monitor (Local Output)
         │
         └──► WiFi ──► Web Dashboard (Remote Display)
```

## 📁 Project Structure

```
Waste_Classification/
├── docs/
│   ├── EDGE_IMPULSE_INTEGRATION.md  # Model setup guide
│   ├── WIFI_SETUP.md                # Network configuration guide
│   └── README.md                    # Documentation index
├── include/
│   ├── config.h.example             # Configuration template
│   └── config.h                     # Your actual config (git-ignored)
├── lib/
│   └── Waste_classification_inferencing/  # Your Edge Impulse model (add this)
├── src/
│   └── main.cpp                     # Main application code
├── platformio.ini                   # PlatformIO configuration
└── README.md                        # This file
```

## 🔧 Configuration

### Camera Settings
- Resolution: 320x240 (QVGA)
- Format: RGB888
- Frame rate: ~0.5 FPS (2 second delay between inferences)

### ML Model Requirements
- Input: 320x240 RGB images
- Output: Classification probabilities
- Optimization: Quantized int8 (recommended)
- Confidence threshold: 0.6 (60%)

### Network Settings
- WiFi: 2.4 GHz only
- Web server: Port 80
- Backend API: Configurable (default: port 5000)

## 🐛 Troubleshooting

### Camera Issues
**"Camera init failed 0x20001"**
- Check ribbon cable connection
- Ensure proper pin configuration

### WiFi Issues
**"WiFi connection failed"**
- Verify 2.4 GHz network (ESP32 doesn't support 5 GHz)
- Check credentials in `config.h`
- System works offline if WiFi unavailable

### Model Issues
**"Waste_classification_inferencing.h: No such file"**
- Edge Impulse library not installed
- See [EDGE_IMPULSE_INTEGRATION.md](docs/EDGE_IMPULSE_INTEGRATION.md)

### Build Issues
**"Region `dram0_0_seg' overflowed"**
- Ensure `huge_app.csv` partition scheme is set in `platformio.ini`
- Check that PSRAM is enabled

See detailed troubleshooting in documentation guides.

## 🔐 Security

- WiFi credentials stored in `config.h` (git-ignored)
- Use `config.h.example` for version control
- HTTPS not implemented (local network only)
- No authentication on web endpoints

**⚠️ For production use:**
- Implement authentication
- Use HTTPS/TLS
- Secure credential storage
- Network isolation

## 📚 Documentation

Comprehensive guides available in [`docs/`](docs/):

1. **[Edge Impulse Integration](docs/EDGE_IMPULSE_INTEGRATION.md)**
   - Model download and installation
   - Verification steps
   - Model updates
   - Performance optimization

2. **[WiFi Setup](docs/WIFI_SETUP.md)**
   - Network configuration
   - Troubleshooting connectivity
   - Static IP setup
   - Remote access options

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- [Edge Impulse](https://edgeimpulse.com/) - ML model training platform
- [Espressif](https://www.espressif.com/) - ESP32 platform
- [PlatformIO](https://platformio.org/) - Development environment

## 📞 Support

- Issues: [GitHub Issues](https://github.com/SarangPratap/Waste_Classification/issues)
- Documentation: [`docs/`](docs/)
- Edge Impulse Forum: [forum.edgeimpulse.com](https://forum.edgeimpulse.com/)

## 🚦 System Status

| Feature | Status |
|---------|--------|
| Edge Impulse Integration | ✅ Working |
| Camera Capture | ✅ Working |
| ML Inference | ✅ Working |
| WiFi Connectivity | ✅ Working |
| MJPEG Streaming | ✅ Working |
| Backend Communication | ✅ Working |
| Serial Commands | ✅ Working |
| Offline Mode | ✅ Working |

---

**Made with ❤️ for a cleaner planet 🌍**
