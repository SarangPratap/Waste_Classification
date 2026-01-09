# Setup Guide - ESP32-CAM Waste Classification System

## 📋 Prerequisites

### Hardware Requirements
- **ESP32-CAM** module (AI Thinker model)
- **USB to Serial adapter** (FTDI or CP2102) for programming
- **Power supply** (5V, minimum 500mA)
- **Computer** (Windows/Mac/Linux) connected to same WiFi network

### Software Requirements
- **PlatformIO** (VSCode extension or CLI)
- **Python 3.8+** (for Flask backend)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)
- **WiFi network** (2.4GHz - ESP32 doesn't support 5GHz)

---

## 🔧 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/SarangPratap/Waste_Classification.git
cd Waste_Classification
```

### Step 2: Configure WiFi and Backend Settings

Edit `include/config.h` and update the following:

```cpp
// Update with your WiFi credentials
#define WIFI_SSID "Your_WiFi_Name"
#define WIFI_PASSWORD "Your_WiFi_Password"

// Update with your computer's IP address
#define BACKEND_HOST "192.168.1.100"  // Find using: ipconfig (Windows) or ifconfig (Mac/Linux)
#define BACKEND_PORT 5000
```

**How to find your computer's IP address:**
- **Windows:** Open Command Prompt → Type `ipconfig` → Look for "IPv4 Address"
- **Mac:** Open Terminal → Type `ifconfig` → Look for "inet" under your network adapter
- **Linux:** Open Terminal → Type `hostname -I` or `ip addr show`

### Step 3: Flash ESP32-CAM Firmware

**Using PlatformIO VSCode Extension:**

1. Open the project folder in VSCode
2. Install PlatformIO extension if not already installed
3. Connect ESP32-CAM to computer via USB-to-Serial adapter:
   - **ESP32-CAM TX** → **RX** on adapter
   - **ESP32-CAM RX** → **TX** on adapter
   - **ESP32-CAM GND** → **GND** on adapter
   - **ESP32-CAM 5V** → **5V** on adapter
   - **Connect GPIO 0 to GND** for programming mode
4. Update `platformio.ini` with your COM port (e.g., COM3, /dev/ttyUSB0)
5. Click **PlatformIO: Upload** button
6. After successful upload, **disconnect GPIO 0 from GND** and press reset

**Using PlatformIO CLI:**

```bash
# Install PlatformIO CLI
pip install platformio

# Build and upload
pio run --target upload

# Monitor serial output
pio device monitor
```

### Step 4: Verify ESP32-CAM Connection

Open Serial Monitor (115200 baud) and you should see:

```
🗑️ ESP32-CAM Waste Classification System
==========================================
Initializing camera...
✅ Camera initialized successfully
Connecting to WiFi...
✅ WiFi connected!
IP address: 192.168.1.50
Setting up web server...
✅ Web server started

✅ System ready!
==========================================
Commands: pause, resume, status, reset
MJPEG Stream: http://192.168.1.50/stream
==========================================
```

**Note the IP address** - you'll need it to connect the video stream.

### Step 5: Install Python Dependencies

Navigate to the `server` directory and install dependencies:

```bash
cd server
pip install -r requirements.txt
```

**Troubleshooting:** If you encounter errors:
- Use `pip3` instead of `pip` on Mac/Linux
- Create a virtual environment first:
  ```bash
  python -m venv venv
  source venv/bin/activate  # Mac/Linux
  venv\Scripts\activate     # Windows
  pip install -r requirements.txt
  ```

### Step 6: Start Flask Backend Server

```bash
python app.py
```

You should see:

```
🗑️ Waste Classification Backend Server
==================================================
Server starting on http://localhost:5000
Dashboard: http://localhost:5000
API: http://localhost:5000/api/*
==================================================
```

### Step 7: Open Web Dashboard

1. Open your web browser
2. Navigate to: `http://localhost:5000` or `http://YOUR_COMPUTER_IP:5000`
3. Enter the ESP32-CAM IP address (from Step 4) in the input field
4. Click **"Connect Stream"**

You should now see:
- ✅ Live video feed from ESP32-CAM
- ✅ Real-time waste classification predictions
- ✅ Prediction history
- ✅ Statistics dashboard

---

## 🎮 Serial Commands

You can control the ESP32-CAM via Serial Monitor:

- **`pause`** - Stop inference temporarily
- **`resume`** - Resume inference
- **`status`** - Display system status (WiFi, IP, memory, etc.)
- **`reset`** - Restart the ESP32-CAM

---

## 🔍 Troubleshooting

### ESP32-CAM won't connect to WiFi

**Problem:** "WiFi connection failed" message  
**Solutions:**
- Verify SSID and password are correct in `config.h`
- Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Check power supply is sufficient (minimum 500mA)
- Try moving closer to WiFi router
- Disable WiFi isolation/AP isolation in router settings

### Camera initialization failed

**Problem:** "Camera init failed with error 0x..."  
**Solutions:**
- Check all camera pins are properly connected
- Ensure ESP32-CAM module has PSRAM
- Try lowering `CAMERA_QUALITY` value in `config.h`
- Power cycle the ESP32-CAM

### Video stream not loading

**Problem:** "Failed to connect to stream" in browser  
**Solutions:**
- Verify ESP32-CAM IP address is correct
- Ensure computer and ESP32 are on same WiFi network
- Try accessing `http://ESP_IP/status` to test connectivity
- Disable firewall temporarily to test
- Check browser console for error messages

### Predictions not appearing in dashboard

**Problem:** No predictions showing up  
**Solutions:**
- Verify Flask server is running
- Check `BACKEND_HOST` in `config.h` matches computer's IP
- Check Flask console for incoming POST requests
- Verify confidence threshold (must be > 60%)
- Check browser console for WebSocket connection errors

### Upload fails to ESP32-CAM

**Problem:** "Timed out waiting for packet header"  
**Solutions:**
- Ensure GPIO 0 is connected to GND during upload
- Press reset button on ESP32-CAM before uploading
- Try lowering `upload_speed` in `platformio.ini` (e.g., 115200 → 9600)
- Check USB cable and connections
- Try different USB port

### Python dependencies installation fails

**Problem:** pip install errors  
**Solutions:**
- Update pip: `pip install --upgrade pip`
- Install missing build tools (especially on Windows)
- Use Python 3.8-3.11 (avoid 3.12 for better compatibility)
- Try installing packages individually if requirements.txt fails

---

## 🌐 Network Configuration

### Port Forwarding (Optional)

To access dashboard from outside your local network:

1. Forward port 5000 on your router to your computer's IP
2. Access using: `http://YOUR_PUBLIC_IP:5000`
3. **Security Warning:** Only do this if you understand the security implications

### Running on Different Port

To run Flask on a different port, edit `server/app.py`:

```python
socketio.run(app, host='0.0.0.0', port=8080, debug=True)
```

And update `BACKEND_PORT` in `include/config.h` accordingly.

---

## 📱 Mobile Access

The dashboard is fully responsive and works on mobile devices:

1. Ensure your phone is on the same WiFi network
2. Access: `http://YOUR_COMPUTER_IP:5000`
3. Enter ESP32-CAM IP and connect

---

## 🔄 Updating the System

### Update ESP32 Firmware:
```bash
cd /path/to/Waste_Classification
pio run --target upload
```

### Update Backend:
```bash
cd server
git pull
pip install -r requirements.txt --upgrade
python app.py
```

---

## 💡 Tips for Best Results

1. **Good Lighting:** Ensure adequate lighting for camera
2. **Stable Power:** Use quality power supply (brownouts cause issues)
3. **Network Stability:** Use stable WiFi connection
4. **Camera Position:** Mount camera at appropriate angle/distance
5. **Clean Lens:** Keep camera lens clean for better accuracy
6. **Monitor Serial:** Keep Serial Monitor open to debug issues

---

## 🆘 Getting Help

If you encounter issues not covered here:

1. Check Serial Monitor output for error messages
2. Check Flask console for backend errors
3. Check browser console (F12) for JavaScript errors
4. Review `server/data/predictions.csv` for logged data
5. Open an issue on GitHub with:
   - Error messages
   - Serial output
   - Flask console output
   - Steps to reproduce

---

## 🚀 Next Steps

Once everything is working:

- Review `docs/API.md` for API integration
- Customize confidence threshold in `config.h`
- Adjust inference interval (default 2 seconds)
- Train custom Edge Impulse model for your specific waste types
- Integrate with physical sorting mechanism (servos, etc.)

---

**Congratulations! Your ESP32-CAM Waste Classification System is now operational! 🎉**
