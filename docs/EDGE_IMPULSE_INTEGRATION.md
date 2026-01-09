# Edge Impulse Model Integration Guide

## ⚠️ CRITICAL: Your Edge Impulse Library is Required!

This project requires YOUR trained Edge Impulse model to function. The model is NOT included in this repository because it's specific to your training data.

## 📥 Step 1: Download Your Model

1. Go to your Edge Impulse project: https://studio.edgeimpulse.com
2. Navigate to **Deployment** tab
3. Select **Arduino library**
4. Select optimization: **Quantized (int8)**
5. Enable **EON Compiler** (optional, for better performance)
6. Click **Build**
7. Download the `.zip` file (e.g., `Waste_classification_inferencing.zip`)

## 📂 Step 2: Extract and Install

### Method A: PlatformIO (Recommended)

```bash
# 1. Extract the downloaded .zip file
unzip Waste_classification_inferencing.zip

# 2. Copy the entire folder to your project's lib directory
cp -r Waste_classification_inferencing/ /path/to/Waste_Classification/lib/

# Your structure should look like:
# Waste_Classification/
# ├── lib/
# │   └── Waste_classification_inferencing/
# │       ├── src/
# │       ├── edge-impulse-sdk/
# │       ├── model-parameters/
# │       └── library.json
# ├── src/
# │   └── main.cpp
# └── platformio.ini
```

### Method B: Arduino IDE

1. Open Arduino IDE
2. Go to **Sketch** → **Include Library** → **Add .ZIP Library**
3. Select the downloaded `.zip` file
4. Restart Arduino IDE

## ✅ Step 3: Verify Installation

The code includes this line:
```cpp
#include <Waste_classification_inferencing.h>
```

This will work automatically once you've placed the library in the correct location.

### Verify in PlatformIO:
```bash
pio lib list
```

You should see `Waste_classification_inferencing` in the output.

## 🔧 Step 4: Configure WiFi (Optional)

If you want to use the web dashboard features:

1. Edit `include/config.h`
2. Replace WiFi credentials:
```cpp
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"
```

3. Set your backend server (computer running the web dashboard):
```cpp
#define BACKEND_HOST "192.168.1.100"  // Your computer's IP
#define BACKEND_PORT 5000
```

## 📤 Step 5: Upload to ESP32-CAM

### Using PlatformIO:
```bash
pio run --target upload
```

### Using Arduino IDE:
1. Select **Tools** → **Board** → **ESP32 Arduino** → **AI Thinker ESP32-CAM**
2. Select correct COM port
3. Click **Upload**
4. Press the **RST** button on ESP32-CAM after upload

## 🖥️ Step 6: Monitor Serial Output

```bash
# PlatformIO
pio device monitor

# Arduino IDE
Tools → Serial Monitor (115200 baud)
```

You should see:
```
=================================
  Waste Classification System
  Edge Impulse + Web Dashboard
=================================

✓ Camera initialized
✓ WiFi connected!
IP address: 192.168.1.xxx
✓ Web server started
   Stream URL: http://192.168.1.xxx/stream

=================================
System ready! Place item in view.
=================================
```

## 🎮 Serial Commands

Send these commands through Serial Monitor:

- `pause` - Stop inference temporarily
- `resume` - Resume inference
- `status` - Show system status
- `reset` - Restart ESP32

## 🌐 Accessing the Camera Stream

Once connected to WiFi, access the camera stream at:
```
http://[ESP32_IP_ADDRESS]/stream
```

Example: `http://192.168.1.150/stream`

## 🚨 Troubleshooting

### "Waste_classification_inferencing.h: No such file"
✅ **Solution:** The Edge Impulse library is not installed. Follow Step 2 again.

### "Camera init failed 0x20001"
✅ **Solution:** Check camera ribbon cable connection. Make sure it's properly inserted.

### "WiFi connection failed"
✅ **Solution:** 
- Check WiFi credentials in `config.h`
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- The system works without WiFi (offline inference only)

### "Malloc failed"
✅ **Solution:** 
- Ensure `huge_app.csv` partition is being used
- Check that PSRAM is enabled in `platformio.ini`

### Predictions are always "Unknown"
✅ **Solution:**
- Retrain your model with more diverse data
- Adjust confidence threshold (currently 0.6) in `main.cpp`
- Ensure proper lighting conditions

## 📊 Model Information

Your Edge Impulse model should include:

- **Input:** 320x240 RGB images
- **Output:** Classification labels (e.g., "cardboard", "glass", "metal", "paper", "plastic", "trash")
- **Format:** Quantized int8 for optimal performance

## 🔄 Updating Your Model

To update your model with new training data:

1. Retrain in Edge Impulse Studio
2. Download new Arduino library
3. Replace the old library in `lib/` folder
4. Rebuild and upload to ESP32-CAM

## 📚 Additional Resources

- [Edge Impulse Documentation](https://docs.edgeimpulse.com/)
- [ESP32-CAM Guide](https://randomnerdtutorials.com/esp32-cam-video-streaming-face-recognition-arduino-ide/)
- [PlatformIO Documentation](https://docs.platformio.org/)

## ⚡ Performance Tips

1. **Enable EON Compiler** when deploying - reduces inference time
2. **Use Quantized (int8)** optimization - smaller model, faster inference
3. **Good lighting** - improves accuracy significantly
4. **Proper distance** - keep objects 10-30cm from camera
5. **Stable mounting** - reduce motion blur

## 🔐 Security Notes

- WiFi credentials are stored in plain text in `config.h`
- Do not commit `config.h` with real credentials to public repositories
- Consider using environment variables for production deployments
