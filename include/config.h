#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration (user will update these)
#define WIFI_SSID "6a"
#define WIFI_PASSWORD "thorsten!!!"

// Backend Server Configuration
#define BACKEND_HOST "192.168.1.100"  // User's laptop IP
#define BACKEND_PORT 5000

// Camera Settings
#define CAMERA_QUALITY 12  // 0-63, lower means higher quality
#define INFERENCE_INTERVAL 2000  // 2 seconds

// LED Pins
#define STATUS_LED 33
#define FLASH_LED 4

// Confidence Threshold
#define CONFIDENCE_THRESHOLD 0.6

#endif // CONFIG_H
