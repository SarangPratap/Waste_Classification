import arcade
import cv2
import numpy as np
from PIL import Image
import threading
import queue
import json
import time
import datetime
import csv
import os
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from dataclasses import dataclass, field
from typing import Dict, Optional
from collections import deque, defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('dashboard.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

CONFIG = {
    "esp32_ip": "10.111.150.217",
    "http_port": 5000,
    "confidence_threshold": 0.6,
    "enable_scanlines": True,
    "stream_port": 81
}

if os.path.exists('config.json'):
    with open('config.json', 'r') as f:
        CONFIG.update(json.load(f))

CATEGORIES = {
    "battery": {"icon": "🔋", "color": (255, 215, 0, 255), "name": "Battery"},
    "biological": {"icon": "🍎", "color": (50, 205, 50, 255), "name": "Biological"},
    "cardboard": {"icon": "📦", "color": (139, 69, 19, 255), "name": "Cardboard"},
    "clothes": {"icon": "👕", "color": (147, 112, 219, 255), "name": "Clothes"},
    "glass": {"icon": "🫙", "color": (0, 206, 209, 255), "name": "Glass"},
    "metal": {"icon": "🔩", "color": (128, 128, 128, 255), "name": "Metal"},
    "paper": {"icon": "📄", "color": (135, 206, 235, 255), "name": "Paper"},
    "plastic": {"icon": "🍾", "color": (30, 144, 255, 255), "name": "Plastic"},
    "shoe": {"icon": "👟", "color": (255, 140, 0, 255), "name": "Shoe"},
}

prediction_queue: queue.Queue = queue.Queue(maxsize=50)
frame_queue: queue.Queue = queue.Queue(maxsize=2)
stop_event = threading.Event()

@dataclass
class Prediction:
    category: str
    confidence: float
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

def with_alpha(color, alpha):
    r, g, b, _ = color
    return (r, g, b, alpha)

class TextManager:
    def __init__(self):
        self.texts = {}
        self.defaults = {
            "font_name": "Arial",
            "anchor_x": "center",
            "bold": False
        }
    
    def get(self, key, text, x, y, color, size, **kwargs):
        if key not in self.texts:
            self.texts[key] = arcade.Text(text, x, y, color, size, **{**self.defaults, **kwargs})
        else:
            self.texts[key].text = text
            self.texts[key].x = x
            self.texts[key].y = y
            self.texts[key].color = color
            self.texts[key].font_size = size
        return self.texts[key]
    
    def draw(self, key):
        if key in self.texts:
            self.texts[key].draw()

class PredictionHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/prediction':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                if data.get('confidence', 0) >= CONFIG['confidence_threshold']:
                    try:
                        prediction_queue.put_nowait(Prediction(
                            category=data.get('category', 'unknown').lower(),
                            confidence=float(data.get('confidence', 0))
                        ))
                    except queue.Full:
                        pass
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
                
            except Exception as e:
                logger.error(f"Error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass

def start_http():
    server = HTTPServer(('0.0.0.0', CONFIG['http_port']), PredictionHandler)
    logger.info(f"HTTP Server on port {CONFIG['http_port']}")
    server.serve_forever()

class VideoCaptureThread(threading.Thread):
    """MJPEG stream capture for ESP32-CAM - True live video!"""
    def __init__(self):
        super().__init__(daemon=True)
        self.stop_requested = False
        self.connected = False
        self.last_error = None
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()
        
    def run(self):
        # Try MJPEG stream first (smoother), fallback to snapshot polling
        stream_url = f"http://{CONFIG['esp32_ip']}:{CONFIG['stream_port']}/stream"
        snapshot_url = f"http://{CONFIG['esp32_ip']}:{CONFIG['stream_port']}/snapshot"
        
        logger.info(f"Video: Attempting MJPEG stream {stream_url}")
        
        while not self.stop_requested:
            # Try MJPEG stream using OpenCV
            try:
                self.cap = cv2.VideoCapture(stream_url)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for low latency
                
                if self.cap.isOpened():
                    logger.info("✓ Connected to MJPEG stream (live video)")
                    self.connected = True
                    self._stream_loop()
                else:
                    raise Exception("MJPEG stream failed to open")
                    
            except Exception as e:
                logger.warning(f"MJPEG failed: {e}, falling back to snapshot polling")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                
                # Fallback to snapshot polling
                self._snapshot_loop(snapshot_url)
            
            if not self.stop_requested:
                time.sleep(2)  # Wait before retry
    
    def _stream_loop(self):
        """Read frames from MJPEG stream"""
        consecutive_fails = 0
        
        while not self.stop_requested and consecutive_fails < 10:
            try:
                ret, frame = self.cap.read()
                
                if ret and frame is not None:
                    consecutive_fails = 0
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Update FPS counter
                    self.frame_count += 1
                    elapsed = time.time() - self.fps_start_time
                    if elapsed >= 1.0:
                        self.fps = self.frame_count / elapsed
                        self.frame_count = 0
                        self.fps_start_time = time.time()
                    
                    # Put frame in queue (non-blocking)
                    try:
                        # Clear old frames to keep latest
                        while not frame_queue.empty():
                            try:
                                frame_queue.get_nowait()
                            except queue.Empty:
                                break
                        frame_queue.put_nowait(frame)
                    except queue.Full:
                        pass
                else:
                    consecutive_fails += 1
                    time.sleep(0.05)
                    
            except Exception as e:
                logger.error(f"Stream read error: {e}")
                consecutive_fails += 1
                time.sleep(0.1)
        
        self.connected = False
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def _snapshot_loop(self, snapshot_url):
        """Fallback: Poll snapshot endpoint"""
        import urllib.request
        logger.info(f"Video: Using snapshot polling {snapshot_url}")
        
        while not self.stop_requested:
            try:
                start_time = time.time()
                url = f"{snapshot_url}?t={int(start_time * 1000)}"
                req = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
                
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        img_data = resp.read()
                        nparr = np.frombuffer(img_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            try:
                                while not frame_queue.empty():
                                    frame_queue.get_nowait()
                                frame_queue.put_nowait(frame)
                                self.connected = True
                            except queue.Full:
                                pass
                
                # ~15 FPS for smoother video
                elapsed = time.time() - start_time
                time.sleep(max(0, 0.066 - elapsed))
                
            except Exception as e:
                if self.connected:
                    logger.error(f"Snapshot error: {e}")
                self.connected = False
                self.last_error = str(e)
                time.sleep(1)
                return  # Exit to try MJPEG again
    
    def stop(self):
        self.stop_requested = True
        if self.cap:
            self.cap.release()
class Dashboard(arcade.Window):
    def __init__(self):
        super().__init__(1400, 900, "Waste Classification", resizable=True)
        self.set_location(50, 50)
        
        self.camera = arcade.Camera2D()
        self.text_manager = TextManager()
        
        self.predictions = deque(maxlen=20)
        self.current: Optional[Prediction] = None
        self.counts = defaultdict(int)
        self.total = 0
        
        self.video_sprite: Optional[arcade.Sprite] = None
        self.connection_status = "Connecting..."
        self.connection_color = (255, 165, 0, 255)
        self.last_frame = 0
        
        self.bar_width = 0
        self.pulse = 0
        
        self._init_static_texts()
        
        self.csv_file = open('predictions_log.csv', 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        if self.csv_file.tell() == 0:
            self.csv_writer.writerow(['timestamp', 'category', 'confidence'])
        
        threading.Thread(target=start_http, daemon=True).start()
        self.video_thread = VideoCaptureThread()
        self.video_thread.start()
        
        logger.info("Dashboard ready")
    
    def _init_static_texts(self):
        self.category_texts = {}
        for i, (key, data) in enumerate(CATEGORIES.items()):
            self.category_texts[key] = {
                'icon': arcade.Text(data['icon'], 0, 0, (255, 255, 255, 255), 20, 
                                  anchor_x="center", font_name="Segoe UI Emoji"),
                'label': arcade.Text(key[:6], 0, 0, (150, 150, 150, 255), 9, 
                                   anchor_x="center", font_name="Arial")
            }
    
    def update_video(self):
        try:
            while not frame_queue.empty():
                frame = frame_queue.get_nowait()
                if frame is not None:
                    h, w = frame.shape[:2]
                    target_w, target_h = 640, 480
                    scale = min(target_w/w, target_h/h)
                    new_w, new_h = int(w*scale), int(h*scale)
                    frame = cv2.resize(frame, (new_w, new_h))
                    
                    # Convert to RGBA (required by Arcade 3.0)
                    img = Image.fromarray(frame).convert('RGBA')
                    texture = arcade.Texture(img)
                    
                    if self.video_sprite:
                        self.video_sprite.texture = texture
                        self.video_sprite.width = new_w
                        self.video_sprite.height = new_h
                    else:
                        self.video_sprite = arcade.Sprite(texture)
                        self.video_sprite.center_x = 350
                        self.video_sprite.center_y = 480
                    
                    # Show FPS if available
                    fps_info = f" ({self.video_thread.fps:.1f} FPS)" if self.video_thread.fps > 0 else ""
                    self.connection_status = f"🎥 LIVE{fps_info}"
                    self.connection_color = (0, 255, 127, 255)
                    self.last_frame = time.time()
        except queue.Empty:
            pass
        
        if time.time() - self.last_frame > 5 and self.last_frame > 0:
            self.connection_status = "Reconnecting..."
            self.connection_color = (255, 165, 0, 255)
            if self.video_thread.last_error:
                self.connection_status = f"Error: {self.video_thread.last_error[:20]}"
    
    def update_predictions(self):
        try:
            while not prediction_queue.empty():
                pred = prediction_queue.get_nowait()
                self.current = pred
                self.predictions.appendleft(pred)
                
                if pred.category in CATEGORIES:
                    self.counts[pred.category] += 1
                    self.total += 1
                    self.pulse = 1.0
                    
                    self.csv_writer.writerow([
                        pred.timestamp.isoformat(),
                        pred.category,
                        pred.confidence
                    ])
                    self.csv_file.flush()
        except queue.Empty:
            pass
        
        if self.current:
            target = self.current.confidence * 280
            self.bar_width += (target - self.bar_width) * 0.1
        
        self.pulse = max(0, self.pulse - 0.02)
    
    def on_update(self, delta_time):
        self.update_video()
        self.update_predictions()
    
    def draw_panel(self, center_x, center_y, width, height, color=(40, 40, 50, 200)):
        rect = arcade.rect.XYWH(center_x, center_y, width, height)
        arcade.draw_rect_filled(rect, color)
        arcade.draw_rect_outline(rect, (255, 255, 255, 50), 1)
    
    def on_draw(self):
        self.clear((15, 15, 20, 255))
        
        with self.camera.activate():
            margin = 20
            header_y = self.height - 40
            bottom_panel_height = 160
            
            video_w, video_h = 640, 480
            video_x = margin + video_w//2
            video_y = (self.height + bottom_panel_height)//2 - 20
            
            right_x = self.width - margin - 200
            panel_w = 380
            
            pred_y = self.height - 180
            pred_h = 220
            stats_y = pred_y - pred_h//2 - 140
            stats_h = 260  # <-- FIXED: Added missing variable
            history_y = bottom_panel_height//2 + margin
            
            # Grid
            for i in range(0, self.width, 60):
                arcade.draw_line(i, 0, i, self.height, (255, 255, 255, 8), 1)
            for i in range(0, self.height, 60):
                arcade.draw_line(0, i, self.width, i, (255, 255, 255, 8), 1)
            
            # Header
            header_text = self.text_manager.get('header', "WASTE CLASSIFICATION SYSTEM", 
                                               self.width//2, header_y, 
                                               (255, 255, 255, 255), 24, bold=True)
            header_text.draw()
            
            status_text = self.text_manager.get('status', 
                                               f"Total: {self.total} | {self.connection_status}", 
                                               self.width//2, header_y - 30, 
                                               self.connection_color, 14)
            status_text.draw()
            
            # Video Panel
            self.draw_panel(video_x, video_y, video_w + 20, video_h + 20, (20, 20, 30, 200))
            if self.video_sprite:
                self.video_sprite.center_x = video_x
                self.video_sprite.center_y = video_y
                arcade.draw_sprite(self.video_sprite)
                
                if CONFIG['enable_scanlines']:
                    for y in range(int(video_y - video_h//2), int(video_y + video_h//2), 4):
                        arcade.draw_line(video_x - video_w//2, y, video_x + video_w//2, y, 
                                       (0, 0, 0, 40), 1)
                
                arcade.draw_circle_filled(video_x - video_w//2 + 30, video_y + video_h//2 - 30, 
                                        8, (255, 0, 0, 200))
                live_text = self.text_manager.get('live', "LIVE", 
                                                  video_x - video_w//2 + 50, 
                                                  video_y + video_h//2 - 35, 
                                                  (255, 0, 0, 255), 12, anchor_x="left")
                live_text.draw()
            else:
                waiting_text = self.text_manager.get('waiting', "Waiting for ESP32-CAM stream...", 
                                                    video_x, video_y, 
                                                    (100, 100, 100, 255), 16)
                waiting_text.draw()
                
                hint_text = self.text_manager.get('hint', 
                                                 f"Check IP: {CONFIG['esp32_ip']}:{CONFIG['stream_port']}", 
                                                 video_x, video_y - 30, 
                                                 (80, 80, 80, 255), 12)
                hint_text.draw()
            
            # Current Prediction
            if self.current and self.current.category in CATEGORIES:
                cat = CATEGORIES[self.current.category]
                col = cat['color']
                
                scale = 1.0 + (self.pulse * 0.05)
                box_w = panel_w * scale
                box_h = pred_h * scale
                
                bg_col = (col[0]//4, col[1]//4, col[2]//4, 180)
                self.draw_panel(right_x, pred_y, box_w, box_h, bg_col)
                arcade.draw_rect_outline(arcade.rect.XYWH(right_x, pred_y, box_w+4, box_h+4), 
                                        with_alpha(col, 100), 2)
                
                icon_text = self.text_manager.get('pred_icon', cat['icon'], 
                                                 right_x, pred_y + 40, 
                                                 (255, 255, 255, 255), 40)
                icon_text.draw()
                
                name_text = self.text_manager.get('pred_name', cat['name'].upper(), 
                                                 right_x, pred_y - 10, col, 22, bold=True)
                name_text.draw()
                
                bar_y = pred_y - 60
                arcade.draw_rect_filled(arcade.rect.XYWH(right_x, bar_y, 280, 18), 
                                      (60, 60, 70, 255))
                if self.bar_width > 0:
                    arcade.draw_rect_filled(arcade.rect.XYWH(right_x - 140 + self.bar_width/2, 
                                                             bar_y, self.bar_width, 18), col)
                
                conf_text = self.text_manager.get('conf', f"{self.current.confidence:.1%}", 
                                                 right_x, bar_y, 
                                                 (255, 255, 255, 255), 12)
                conf_text.draw()
            else:
                self.draw_panel(right_x, pred_y, panel_w, pred_h, (30, 30, 40, 200))
                no_det_text = self.text_manager.get('no_det', "NO DETECTION", 
                                                   right_x, pred_y, 
                                                   (100, 100, 100, 255), 20)
                no_det_text.draw()
            
            # Statistics
            stats_title = self.text_manager.get('stats_title', "CATEGORY STATISTICS", 
                                               right_x, stats_y + stats_h//2 - 20,  # <-- Now works!
                                               (255, 255, 255, 255), 16, bold=True)
            stats_title.draw()
            
            grid_start_y = stats_y + 60
            cell_w, cell_h = 110, 70
            spacing = 10
            
            for i, (key, data) in enumerate(CATEGORIES.items()):
                row = i // 3
                col = i % 3
                x = right_x - panel_w//2 + 60 + col * (cell_w + spacing)
                y = grid_start_y - row * (cell_h + spacing)
                
                count = self.counts[key]
                is_active = self.current and self.current.category == key
                
                box_color = with_alpha(data['color'], 100 if is_active else 50)
                cell_rect = arcade.rect.XYWH(x, y, cell_w, cell_h)
                arcade.draw_rect_filled(cell_rect, box_color)
                
                if is_active:
                    arcade.draw_rect_outline(cell_rect, data['color'], 2)
                else:
                    arcade.draw_rect_outline(cell_rect, (255, 255, 255, 30), 1)
                
                icon_obj = self.category_texts[key]['icon']
                icon_obj.x = x
                icon_obj.y = y + 10
                icon_obj.draw()
                
                count_text = self.text_manager.get(f'count_{key}', str(count), 
                                                   x, y - 12, data['color'], 14, bold=True)
                count_text.draw()
                
                label_obj = self.category_texts[key]['label']
                label_obj.x = x
                label_obj.y = y - cell_h//2 - 10
                label_obj.draw()
            
            # History
            self.draw_panel(self.width//2, history_y, self.width - margin*2, bottom_panel_height, 
                          (25, 25, 35, 200))
            hist_title = self.text_manager.get('hist_title', "RECENT DETECTIONS", 
                                              margin + 10, history_y + 50, 
                                              (255, 255, 255, 255), 14, bold=True, anchor_x="left")
            hist_title.draw()
            
            start_x = margin + 80
            for i, pred in enumerate(list(self.predictions)[:10]):
                x = start_x + i * 130
                y = history_y
                
                if pred.category in CATEGORIES:
                    data = CATEGORIES[pred.category]
                    col = data['color']
                    
                    item_rect = arcade.rect.XYWH(x, y, 120, 120)
                    arcade.draw_rect_filled(item_rect, with_alpha(col, 40))
                    
                    r_icon = self.text_manager.get(f'rec_{i}_icon', data['icon'], x, y + 25, col, 28)
                    r_icon.draw()
                    
                    r_name = self.text_manager.get(f'rec_{i}_name', data['name'][:8], 
                                                   x, y - 5, (255, 255, 255, 255), 11)
                    r_name.draw()
                    
                    r_conf = self.text_manager.get(f'rec_{i}_conf', f"{pred.confidence:.0%}", 
                                                   x, y - 25, (200, 200, 200, 255), 10)
                    r_conf.draw()
                    
                    r_time = self.text_manager.get(f'rec_{i}_time', 
                                                   pred.timestamp.strftime("%H:%M"), 
                                                   x, y - 42, (120, 120, 120, 255), 9)
                    r_time.draw()

    def on_close(self):
        stop_event.set()
        self.video_thread.stop()
        self.csv_file.close()
        super().on_close()

if __name__ == "__main__":
    if CONFIG['esp32_ip'] == "192.168.1.100":
        print("⚠️  WARNING: Using default IP 192.168.1.100")
        print("    Update config.json with your ESP32-CAM IP")
        print("    Stream URL:", f"http://{CONFIG['esp32_ip']}:{CONFIG['stream_port']}/stream")
    
    app = Dashboard()
    arcade.run()