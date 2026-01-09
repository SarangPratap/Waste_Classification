# API Documentation - Waste Classification System

## Overview

This document describes the REST API and WebSocket events for the ESP32-CAM Waste Classification System backend.

**Base URL:** `http://localhost:5000`  
**Protocol:** HTTP/1.1  
**Response Format:** JSON  
**WebSocket Protocol:** Socket.IO v4

---

## REST API Endpoints

### 1. GET `/`

**Description:** Serve the web dashboard  
**Authentication:** None  
**Response:** HTML page

**Example:**
```bash
curl http://localhost:5000/
```

---

### 2. POST `/api/prediction`

**Description:** Receive a prediction from ESP32-CAM  
**Authentication:** None  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "category": "plastic",
  "confidence": 0.87,
  "device_id": "ESP32-CAM-001",
  "timestamp": 123456789
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| category | string | Yes | Waste category name (battery, biological, cardboard, clothes, glass, metal, paper, plastic, shoe) |
| confidence | float | Yes | Confidence score (0.0 - 1.0) |
| device_id | string | Yes | Unique identifier for the ESP32-CAM device |
| timestamp | integer | No | Unix timestamp in milliseconds |

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Prediction received"
}
```

**Error Response (400):**
```json
{
  "status": "error",
  "message": "Invalid request format"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/prediction \
  -H "Content-Type: application/json" \
  -d '{
    "category": "plastic",
    "confidence": 0.87,
    "device_id": "ESP32-CAM-001",
    "timestamp": 1704816000000
  }'
```

**Notes:**
- Predictions are automatically broadcast to all connected WebSocket clients
- Data is logged to `data/predictions.csv`
- Only last 50 predictions are kept in memory

---

### 3. GET `/api/predictions`

**Description:** Retrieve recent predictions  
**Authentication:** None

**Query Parameters:** None

**Success Response (200):**
```json
{
  "status": "success",
  "predictions": [
    {
      "category": "plastic",
      "confidence": 0.87,
      "device_id": "ESP32-CAM-001",
      "timestamp": "2024-01-09T12:00:00.123456"
    },
    {
      "category": "paper",
      "confidence": 0.92,
      "device_id": "ESP32-CAM-001",
      "timestamp": "2024-01-09T12:00:02.456789"
    }
  ]
}
```

**Error Response (500):**
```json
{
  "status": "error",
  "message": "Internal server error"
}
```

**Example:**
```bash
curl http://localhost:5000/api/predictions
```

**Notes:**
- Returns last 50 predictions in chronological order
- Timestamps are in ISO 8601 format

---

### 4. GET `/api/stats`

**Description:** Get classification statistics  
**Authentication:** None

**Query Parameters:** None

**Success Response (200):**
```json
{
  "status": "success",
  "stats": {
    "total_classifications": 42,
    "category_counts": {
      "plastic": 15,
      "paper": 12,
      "cardboard": 8,
      "glass": 5,
      "metal": 2
    },
    "average_confidence": 0.853,
    "most_common_category": "plastic",
    "average_confidence_per_category": {
      "plastic": 0.87,
      "paper": 0.91,
      "cardboard": 0.78,
      "glass": 0.85,
      "metal": 0.82
    }
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| total_classifications | integer | Total number of predictions received |
| category_counts | object | Count of predictions per category |
| average_confidence | float | Overall average confidence score |
| most_common_category | string | Category with highest count |
| average_confidence_per_category | object | Average confidence per category |

**Error Response (500):**
```json
{
  "status": "error",
  "message": "Internal server error"
}
```

**Example:**
```bash
curl http://localhost:5000/api/stats
```

---

## WebSocket Events

The system uses Socket.IO for real-time communication.

**Connection URL:** `http://localhost:5000`  
**Transport:** WebSocket (fallback to long-polling)

### Client → Server Events

#### `connect`

**Description:** Automatically emitted when client connects

**Example (JavaScript):**
```javascript
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected to server');
  console.log('Socket ID:', socket.id);
});
```

#### `disconnect`

**Description:** Automatically emitted when client disconnects

**Example (JavaScript):**
```javascript
socket.on('disconnect', () => {
  console.log('Disconnected from server');
});
```

---

### Server → Client Events

#### `connection_status`

**Description:** Sent immediately after connection  
**Payload:**
```json
{
  "status": "connected"
}
```

**Example (JavaScript):**
```javascript
socket.on('connection_status', (data) => {
  console.log('Connection status:', data.status);
});
```

#### `new_prediction`

**Description:** Broadcast to all connected clients when new prediction is received  
**Trigger:** When ESP32-CAM sends POST to `/api/prediction`

**Payload:**
```json
{
  "category": "plastic",
  "confidence": 0.87,
  "device_id": "ESP32-CAM-001",
  "timestamp": "2024-01-09T12:00:00.123456"
}
```

**Example (JavaScript):**
```javascript
socket.on('new_prediction', (data) => {
  console.log('New prediction:', data);
  // Update UI with prediction data
  updateUI(data.category, data.confidence);
});
```

---

## Integration Examples

### ESP32-CAM (Arduino C++)

```cpp
#include <HTTPClient.h>
#include <ArduinoJson.h>

void sendPrediction(String category, float confidence) {
  HTTPClient http;
  http.begin("http://192.168.1.100:5000/api/prediction");
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["category"] = category;
  doc["confidence"] = confidence;
  doc["device_id"] = "ESP32-CAM-001";
  doc["timestamp"] = millis();
  
  String json;
  serializeJson(doc, json);
  
  int httpCode = http.POST(json);
  http.end();
}
```

### Python Client

```python
import requests
import socketio

# REST API
def send_prediction(category, confidence):
    url = 'http://localhost:5000/api/prediction'
    data = {
        'category': category,
        'confidence': confidence,
        'device_id': 'python-client',
        'timestamp': int(time.time() * 1000)
    }
    response = requests.post(url, json=data)
    return response.json()

# WebSocket
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Connected to server')

@sio.on('new_prediction')
def on_prediction(data):
    print(f"Prediction: {data['category']} ({data['confidence']:.2%})")

sio.connect('http://localhost:5000')
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');
const io = require('socket.io-client');

// REST API
async function sendPrediction(category, confidence) {
  const response = await axios.post('http://localhost:5000/api/prediction', {
    category: category,
    confidence: confidence,
    device_id: 'nodejs-client',
    timestamp: Date.now()
  });
  return response.data;
}

// WebSocket
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected to server');
});

socket.on('new_prediction', (data) => {
  console.log(`Prediction: ${data.category} (${data.confidence * 100}%)`);
});
```

### cURL Examples

**Send Prediction:**
```bash
curl -X POST http://localhost:5000/api/prediction \
  -H "Content-Type: application/json" \
  -d '{
    "category": "plastic",
    "confidence": 0.87,
    "device_id": "curl-client",
    "timestamp": 1704816000000
  }'
```

**Get Recent Predictions:**
```bash
curl http://localhost:5000/api/predictions | jq
```

**Get Statistics:**
```bash
curl http://localhost:5000/api/stats | jq '.stats'
```

---

## Error Codes

| HTTP Code | Description | Common Causes |
|-----------|-------------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid JSON format or missing required fields |
| 404 | Not Found | Invalid endpoint URL |
| 500 | Internal Server Error | Server-side error (check logs) |

---

## Rate Limiting

Currently, there are **no rate limits** implemented. For production use, consider:
- Implementing rate limiting per device_id
- Using authentication tokens
- Setting up request quotas

---

## Data Storage

### CSV Format

Predictions are logged to `server/data/predictions.csv`:

```csv
timestamp,category,confidence,device_id
2024-01-09T12:00:00.123456,plastic,0.87,ESP32-CAM-001
2024-01-09T12:00:02.456789,paper,0.92,ESP32-CAM-001
2024-01-09T12:00:04.789012,cardboard,0.78,ESP32-CAM-001
```

**Fields:**
- `timestamp` - ISO 8601 format
- `category` - Waste category name
- `confidence` - Float (0.0 - 1.0)
- `device_id` - Device identifier

### Memory Storage

- Last **50 predictions** kept in memory
- Cleared on server restart
- Used for `/api/predictions` endpoint

---

## CORS Configuration

CORS is enabled for all origins (`*`). For production:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://192.168.1.100:5000"]
    }
})
```

---

## WebSocket Configuration

Default configuration:
- **Protocol:** Socket.IO v4
- **Transports:** WebSocket, polling
- **Path:** `/socket.io/`
- **CORS:** Allowed for all origins

---

## Testing the API

### Using Postman

1. Import the following collection:
   - POST `http://localhost:5000/api/prediction`
   - GET `http://localhost:5000/api/predictions`
   - GET `http://localhost:5000/api/stats`

2. Set headers:
   - `Content-Type: application/json`

3. Test WebSocket using Postman WebSocket feature

### Using Python Script

```python
import requests
import time

# Test prediction endpoint
for i in range(5):
    category = ['plastic', 'paper', 'cardboard', 'glass', 'metal'][i]
    response = requests.post('http://localhost:5000/api/prediction', json={
        'category': category,
        'confidence': 0.7 + (i * 0.05),
        'device_id': 'test-device',
        'timestamp': int(time.time() * 1000)
    })
    print(f"Sent {category}: {response.status_code}")
    time.sleep(1)

# Get statistics
stats = requests.get('http://localhost:5000/api/stats').json()
print(f"Total classifications: {stats['stats']['total_classifications']}")
```

---

## Best Practices

1. **Always include device_id** for tracking multiple devices
2. **Use confidence threshold** (e.g., >0.6) before sending predictions
3. **Handle network errors** gracefully in ESP32 code
4. **Monitor CSV file size** - implement rotation if needed
5. **Use WebSocket** for real-time updates instead of polling
6. **Validate data** before sending to API
7. **Log timestamps** for debugging and analysis

---

## Future API Enhancements

Planned for future versions:
- Authentication with JWT tokens
- User management endpoints
- Device registration and management
- Historical data queries with date ranges
- Export endpoints (CSV, JSON)
- Webhook support for alerts
- GraphQL API option
- REST pagination for large datasets

---

For questions or issues, please open an issue on GitHub.
