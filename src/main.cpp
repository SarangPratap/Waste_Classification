/* Edge Impulse + Arcade Dashboard - Working Version for PlatformIO */
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESPAsyncWebServer.h>
#include <Waste_classification_inferencing.h>
#include "edge-impulse-sdk/dsp/image/image.hpp"
#include "esp_camera.h"

/* Configuration ---------------------------------------------------------- */
#define WIFI_SSID "SARANG's Galaxy S22+"
#define WIFI_PASSWORD "tfru4008"
#define BACKEND_HOST "10.111.150.17"  // Your PC IP running Arcade
#define BACKEND_PORT 5000

/* Hardware Defines ------------------------------------------------------- */
#define STATUS_LED 4                   // GPIO4 onboard LED
#define CAMERA_QUALITY 12              // JPEG quality 0-63, lower is better
#define CONFIDENCE_THRESHOLD 0.6       // 60% confidence threshold
#define INFERENCE_INTERVAL 3000        // 3 seconds between inferences (captures image & detects)

/* Camera Pins ------------------------------------------------------------ */
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define EI_CAMERA_RAW_FRAME_BUFFER_COLS  320
#define EI_CAMERA_RAW_FRAME_BUFFER_ROWS  240

/* Global Variables ------------------------------------------------------- */
static bool is_initialised = false;
static uint8_t *snapshot_buf = NULL;
bool inference_running = true;
unsigned long lastInferenceTime = 0;
String lastCategory = "Waiting...";
float lastConfidence = 0.0;

// Web server on port 80 for video streaming
AsyncWebServer server(80);

/* Camera Configuration --------------------------------------------------- */
static camera_config_t camera_config = {
    .pin_pwdn = PWDN_GPIO_NUM,
    .pin_reset = RESET_GPIO_NUM,
    .pin_xclk = XCLK_GPIO_NUM,
    .pin_sccb_sda = SIOD_GPIO_NUM,
    .pin_sccb_scl = SIOC_GPIO_NUM,
    .pin_d7 = Y9_GPIO_NUM,
    .pin_d6 = Y8_GPIO_NUM,
    .pin_d5 = Y7_GPIO_NUM,
    .pin_d4 = Y6_GPIO_NUM,
    .pin_d3 = Y5_GPIO_NUM,
    .pin_d2 = Y4_GPIO_NUM,
    .pin_d1 = Y3_GPIO_NUM,
    .pin_d0 = Y2_GPIO_NUM,
    .pin_vsync = VSYNC_GPIO_NUM,
    .pin_href = HREF_GPIO_NUM,
    .pin_pclk = PCLK_GPIO_NUM,
    .xclk_freq_hz = 20000000,
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,
    .pixel_format = PIXFORMAT_JPEG,
    .frame_size = FRAMESIZE_QVGA,
    .jpeg_quality = CAMERA_QUALITY,
    .fb_count = 1,
    .fb_location = CAMERA_FB_IN_PSRAM,
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
};

/* Camera Functions ------------------------------------------------------- */
bool ei_camera_init(void) {
    if (is_initialised) return true;

    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed 0x%x\n", err);
        return false;
    }

    sensor_t *s = esp_camera_sensor_get();
    if (s) {
        s->set_framesize(s, FRAMESIZE_QVGA);
    }

    is_initialised = true;
    return true;
}

void ei_camera_deinit(void) {
    esp_camera_deinit();
    is_initialised = false;
}

bool ei_camera_capture(uint32_t img_width, uint32_t img_height, uint8_t *out_buf) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("Camera capture failed");
        return false;
    }

    bool converted = fmt2rgb888(fb->buf, fb->len, fb->format, out_buf);
    esp_camera_fb_return(fb);
    
    if (!converted) {
        Serial.println("Conversion failed");
        return false;
    }
    return true;
}

static int ei_camera_get_data(size_t offset, size_t length, float *out_ptr) {
    size_t pixel_ix = offset * 3;
    size_t bytes_left = length;
    size_t out_ptr_ix = 0;

    while (bytes_left != 0) {
        out_ptr[out_ptr_ix] = (snapshot_buf[pixel_ix] << 16) + 
                              (snapshot_buf[pixel_ix + 1] << 8) + 
                              snapshot_buf[pixel_ix + 2];
        out_ptr_ix++;
        pixel_ix += 3;
        bytes_left--;
    }
    return 0;
}

/* Arcade Dashboard Integration ------------------------------------------- */
void sendPredictionToBackend(String category, float confidence) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi not connected, skipping backend");
        return;
    }
    
    HTTPClient http;
    String url = "http://" + String(BACKEND_HOST) + ":" + String(BACKEND_PORT) + "/api/prediction";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(3000);
    
    JsonDocument doc;
    doc["category"] = category;
    doc["confidence"] = confidence;
    doc["device_id"] = "ESP32-CAM-001";
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    
    if (httpCode > 0) {
        Serial.printf("✓ Sent to Arcade: HTTP %d\n", httpCode);
    } else {
        Serial.printf("✗ Send failed: %s\n", http.errorToString(httpCode).c_str());
    }
    
    http.end();
}

/* Web Server for Video Streaming ----------------------------------------- */
void handleSnapshot(AsyncWebServerRequest *request) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        request->send(503, "text/plain", "Camera capture failed");
        return;
    }
    
    AsyncWebServerResponse *response = request->beginResponse_P(
        200, "image/jpeg", fb->buf, fb->len
    );
    response->addHeader("Access-Control-Allow-Origin", "*");
    response->addHeader("Cache-Control", "no-cache, no-store, must-revalidate");
    request->send(response);
    esp_camera_fb_return(fb);
}

void handleStream(AsyncWebServerRequest *request) {
    // MJPEG streaming using chunked response
    AsyncWebServerResponse *response = request->beginChunkedResponse(
        "multipart/x-mixed-replace; boundary=frame",
        [](uint8_t *buffer, size_t maxLen, size_t index) -> size_t {
            camera_fb_t *fb = esp_camera_fb_get();
            if (!fb) return 0;
            
            size_t len = 0;
            // Frame header
            len = snprintf((char *)buffer, maxLen,
                "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
                fb->len);
            
            // Check if frame fits in buffer
            if (len + fb->len + 2 <= maxLen) {
                memcpy(buffer + len, fb->buf, fb->len);
                len += fb->len;
                len += snprintf((char *)buffer + len, maxLen - len, "\r\n");
            } else {
                len = 0;  // Frame too large, skip
            }
            
            esp_camera_fb_return(fb);
            return len;
        }
    );
    response->addHeader("Access-Control-Allow-Origin", "*");
    request->send(response);
}

void setupWebServer() {
    // Root page
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        String html = "<html><head><title>ESP32-CAM</title></head><body>";
        html += "<h1>ESP32-CAM Waste Classifier</h1>";
        html += "<p>Status: " + String(inference_running ? "Running" : "Paused") + "</p>";
        html += "<p>Last: " + lastCategory + " (" + String(lastConfidence * 100, 1) + "%)</p>";
        html += "<p><a href='/stream'>MJPEG Stream</a></p>";
        html += "<p><a href='/snapshot'>Snapshot</a></p>";
        html += "<p>Arcade Dashboard: http://" + String(BACKEND_HOST) + ":" + String(BACKEND_PORT) + "</p>";
        html += "<hr><img src='/stream' width='640'>";
        html += "</body></html>";
        request->send(200, "text/html", html);
    });
    
    // Snapshot endpoint (single JPEG)
    server.on("/snapshot", HTTP_GET, handleSnapshot);
    
    // Stream endpoint (MJPEG)
    server.on("/stream", HTTP_GET, handleStream);
    
    // Status endpoint (JSON)
    server.on("/status", HTTP_GET, [](AsyncWebServerRequest *request) {
        JsonDocument doc;
        doc["status"] = inference_running ? "running" : "paused";
        doc["wifi"] = WiFi.status() == WL_CONNECTED;
        doc["ip"] = WiFi.localIP().toString();
        doc["category"] = lastCategory;
        doc["confidence"] = lastConfidence;
        
        String json;
        serializeJson(doc, json);
        
        AsyncWebServerResponse *response = request->beginResponse(200, "application/json", json);
        response->addHeader("Access-Control-Allow-Origin", "*");
        request->send(response);
    });
    
    server.begin();
    Serial.println("✓ Web server started on port 80");
}

void setupWiFi() {
    Serial.println("\n=== WiFi Setup ===");
    Serial.printf("Connecting to: %s\n", WIFI_SSID);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✓ WiFi Connected!");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
        Serial.printf("Stream: http://%s:81 (for Arcade)\n", WiFi.localIP().toString().c_str());
        Serial.printf("Dashboard: http://%s:%d\n", BACKEND_HOST, BACKEND_PORT);
        digitalWrite(STATUS_LED, HIGH);
    } else {
        Serial.println("\n✗ WiFi Failed - running offline");
        digitalWrite(STATUS_LED, LOW);
    }
}

/* Setup ------------------------------------------------------------------ */
void setup() {
    // CRITICAL: Serial.begin MUST be first!
    Serial.begin(115200);
    delay(1000);  // Wait for USB to stabilize
    
    // Optional: Now we can set buffer size (after begin)
    Serial.setTxBufferSize(1024);
    
    // Header
    Serial.println("\n\n");
    Serial.println("╔════════════════════════════════════════════╗");
    Serial.println("║  ESP32-CAM Waste Classification System     ║");
    Serial.println("║  With Arcade Dashboard Integration         ║");
    Serial.println("╚════════════════════════════════════════════╝");
    Serial.println();
    
    // Setup LED
    pinMode(STATUS_LED, OUTPUT);
    digitalWrite(STATUS_LED, LOW);
    
    // Initialize camera
    Serial.println("Initializing camera...");
    if (!ei_camera_init()) {
        Serial.println("✗ Camera initialization failed!");
        while(1) { 
            digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
            delay(200); 
        }
    }
    Serial.println("✓ Camera initialized");
    
    // Setup WiFi
    setupWiFi();
    
    // Setup web server for video streaming (only if WiFi connected)
    if (WiFi.status() == WL_CONNECTED) {
        setupWebServer();
        Serial.printf("   Snapshot: http://%s/snapshot\n", WiFi.localIP().toString().c_str());
        Serial.printf("   Stream:   http://%s/stream\n", WiFi.localIP().toString().c_str());
    }
    
    Serial.println("\n=== System Ready ===");
    Serial.println("Commands: pause, resume, status, reset");
    Serial.println("=============================\n");
    
    lastInferenceTime = millis();
}

/* Main Loop -------------------------------------------------------------- */
void loop() {
    // Handle serial commands
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        command.toLowerCase();
        
        if (command == "pause") {
            inference_running = false;
            Serial.println(">>> Inference PAUSED");
        } 
        else if (command == "resume") {
            inference_running = true;
            Serial.println(">>> Inference RESUMED");
        }
        else if (command == "status") {
            Serial.println("\n=== System Status ===");
            Serial.printf("Inference: %s\n", inference_running ? "RUNNING" : "PAUSED");
            Serial.printf("WiFi: %s\n", WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
            if (WiFi.status() == WL_CONNECTED) {
                Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
            }
            Serial.println("====================\n");
        }
        else if (command == "reset") {
            Serial.println(">>> Resetting ESP32...");
            delay(500);
            ESP.restart();
        }
        else {
            Serial.println(">>> Unknown command. Use: pause, resume, status, reset");
        }
    }

    // Check WiFi reconnection
    if (WiFi.status() != WL_CONNECTED) {
        static unsigned long lastReconnect = 0;
        if (millis() - lastReconnect > 30000) {
            Serial.println("WiFi disconnected, attempting reconnect...");
            WiFi.reconnect();
            lastReconnect = millis();
        }
    }

    // Skip inference if paused
    if (!inference_running) {
        delay(100);
        return;
    }

    // Check interval
    if (millis() - lastInferenceTime < INFERENCE_INTERVAL) {
        delay(10);
        return;
    }
    lastInferenceTime = millis();

    // Run inference
    Serial.println("\n📸 Capturing and classifying...");
    
    snapshot_buf = (uint8_t*)malloc(EI_CAMERA_RAW_FRAME_BUFFER_COLS * 
                                     EI_CAMERA_RAW_FRAME_BUFFER_ROWS * 3);
    if (!snapshot_buf) {
        Serial.println("✗ Memory allocation failed!");
        delay(1000);
        return;
    }

    if (!ei_camera_capture((size_t)EI_CLASSIFIER_INPUT_WIDTH, 
                           (size_t)EI_CLASSIFIER_INPUT_HEIGHT, 
                           snapshot_buf)) {
        free(snapshot_buf);
        delay(1000);
        return;
    }

    ei::signal_t signal;
    signal.total_length = EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT;
    signal.get_data = &ei_camera_get_data;

    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);

    if (res != EI_IMPULSE_OK) {
        Serial.printf("✗ Classifier failed: %d\n", res);
        free(snapshot_buf);
        delay(1000);
        return;
    }

    // Process results
    Serial.println("\n=== Classification Results ===");
    float best_confidence = 0;
    int best_index = -1;
    String best_category = "";
    
    for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        float confidence = result.classification[ix].value;
        String label = String(result.classification[ix].label);
        Serial.printf("  %s: %.2f%%\n", label.c_str(), confidence * 100);
        
        if (confidence > best_confidence) {
            best_confidence = confidence;
            best_index = ix;
            best_category = label;
        }
    }

    // Handle detection
    if (best_confidence > CONFIDENCE_THRESHOLD) {
        Serial.printf("\n✓ DETECTED: %s (%.1f%%)\n", 
                     best_category.c_str(), best_confidence * 100);
        
        lastCategory = best_category;
        lastConfidence = best_confidence;
        
        // Send to Arcade Dashboard
        sendPredictionToBackend(best_category, best_confidence);
        
        // Blink LED 3 times
        for(int i = 0; i < 3; i++) {
            digitalWrite(STATUS_LED, LOW);
            delay(100);
            digitalWrite(STATUS_LED, HIGH);
            delay(100);
        }
    } else {
        Serial.printf("\n✗ Low confidence: %.1f%% (need >%.0f%%)\n", 
                     best_confidence * 100, CONFIDENCE_THRESHOLD * 100);
        lastCategory = "Unknown";
        lastConfidence = best_confidence;
    }

    Serial.println("==============================\n");
    free(snapshot_buf);
}