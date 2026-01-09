# Flask Backend Server - Waste Classification System

## Overview

This directory contains the Flask backend server that receives predictions from ESP32-CAM devices, stores the data, and provides a real-time web dashboard for monitoring.

## Features

- ✅ **REST API** for receiving and querying predictions
- ✅ **WebSocket Server** (Socket.IO) for real-time updates
- ✅ **Data Logging** to CSV format
- ✅ **Statistics Engine** for analytics
- ✅ **CORS Enabled** for cross-origin requests
- ✅ **Static File Serving** for web dashboard

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

**Recommended:** Use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Running the Server

### Development Mode

```bash
python app.py
```

The server will start on `http://0.0.0.0:5000` with debug mode enabled.

### Production Mode

For production deployment, use a production WSGI server like Gunicorn:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn --worker-class eventlet -w 1 app:app -b 0.0.0.0:5000
```

**Note:** Socket.IO requires eventlet worker class and single worker (`-w 1`) for proper operation.

---

## Configuration

### Port Configuration

To change the port, edit `app.py`:

```python
socketio.run(app, host='0.0.0.0', port=8080, debug=True)
```

### CORS Configuration

To restrict CORS origins, edit `app.py`:

```python
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"])
```

### Data Directory

Predictions are logged to `data/predictions.csv`. The directory is created automatically if it doesn't exist.

To change the data directory location:

```python
DATA_DIR = '/path/to/your/data/directory'
```

---

## API Endpoints

### REST API

#### `GET /`
- **Description:** Serve web dashboard
- **Response:** HTML page

#### `POST /api/prediction`
- **Description:** Receive prediction from ESP32-CAM
- **Content-Type:** `application/json`
- **Body:**
  ```json
  {
    "category": "plastic",
    "confidence": 0.87,
    "device_id": "ESP32-CAM-001",
    "timestamp": 123456789
  }
  ```
- **Response:** `{"status": "success", "message": "Prediction received"}`

#### `GET /api/predictions`
- **Description:** Get recent predictions (last 50)
- **Response:**
  ```json
  {
    "status": "success",
    "predictions": [...]
  }
  ```

#### `GET /api/stats`
- **Description:** Get statistics
- **Response:**
  ```json
  {
    "status": "success",
    "stats": {
      "total_classifications": 42,
      "category_counts": {...},
      "average_confidence": 0.85,
      "most_common_category": "plastic"
    }
  }
  ```

### WebSocket Events

#### Server → Client

- **`connection_status`** - Sent on connection
- **`new_prediction`** - Broadcast when new prediction received

#### Client → Server

- **`connect`** - Connection established
- **`disconnect`** - Connection closed

---

## File Structure

```
server/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── static/                # Static files for web dashboard
│   ├── index.html         # Dashboard HTML
│   ├── css/
│   │   └── style.css      # Styles
│   └── js/
│       └── app.js         # JavaScript logic
└── data/                  # Data storage
    └── predictions.csv    # Logged predictions
```

---

## Data Format

### CSV Structure

`data/predictions.csv`:

```csv
timestamp,category,confidence,device_id
2024-01-09T12:00:00.123456,plastic,0.87,ESP32-CAM-001
2024-01-09T12:00:02.456789,paper,0.92,ESP32-CAM-001
```

**Fields:**
- `timestamp` - ISO 8601 format
- `category` - Waste category name
- `confidence` - Float (0.0 - 1.0)
- `device_id` - Device identifier

### In-Memory Storage

- Last **50 predictions** kept in memory
- Used for quick access via `/api/predictions`
- Cleared on server restart

---

## Testing

### Test with cURL

**Send prediction:**
```bash
curl -X POST http://localhost:5000/api/prediction \
  -H "Content-Type: application/json" \
  -d '{
    "category": "plastic",
    "confidence": 0.87,
    "device_id": "test-device",
    "timestamp": 1704816000000
  }'
```

**Get predictions:**
```bash
curl http://localhost:5000/api/predictions
```

**Get statistics:**
```bash
curl http://localhost:5000/api/stats
```

### Test with Python

```python
import requests

# Send prediction
response = requests.post('http://localhost:5000/api/prediction', json={
    'category': 'plastic',
    'confidence': 0.87,
    'device_id': 'test-device',
    'timestamp': 1704816000000
})
print(response.json())

# Get stats
stats = requests.get('http://localhost:5000/api/stats').json()
print(stats)
```

---

## Monitoring

### Server Logs

The server outputs logs to console:

```
📊 Received prediction: plastic (87.00%)
✅ Client connected
❌ Client disconnected
```

### Check Server Status

```bash
# Check if server is running
curl http://localhost:5000/api/stats

# Should return statistics JSON
```

---

## Troubleshooting

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 5000
# On Linux/Mac:
lsof -i :5000
# On Windows:
netstat -ano | findstr :5000

# Kill the process or use a different port
```

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
pip install -r requirements.txt
```

### CSV Permission Error

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
- Ensure `data/` directory has write permissions
- Run server with appropriate user permissions

### WebSocket Not Connecting

**Problem:** Dashboard shows "Disconnected"

**Solution:**
- Check Flask console for errors
- Verify firewall settings
- Check browser console for WebSocket errors
- Ensure eventlet is installed

---

## Deployment

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

Build and run:

```bash
docker build -t waste-classification-backend .
docker run -p 5000:5000 -v $(pwd)/data:/app/data waste-classification-backend
```

### Cloud Deployment

#### Heroku

```bash
# Install Heroku CLI
# Create Procfile:
echo "web: gunicorn --worker-class eventlet -w 1 app:app" > Procfile

# Deploy
heroku create waste-classification
git push heroku main
```

#### AWS EC2

1. Launch EC2 instance (Ubuntu)
2. Install Python and dependencies
3. Clone repository
4. Run with Gunicorn and Nginx
5. Configure security groups for port 5000

---

## Security Considerations

### Production Checklist

- [ ] Disable debug mode (`debug=False`)
- [ ] Configure proper CORS origins
- [ ] Add authentication for API endpoints
- [ ] Use HTTPS (SSL/TLS)
- [ ] Implement rate limiting
- [ ] Validate input data
- [ ] Set up logging
- [ ] Use environment variables for sensitive data
- [ ] Regular security updates

### Environment Variables

For production, use environment variables:

```python
import os

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
PORT = int(os.environ.get('PORT', 5000))
```

---

## Performance

### Current Capacity

- Handles multiple concurrent WebSocket connections
- Processes predictions in real-time
- Memory usage: ~50MB base + 50 predictions in memory

### Optimization Tips

- Use Redis for session storage (multi-instance)
- Implement database instead of CSV for large datasets
- Use Nginx for static file serving
- Enable gzip compression
- Implement caching for statistics

---

## Maintenance

### Clear Old Data

```bash
# Backup current data
cp data/predictions.csv data/predictions_backup_$(date +%Y%m%d).csv

# Clear CSV (keep headers)
head -1 data/predictions.csv > temp.csv
mv temp.csv data/predictions.csv
```

### Update Dependencies

```bash
pip list --outdated
pip install --upgrade -r requirements.txt
```

---

## Contributing

When contributing to the backend:

1. Follow PEP 8 style guide
2. Add docstrings to functions
3. Update this README if adding features
4. Test API endpoints before committing
5. Update `requirements.txt` if adding dependencies

---

## License

MIT License - See main repository LICENSE file

---

## Support

For backend-specific issues:
1. Check Flask console output
2. Review logs in terminal
3. Test endpoints with cURL
4. Check `data/predictions.csv` for data integrity
5. Open an issue on GitHub with logs

---

**Last Updated:** 2024-01-09
