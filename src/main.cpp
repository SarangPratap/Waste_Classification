/* Includes ---------------------------------------------------------------- */
#include <Waste_classification_inferencing.h>
#include "edge-impulse-sdk/dsp/image/image.hpp"
#include "esp_camera.h"
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Configuration
#include "config.h"

/* Camera model configuration ---------------------------------------------- */
#define CAMERA_MODEL_AI_THINKER 

#if defined(CAMERA_MODEL_AI_THINKER)
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
#endif

/* Constant defines -------------------------------------------------------- */
#define EI_CAMERA_RAW_FRAME_BUFFER_COLS           320
#define EI_CAMERA_RAW_FRAME_BUFFER_ROWS           240
#define EI_CAMERA_FRAME_BYTE_SIZE                 3

/* Private variables ------------------------------------------------------- */
static bool is_initialised = false;
static uint8_t *snapshot_buf = NULL;
bool inference_running = true;  // Control flag for pause/resume

/* WiFi globals ------------------------------------------------------------ */
AsyncWebServer server(80);

/* Camera configuration ---------------------------------------------------- */
static camera_config_t camera_config = {
    .pin_pwdn = PWDN_GPIO_NUM,
    .pin_reset = RESET_GPIO_NUM,
    .pin_xclk = XCLK_GPIO_NUM,
    .pin_sccb_sda = SIOD_GPIO_NUM,      // ✅ FIXED: was pin_sscb_sda
    .pin_sccb_scl = SIOC_GPIO_NUM,      // ✅ FIXED: was pin_sscb_scl
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
    .jpeg_quality = 12,
    .fb_count = 1,
    .fb_location = CAMERA_FB_IN_PSRAM,
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
};

/* Function declarations --------------------------------------------------- */
bool ei_camera_init(void);
void ei_camera_deinit(void);
bool ei_camera_capture(uint32_t img_width, uint32_t img_height, uint8_t *out_buf);
static int ei_camera_get_data(size_t offset, size_t length, float *out_ptr);
void setupWiFi(void);
void handleStream(AsyncWebServerRequest *request);
void sendPredictionToBackend(String category, float confidence);

/* Camera Functions -------------------------------------------------------- */
bool ei_camera_init(void) {
    if (is_initialised) return true;

    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed 0x%x\n", err);
        return false;
    }

    sensor_t *s = esp_camera_sensor_get();
    s->set_framesize(s, FRAMESIZE_QVGA);

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
        Serial.println("Capture failed");
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
        out_ptr[out_ptr_ix] = (snapshot_buf[pixel_ix] << 16) + (snapshot_buf[pixel_ix + 1] << 8) + snapshot_buf[pixel_ix + 2];
        out_ptr_ix++;
        pixel_ix += 3;
        bytes_left--;
    }
    return 0;
}

/* WiFi Functions ---------------------------------------------------------- */
void setupWiFi() {
    Serial.print("Connecting to WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✓ WiFi connected!");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n✗ WiFi connection failed. Continuing without WiFi.");
    }
}

/* MJPEG Streaming --------------------------------------------------------- */
void handleStream(AsyncWebServerRequest *request) {
    AsyncWebServerResponse *response = request->beginChunkedResponse("multipart/x-mixed-replace; boundary=frame", 
        [](uint8_t *buffer, size_t maxLen, size_t index) -> size_t {
            camera_fb_t *fb = esp_camera_fb_get();
            if (!fb) {
                return 0;
            }
            
            size_t len = 0;
            
            // Write frame header
            len = snprintf((char *)buffer, maxLen,
                          "--frame\r\n"
                          "Content-Type: image/jpeg\r\n"
                          "Content-Length: %u\r\n\r\n",
                          fb->len);
            
            // Check if frame data fits in remaining buffer
            // Note: If frames are consistently too large, consider adjusting
            // camera quality settings in camera_config.jpeg_quality
            if (len + fb->len + 2 <= maxLen) {
                memcpy(buffer + len, fb->buf, fb->len);
                len += fb->len;
                len += snprintf((char *)buffer + len, maxLen - len, "\r\n");
            } else {
                // Frame too large for buffer, skip this frame
                Serial.printf("Frame too large (%u bytes), skipping\n", fb->len);
                len = 0;
            }
            
            esp_camera_fb_return(fb);
            return len;
        });
    
    request->send(response);
}

/* Backend Communication --------------------------------------------------- */
void sendPredictionToBackend(String category, float confidence) {
    if (WiFi.status() != WL_CONNECTED) {
        return;  // Silently skip if no WiFi
    }
    
    HTTPClient http;
    String url = String("http://") + BACKEND_HOST + ":" + String(BACKEND_PORT) + "/api/prediction";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(1000);  // 1 second timeout to prevent inference delays
    
    StaticJsonDocument<200> doc;
    doc["category"] = category;
    doc["confidence"] = confidence;
    doc["device_id"] = "ESP32-CAM-001";
    doc["timestamp"] = millis();
    
    String json;
    serializeJson(doc, json);
    
    int httpCode = http.POST(json);
    
    if (httpCode > 0) {
        Serial.printf("Backend response: %d\n", httpCode);
    } else {
        Serial.printf("Backend error: %s\n", http.errorToString(httpCode).c_str());
    }
    
    http.end();
}

/* Arduino Setup ----------------------------------------------------------- */
void setup() {
    Serial.begin(115200);
    Serial.println("\n=================================");
    Serial.println("  Waste Classification System");
    Serial.println("  Edge Impulse + Web Dashboard");
    Serial.println("=================================\n");
    
    Serial.println("Commands: pause, resume, status, reset\n");

    // ✅ KEEP: Initialize camera with user's code
    if (!ei_camera_init()) {
        Serial.println("✗ Camera initialization failed!");
        while(1) { delay(1000); }
    }
    Serial.println("✓ Camera initialized");

    // ✅ NEW: Allocate snapshot buffer once (reuse throughout application)
    snapshot_buf = (uint8_t*)malloc(EI_CAMERA_RAW_FRAME_BUFFER_COLS * EI_CAMERA_RAW_FRAME_BUFFER_ROWS * EI_CAMERA_FRAME_BYTE_SIZE);
    if (!snapshot_buf) {
        Serial.println("✗ Failed to allocate snapshot buffer!");
        while(1) { delay(1000); }
    }
    Serial.println("✓ Snapshot buffer allocated");

    // ✅ NEW: Setup WiFi
    setupWiFi();
    
    // ✅ NEW: Setup web server (only if WiFi connected)
    if (WiFi.status() == WL_CONNECTED) {
        server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
            String html = "<html><body><h1>ESP32-CAM Waste Classifier</h1>";
            html += "<p>Stream: <a href='/stream'>/stream</a></p>";
            html += "<p>IP: " + WiFi.localIP().toString() + "</p>";
            html += "<p>Dashboard: http://" + String(BACKEND_HOST) + ":" + String(BACKEND_PORT) + "</p>";
            html += "</body></html>";
            request->send(200, "text/html", html);
        });
        
        server.on("/stream", HTTP_GET, handleStream);
        
        server.begin();
        Serial.println("✓ Web server started");
        Serial.printf("   Stream URL: http://%s/stream\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("⚠ Web server not started (no WiFi)");
    }
    
    Serial.println("\n=================================");
    Serial.println("System ready! Place item in view.");
    Serial.println("=================================\n");
}

/* Arduino Loop ------------------------------------------------------------ */
void loop() {
    // ✅ KEEP: Serial commands
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command == "pause") {
            inference_running = false;
            Serial.println(">>> Inference PAUSED");
        } 
        else if (command == "resume") {
            inference_running = true;
            Serial.println(">>> Inference RESUMED");
        }
        else if (command == "status") {
            Serial.print(">>> Status: ");
            Serial.println(inference_running ? "RUNNING" : "PAUSED");
            Serial.print(">>> WiFi: ");
            if (WiFi.status() == WL_CONNECTED) {
                Serial.println(WiFi.localIP());
            } else {
                Serial.println("Not connected");
            }
        }
        else if (command == "reset") {
            Serial.println(">>> Resetting ESP32...");
            delay(500);
            ESP.restart();
        }
    }

    if (!inference_running) {
        delay(100);
        return;
    }

    // ✅ MODIFIED: Capture image (buffer already allocated in setup)
    if (!ei_camera_capture((size_t)EI_CLASSIFIER_INPUT_WIDTH, (size_t)EI_CLASSIFIER_INPUT_HEIGHT, snapshot_buf)) {
        Serial.println("Capture failed");
        delay(1000);
        return;
    }

    // ✅ KEEP: Prepare signal for Edge Impulse
    ei::signal_t signal;
    signal.total_length = EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT;
    signal.get_data = &ei_camera_get_data;

    // ✅ KEEP: Run REAL classifier
    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);

    if (res != EI_IMPULSE_OK) {
        Serial.printf("Classifier failed %d\n", res);
        delay(1000);
        return;
    }

    // ✅ KEEP: Process results
    Serial.println("Predictions:");
    float best = 0;
    int best_ix = -1;
    String best_category = "";
    
    for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        Serial.printf("%s: %.2f\n", result.classification[ix].label, result.classification[ix].value);
        if (result.classification[ix].value > best) {
            best = result.classification[ix].value;
            best_ix = ix;
            best_category = String(result.classification[best_ix].label);
        }
    }

    // ✅ KEEP + NEW: Display AND send to backend
    if (best > 0.6) {
        Serial.printf(">>> %s (%.0f%%)\n", best_category.c_str(), best * 100);
        
        // ✅ NEW: Send REAL prediction to web dashboard
        sendPredictionToBackend(best_category, best);
    } else {
        Serial.println(">>> Unknown (confidence too low)");
    }

    Serial.println("---");
    delay(2000);
}