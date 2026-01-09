# WiFi Setup Guide

## 📡 Network Configuration

The ESP32-CAM needs to connect to your WiFi network to enable:
- Live camera streaming via MJPEG
- Sending predictions to the web dashboard backend
- Remote monitoring and control

## 🔧 Configuration Steps

### 1. Edit Configuration File

Open `include/config.h` and update with your network details:

```cpp
// WiFi Configuration
#define WIFI_SSID "your_wifi_ssid"          // Replace with your WiFi name
#define WIFI_PASSWORD "your_wifi_password"  // Replace with your WiFi password

// Backend Configuration
#define BACKEND_HOST "192.168.1.100"        // Your computer's IP address
#define BACKEND_PORT 5000                   // Backend server port (default: 5000)
```

### 2. Find Your Computer's IP Address

#### Windows:
```cmd
ipconfig
```
Look for "IPv4 Address" under your active network adapter (e.g., `192.168.1.100`).

#### macOS/Linux:
```bash
ifconfig
# or
ip addr show
```
Look for `inet` address under your active network interface (e.g., `inet 192.168.1.100`).

**Note:** You need your **local/private IP** address on your network, not your public internet IP. Local addresses typically start with:
- `192.168.x.x` (most common for home networks)
- `10.x.x.x` (large private networks)
- `172.16.0.0` to `172.31.255.255` (medium private networks)

### 3. Important WiFi Requirements

✅ **ESP32 supports:**
- 2.4 GHz WiFi networks only
- WPA/WPA2 security
- DHCP (automatic IP assignment)

❌ **ESP32 does NOT support:**
- 5 GHz WiFi networks
- Enterprise WiFi (WPA2-Enterprise)
- Hidden SSIDs (limited support)

## 🌐 Network Modes

### Mode 1: Same Network (Recommended)
Both ESP32-CAM and your computer on the same WiFi network.

```
Router (192.168.1.1)
    ├── Computer (192.168.1.100)
    └── ESP32-CAM (192.168.1.150)
```

**Setup:**
- Connect computer to WiFi
- Configure ESP32 with same WiFi credentials
- Use computer's local IP in `BACKEND_HOST`

### Mode 2: Offline (No WiFi)
ESP32-CAM works without WiFi for inference only.

```
ESP32-CAM (standalone)
```

**Limitations:**
- No web streaming
- No dashboard integration
- Serial monitor output only

## 📝 Example Configurations

### Home Network
```cpp
#define WIFI_SSID "MyHomeNetwork"
#define WIFI_PASSWORD "mypassword123"
#define BACKEND_HOST "192.168.1.100"
#define BACKEND_PORT 5000
```

### Office Network
```cpp
#define WIFI_SSID "Office-Guest"
#define WIFI_PASSWORD "guest2024"
#define BACKEND_HOST "10.0.0.45"
#define BACKEND_PORT 5000
```

### Mobile Hotspot
```cpp
#define WIFI_SSID "iPhone"
#define WIFI_PASSWORD "hotspot123"
#define BACKEND_HOST "172.20.10.1"
#define BACKEND_PORT 5000
```

## 🔍 Testing Connection

### Step 1: Upload and Monitor
```bash
pio run --target upload && pio device monitor
```

### Step 2: Check Serial Output
Look for:
```
Connecting to WiFi.......
✓ WiFi connected!
IP address: 192.168.1.150
✓ Web server started
   Stream URL: http://192.168.1.150/stream
```

### Step 3: Test Camera Stream
Open browser and navigate to:
```
http://[ESP32_IP_ADDRESS]/stream
```

### Step 4: Verify Dashboard Connection
Check serial output for:
```
Backend response: 200
```
This confirms predictions are being sent to the backend.

## 🚨 Troubleshooting

### "WiFi connection failed"

**Check 1: Correct Credentials**
- Verify SSID spelling (case-sensitive)
- Verify password (case-sensitive)
- Remove any special quotes or spaces

**Check 2: 2.4GHz Network**
```
✅ Router set to 2.4 GHz mode
❌ Router in 5 GHz only mode
```

Many modern routers broadcast both. Ensure 2.4GHz is enabled.

**Check 3: Signal Strength**
- Move ESP32-CAM closer to router
- Check for interference (microwaves, other devices)
- Use WiFi analyzer app to check signal

**Check 4: Router Settings**
- Disable MAC address filtering (temporarily for testing)
- Enable DHCP
- Check maximum client limit

### "Backend error: connection refused"

**Check 1: Backend Server Running**
```bash
# Verify backend is running on specified port
netstat -an | grep 5000
```

**Check 2: Firewall Settings**
- Allow incoming connections on port 5000
- Add exception for Python/Node.js (backend server)

**Check 3: Correct IP Address**
```bash
# Verify computer's IP hasn't changed
ipconfig  # Windows
ifconfig  # macOS/Linux
```

**Check 4: Both on Same Network**
```bash
# From computer, ping ESP32
ping 192.168.1.150
```

### "Cannot access stream URL"

**Check 1: ESP32 IP Address**
- Note IP from serial output
- May change if router reboots

**Check 2: Firewall/Antivirus**
- Temporarily disable to test
- Add exception for port 80

**Check 3: Browser**
- Try different browser (Chrome, Firefox, Safari)
- Clear cache and cookies

**Check 4: Same Network**
- Computer must be on same WiFi network as ESP32
- Disable VPN if active

## 🔐 Security Best Practices

### Development
```cpp
// OK for development - Easy to change
#define WIFI_SSID "TestNetwork"
#define WIFI_PASSWORD "test1234"
```

### Production
```cpp
// Use strong passwords
#define WIFI_SSID "SecureNetwork"
#define WIFI_PASSWORD "Str0ng!P@ssw0rd#2024"
```

### Git Repository
Add to `.gitignore`:
```
include/config.h
```

Create `config.h.example`:
```cpp
// Copy to config.h and fill in your credentials
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"
#define BACKEND_HOST "192.168.1.100"
#define BACKEND_PORT 5000
```

## 📊 Network Monitoring

### Check Connection Status
Serial command:
```
status
```

Output:
```
>>> Status: RUNNING
>>> WiFi: 192.168.1.150
```

### Monitor Backend Communication
Watch serial output for:
```
Backend response: 200  ✅ Success
Backend response: 404  ❌ Endpoint not found
Backend error: connection refused  ❌ Server not running
```

## 🔄 Dynamic IP vs Static IP

### Dynamic IP (Default)
- IP assigned automatically by router
- May change after router reboot
- Suitable for development

### Static IP (Advanced)
Modify `main.cpp` after `WiFi.begin()`:

```cpp
IPAddress local_IP(192, 168, 1, 150);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("Static IP configuration failed");
}
```

Benefits:
- Consistent IP address
- Easier to bookmark
- Recommended for production

## 📱 Mobile Access

Access ESP32-CAM from smartphone on same network:

1. Connect phone to same WiFi
2. Open browser
3. Navigate to: `http://[ESP32_IP]:80/stream`

**Tip:** Use QR code generator for easy access:
```
http://192.168.1.150/stream
```

## 🌍 Remote Access (Advanced)

⚠️ **Security Warning:** Only for advanced users

### Option 1: Port Forwarding
Configure router to forward external port to ESP32 internal IP.

### Option 2: VPN
Use VPN service (Tailscale, ZeroTier) for secure remote access.

### Option 3: Reverse Proxy
Use ngrok or similar service (not recommended for production).

## 📚 Additional Resources

- [ESP32 WiFi Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_wifi.html)
- [Router Configuration Guides](https://www.192-168-1-1-ip.co/)
- [Network Troubleshooting Tools](https://www.wireshark.org/)

## 💡 Tips

1. **Use WiFi analyzer app** to find best channel
2. **Keep router firmware updated** for stability
3. **Reserve DHCP IP** in router for consistent address
4. **Document your setup** for future reference
5. **Test connection** before final deployment
