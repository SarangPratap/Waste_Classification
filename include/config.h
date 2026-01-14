#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration (user will update these)
#define WIFI_SSID "SARANG's Galaxy S22+"
#define WIFI_PASSWORD "tfru4008"

// Backend Server Configuration
#define BACKEND_HOST "10.208.253.17"  // User's laptop IP
#define BACKEND_PORT 5000

// Camera Settings
// Increase value for faster streaming (lower JPEG quality)
#define CAMERA_QUALITY 10  // 0-63, lower means higher quality
#define INFERENCE_INTERVAL 3000  // 3 seconds

// LED Pins
#define STATUS_LED 33
#define FLASH_LED 4

// Confidence Threshold
#define CONFIDENCE_THRESHOLD 0.6

#endif // CONFIG_H
