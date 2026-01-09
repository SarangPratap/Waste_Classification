#include <Arduino.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include "esp_timer.h"
#include "config.h"
#include "camera_pins.h"

// Global variables
AsyncWebServer server(80);
camera_fb_t * fb = NULL;

// Inference state
bool inference_enabled = true;
unsigned long last_inference_time = 0;
String last_category = "none";
float last_confidence = 0.0;

// Waste categories (matching Edge Impulse model)
const char* waste_categories[] = {
  "battery", "biological", "cardboard", "clothes", 
  "glass", "metal", "paper", "plastic", "shoe"
};
const int num_categories = 9;

// WiFi connection status
bool wifi_connected = false;

// Function declarations
void setupCamera();
void setupWiFi();
void setupWebServer();
void handleStream(AsyncWebServerRequest *request);
void runInference();
void sendPredictionToBackend(String category, float confidence);
void handleSerialCommands();
void blinkStatusLED(int times);

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n🗑️ ESP32-CAM Waste Classification System");
  Serial.println("==========================================");
  
  // Setup status LED
  pinMode(STATUS_LED, OUTPUT);
  pinMode(FLASH_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);
  digitalWrite(FLASH_LED, LOW);
  
  // Initialize camera
  Serial.println("Initializing camera...");
  setupCamera();
  
  // Connect to WiFi
  Serial.println("Connecting to WiFi...");
  setupWiFi();
  
  // Setup web server
  Serial.println("Setting up web server...");
  setupWebServer();
  
  Serial.println("\n✅ System ready!");
  Serial.println("==========================================");
  Serial.println("Commands: pause, resume, status, reset");
  Serial.println("MJPEG Stream: http://" + WiFi.localIP().toString() + "/stream");
  Serial.println("==========================================\n");
  
  blinkStatusLED(3);
}

void loop() {
  // Handle serial commands
  handleSerialCommands();
  
  // Run inference at specified interval
  if (inference_enabled && (millis() - last_inference_time >= INFERENCE_INTERVAL)) {
    runInference();
    last_inference_time = millis();
  }
  
  // Blink status LED to show system is alive
  static unsigned long last_blink = 0;
  if (millis() - last_blink >= 2000) {
    digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    last_blink = millis();
  }
  
  delay(10);
}

void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Init with high specs for streaming
  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA; // 640x480
    config.jpeg_quality = CAMERA_QUALITY;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed with error 0x%x\n", err);
    return;
  }
  
  Serial.println("✅ Camera initialized successfully");
}

void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifi_connected = true;
    Serial.println("\n✅ WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    wifi_connected = false;
    Serial.println("\n❌ WiFi connection failed!");
    Serial.println("⚠️  System will continue without network features");
  }
}

void setupWebServer() {
  // Root endpoint - redirect to dashboard
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    String backend_url = "http://" + String(BACKEND_HOST) + ":" + String(BACKEND_PORT);
    request->redirect(backend_url);
  });
  
  // MJPEG stream endpoint
  server.on("/stream", HTTP_GET, handleStream);
  
  // Status endpoint
  server.on("/status", HTTP_GET, [](AsyncWebServerRequest *request){
    StaticJsonDocument<200> doc;
    doc["status"] = "online";
    doc["inference_enabled"] = inference_enabled;
    doc["last_category"] = last_category;
    doc["last_confidence"] = last_confidence;
    doc["wifi"] = wifi_connected;
    
    String json;
    serializeJson(doc, json);
    request->send(200, "application/json", json);
  });
  
  server.begin();
  Serial.println("✅ Web server started");
}

void handleStream(AsyncWebServerRequest *request) {
  // Note: This is a simplified stream handler
  // For production MJPEG streaming, consider using esp32-camera's built-in stream server
  // or a dedicated streaming library
  
  AsyncWebServerResponse *response = request->beginResponse(
    200, 
    "multipart/x-mixed-replace; boundary=frame",
    "Streaming not fully implemented. Use ESP32-CAM example stream server."
  );
  
  request->send(response);
  
  // TODO: For full MJPEG implementation, use:
  // 1. httpd_handle from esp_http_server.h for proper streaming
  // 2. Or integrate CameraWebServer example from esp32-camera library
  // 3. Current AsyncWebServer approach requires complex state management
}

void runInference() {
  // Capture image
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Camera capture failed");
    return;
  }
  
  digitalWrite(STATUS_LED, HIGH);
  
  // NOTE: This is a simulated inference since we don't have the actual Edge Impulse model
  // In production, you would:
  // 1. Include the Edge Impulse library: #include <Waste_classification_inferencing.h>
  // 2. Convert frame buffer to format expected by model
  // 3. Run: ei_impulse_result_t result; run_classifier(&signal, &result);
  // 4. Extract predictions from result.classification
  
  // Simulate inference (replace with actual Edge Impulse code)
  int predicted_index = random(0, num_categories);
  float confidence = 0.5 + (random(0, 50) / 100.0); // Random confidence 0.5-0.99
  
  String category = waste_categories[predicted_index];
  
  // Store last prediction
  last_category = category;
  last_confidence = confidence;
  
  // Print to serial
  Serial.printf("📊 Prediction: %s (%.2f%%)\n", category.c_str(), confidence * 100);
  
  // Send to backend if confidence meets threshold
  if (confidence >= CONFIDENCE_THRESHOLD && wifi_connected) {
    sendPredictionToBackend(category, confidence);
  }
  
  // Return frame buffer
  esp_camera_fb_return(fb);
  
  digitalWrite(STATUS_LED, LOW);
}

void sendPredictionToBackend(String category, float confidence) {
  if (!wifi_connected) return;
  
  HTTPClient http;
  String url = "http://" + String(BACKEND_HOST) + ":" + String(BACKEND_PORT) + "/api/prediction";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["category"] = category;
  doc["confidence"] = confidence;
  doc["device_id"] = "ESP32-CAM-001";
  doc["timestamp"] = millis();
  
  String json;
  serializeJson(doc, json);
  
  int httpCode = http.POST(json);
  
  if (httpCode > 0) {
    Serial.printf("✅ Sent to backend: %s\n", json.c_str());
  } else {
    Serial.printf("❌ Backend error: %s\n", http.errorToString(httpCode).c_str());
  }
  
  http.end();
}

void handleSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    command.toLowerCase();
    
    if (command == "pause") {
      inference_enabled = false;
      Serial.println("⏸️  Inference paused");
    } 
    else if (command == "resume") {
      inference_enabled = true;
      Serial.println("▶️  Inference resumed");
    } 
    else if (command == "status") {
      Serial.println("\n📊 System Status:");
      Serial.println("==========================================");
      Serial.printf("WiFi: %s\n", wifi_connected ? "Connected" : "Disconnected");
      Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
      Serial.printf("Inference: %s\n", inference_enabled ? "Enabled" : "Paused");
      Serial.printf("Last prediction: %s (%.2f%%)\n", last_category.c_str(), last_confidence * 100);
      Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
      Serial.println("==========================================\n");
    } 
    else if (command == "reset") {
      Serial.println("🔄 Resetting system...");
      ESP.restart();
    } 
    else {
      Serial.println("❓ Unknown command. Available: pause, resume, status, reset");
    }
  }
}

void blinkStatusLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(STATUS_LED, HIGH);
    delay(200);
    digitalWrite(STATUS_LED, LOW);
    delay(200);
  }
}