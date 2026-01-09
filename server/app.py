from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import pandas as pd
import os
import json

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)
# Use threading to avoid eventlet/gevent issues on Windows
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Data storage
predictions_list = []
DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "predictions.csv")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize CSV if it doesn't exist
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=["timestamp", "category", "confidence", "device_id"])
    df.to_csv(CSV_FILE, index=False)


@app.route("/")
def index():
    """Serve the web dashboard"""
    return send_from_directory("static", "index.html")


@app.route("/api/prediction", methods=["POST"])
def receive_prediction():
    """Receive prediction from ESP32-CAM"""
    try:
        data = request.get_json()

        # Add timestamp
        data["timestamp"] = datetime.now().isoformat()

        # Store in memory
        predictions_list.append(data)

        # Keep only last 50 predictions in memory
        if len(predictions_list) > 50:
            predictions_list.pop(0)

        # Log to CSV with correct column order
        df = pd.DataFrame([data])
        df = df[["timestamp", "category", "confidence", "device_id"]]
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)

        # Broadcast to all connected clients via WebSocket
        socketio.emit("new_prediction", data)

        print(f"📊 Received prediction: {data['category']} ({data['confidence']:.2%})")

        return jsonify({"status": "success", "message": "Prediction received"}), 200

    except Exception as e:
        print(f"❌ Error receiving prediction: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    """Get recent predictions"""
    try:
        # Return last 50 predictions
        return jsonify({"status": "success", "predictions": predictions_list}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get statistics"""
    try:
        if len(predictions_list) == 0:
            return jsonify(
                {
                    "status": "success",
                    "stats": {
                        "total_classifications": 0,
                        "category_counts": {},
                        "average_confidence": 0,
                        "most_common_category": "none",
                    },
                }
            ), 200

        # Calculate statistics
        df = pd.DataFrame(predictions_list)

        category_counts = df["category"].value_counts().to_dict()
        avg_confidence = df["confidence"].mean()
        most_common = df["category"].mode()[0] if len(df) > 0 else "none"

        # Calculate average confidence per category
        avg_confidence_per_category = (
            df.groupby("category")["confidence"].mean().to_dict()
        )

        stats = {
            "total_classifications": len(predictions_list),
            "category_counts": category_counts,
            "average_confidence": float(avg_confidence),
            "most_common_category": most_common,
            "average_confidence_per_category": avg_confidence_per_category,
        }

        return jsonify({"status": "success", "stats": stats}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    print("✅ Client connected")
    emit("connection_status", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    print("❌ Client disconnected")


if __name__ == "__main__":
    print("\n🗑️ Waste Classification Backend Server")
    print("=" * 50)
    print("Server starting on http://localhost:5000")
    print("Dashboard: http://localhost:5000")
    print("API: http://localhost:5000/api/*")
    print("=" * 50 + "\n")

    # Run without the Flask debug reloader and allow Werkzeug explicitly
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
