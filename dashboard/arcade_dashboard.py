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
from typing import Dict, Optional, List, Tuple
from collections import deque, defaultdict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log', encoding='utf-8'),
        logging.StreamHandler(open(1, 'w', encoding='utf-8', closefd=False))
    ]
)
logger = logging.getLogger(__name__)

CONFIG = {
    "esp32_ip": "10.111.150.217",
    "http_port": 5000,
    "confidence_threshold": 0.6,
    "enable_scanlines": True,
    "stream_port": 80  # Default to port 80 (ESP32 server port)
}

# Look for config.json in script directory or parent directory
script_dir = os.path.dirname(os.path.abspath(__file__))
config_paths = [
    os.path.join(script_dir, 'config.json'),
    os.path.join(script_dir, '..', 'config.json'),
    'config.json'
]

for config_path in config_paths:
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            CONFIG.update(json.load(f))
        logger.info(f"Loaded config from: {config_path}")
        break

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

# Date range presets for analytics dropdown
DATE_PRESETS = [
    ("Today", 0),
    ("Last 7 Days", 7),
    ("Last 14 Days", 14),
    ("Last 30 Days", 30),
    ("Last 90 Days", 90),
    ("All Time", -1),
]

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

class AnalyticsEngine:
    """Handles data analysis, filtering, and chart generation"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file = csv_file_path
        self.predictions: List[Prediction] = []
        self.load_data()
    
    def load_data(self):
        """Load all predictions from CSV file"""
        self.predictions = []
        try:
            if os.path.exists(self.csv_file):
                with open(self.csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            timestamp = datetime.datetime.fromisoformat(row['timestamp'])
                            pred = Prediction(
                                category=row['category'].lower(),
                                confidence=float(row['confidence']),
                                timestamp=timestamp
                            )
                            self.predictions.append(pred)
                        except (ValueError, KeyError):
                            continue
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
    
    def filter_by_date(self, start_date: datetime.datetime, end_date: datetime.datetime) -> List[Prediction]:
        """Filter predictions by date range"""
        return [p for p in self.predictions 
                if start_date <= p.timestamp <= end_date]
    
    def get_category_stats(self, predictions: List[Prediction]) -> Dict[str, Tuple[int, float]]:
        """Get count and average confidence per category"""
        stats = defaultdict(lambda: {'count': 0, 'confidences': []})
        
        for pred in predictions:
            stats[pred.category]['count'] += 1
            stats[pred.category]['confidences'].append(pred.confidence)
        
        result = {}
        for cat, data in stats.items():
            avg_conf = np.mean(data['confidences']) if data['confidences'] else 0
            result[cat] = (data['count'], avg_conf)
        
        return result
    
    def generate_histogram(self, predictions: List[Prediction], width: int = 600, height: int = 400) -> Image.Image:
        """Generate histogram of predictions by category"""
        plt.ioff()  # Disable interactive mode
        
        stats = self.get_category_stats(predictions)
        categories = list(CATEGORIES.keys())
        counts = [stats.get(cat, (0, 0))[0] for cat in categories]
        
        # Create figure with dark background
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        fig.patch.set_facecolor('#0f0f14')
        ax.set_facecolor('#1a1a24')
        
        # Get colors and normalize to 0-1 range
        colors = []
        for cat in categories:
            r, g, b, a = CATEGORIES[cat]['color']
            colors.append((r/255.0, g/255.0, b/255.0))
        
        # Create bar chart
        bars = ax.bar(range(len(categories)), counts, color=colors, edgecolor='white', linewidth=1.5)
        
        ax.set_xlabel('Waste Category', fontsize=12, color='white')
        ax.set_ylabel('Count', fontsize=12, color='white')
        ax.set_title('Waste Classification Distribution', fontsize=14, color='white', fontweight='bold', pad=20)
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=45, ha='right', color='white', fontsize=9)
        ax.tick_params(colors='white', labelsize=10)
        
        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('white')
        ax.spines['bottom'].set_color('white')
        ax.grid(axis='y', alpha=0.3, color='white', linestyle='--')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom', color='white', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to PIL Image
        buf = BytesIO()
        fig.savefig(buf, format='png', facecolor='#0f0f14', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf).convert('RGBA')
        plt.close(fig)
        
        return img
    
    def generate_confidence_table(self, predictions: List[Prediction], width: int = 500, height: int = 300) -> Image.Image:
        """Generate confidence statistics table"""
        plt.ioff()  # Disable interactive mode
        
        stats = self.get_category_stats(predictions)
        
        # Sort by count descending
        sorted_stats = sorted([(cat, data) for cat, data in stats.items()], 
                            key=lambda x: x[1][0], reverse=True)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        fig.patch.set_facecolor('#0f0f14')
        ax.axis('tight')
        ax.axis('off')
        
        # Prepare table data
        table_data = [['Category', 'Count', 'Avg Confidence', 'Min', 'Max']]
        
        for cat, (count, avg_conf) in sorted_stats:
            confidences = [p.confidence for p in predictions if p.category == cat]
            min_conf = min(confidences) if confidences else 0
            max_conf = max(confidences) if confidences else 0
            
            table_data.append([
                cat.capitalize(),
                str(count),
                f'{avg_conf:.1%}',
                f'{min_conf:.1%}',
                f'{max_conf:.1%}'
            ])
        
        # Create table
        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.2, 0.15, 0.2, 0.15, 0.15])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.5)
        
        # Style header
        for i in range(5):
            cell = table[(0, i)]
            cell.set_facecolor('#ff6b35')
            cell.set_text_props(weight='bold', color='white')
        
        # Style rows with alternating colors
        for i in range(1, len(table_data)):
            for j in range(5):
                cell = table[(i, j)]
                if i % 2 == 0:
                    cell.set_facecolor('#2a2a35')
                else:
                    cell.set_facecolor('#1f1f28')
                cell.set_text_props(color='white')
                cell.set_edgecolor('#555555')
        
        plt.title('Confidence Statistics', fontsize=14, color='white', fontweight='bold', pad=20)
        
        # Convert to PIL Image
        buf = BytesIO()
        fig.savefig(buf, format='png', facecolor='#0f0f14', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf).convert('RGBA')
        plt.close(fig)
        
        return img

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
                    logger.info("Connected to MJPEG stream (live video)")
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
        
        # Analytics
        self.analytics = AnalyticsEngine(os.path.join(os.path.dirname(__file__), 'predictions_log.csv'))
        self.show_analytics = False
        self.histogram_sprite: Optional[arcade.Sprite] = None
        self.stats_sprite: Optional[arcade.Sprite] = None
        
        # Date range presets
        self.date_preset_index = 3  # Default: "Last 30 Days"
        self._apply_date_preset()
        
        # Dropdown state
        self.dropdown_open = False
        self.dropdown_buttons: List[Tuple[float, float, float, float]] = []  # x, y, w, h per item
        
        self._init_static_texts()
        
        csv_file_path = os.path.join(os.path.dirname(__file__), 'predictions_log.csv')
        self.csv_file = open(csv_file_path, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        if self.csv_file.tell() == 0:
            self.csv_writer.writerow(['timestamp', 'category', 'confidence'])
        
        threading.Thread(target=start_http, daemon=True).start()
        self.video_thread = VideoCaptureThread()
        self.video_thread.start()
        
        logger.info("Dashboard ready")
        self.update_analytics_charts()
    
    def _apply_date_preset(self):
        """Set start_date / end_date from the current preset index"""
        label, days = DATE_PRESETS[self.date_preset_index]
        self.end_date = datetime.datetime.now()
        if days == -1:  # All Time
            self.start_date = datetime.datetime(2000, 1, 1)
        elif days == 0:  # Today
            self.start_date = self.end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            self.start_date = self.end_date - datetime.timedelta(days=days)

    def update_analytics_charts(self):
        """Regenerate histogram and statistics charts side-by-side"""
        try:
            filtered = self.analytics.filter_by_date(self.start_date, self.end_date)
            logger.info(f"Analytics: {len(filtered)} predictions in range {self.start_date.date()} to {self.end_date.date()}")
            
            if filtered:
                # Scale charts to roughly half the window each
                chart_w = max(400, min(650, self.width // 2 - 40))
                chart_h = max(280, min(480, self.height - 200))
                
                hist_img = self.analytics.generate_histogram(filtered, chart_w, chart_h)
                hist_texture = arcade.Texture(hist_img)
                self.histogram_sprite = arcade.Sprite(hist_texture)
                
                stats_img = self.analytics.generate_confidence_table(filtered, chart_w, chart_h)
                stats_texture = arcade.Texture(stats_img)
                self.stats_sprite = arcade.Sprite(stats_texture)
                
                logger.info(f"Analytics charts generated ({len(filtered)} predictions)")
            else:
                self.histogram_sprite = None
                self.stats_sprite = None
                logger.info("Analytics: no data in selected range")
        except Exception as e:
            logger.error(f"Error updating analytics: {e}", exc_info=True)
    
    def on_key_press(self, key, modifiers):
        """Handle keyboard input"""
        if key == arcade.key.A:
            self.show_analytics = not self.show_analytics
            self.dropdown_open = False
            if self.show_analytics:
                self.analytics.load_data()
                self.update_analytics_charts()
                logger.info("Analytics view ON")
            else:
                logger.info("Analytics view OFF")
        
        elif key == arcade.key.R and self.show_analytics:
            self.analytics.load_data()
            self.update_analytics_charts()
            logger.info("Data reloaded")
        
        elif key == arcade.key.ESCAPE:
            if self.dropdown_open:
                self.dropdown_open = False
            elif self.show_analytics:
                self.show_analytics = False
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks — date preset dropdown"""
        if not self.show_analytics or button != arcade.MOUSE_BUTTON_LEFT:
            return
        
        # Check if click is on the dropdown toggle button
        btn_x, btn_y = self.width // 2, self.height - 90
        btn_w, btn_h = 260, 30
        if (btn_x - btn_w // 2 <= x <= btn_x + btn_w // 2 and
                btn_y - btn_h // 2 <= y <= btn_y + btn_h // 2):
            self.dropdown_open = not self.dropdown_open
            return
        
        # Check if click is on a dropdown item
        if self.dropdown_open:
            for idx, (bx, by, bw, bh) in enumerate(self.dropdown_buttons):
                if (bx - bw / 2 <= x <= bx + bw / 2 and
                        by - bh / 2 <= y <= by + bh / 2):
                    self.date_preset_index = idx
                    self._apply_date_preset()
                    self.update_analytics_charts()
                    self.dropdown_open = False
                    logger.info(f"Date preset: {DATE_PRESETS[idx][0]}")
                    return
            # Click outside dropdown closes it
            self.dropdown_open = False
    
    def _init_static_texts(self):
        self.category_texts = {}
        for i, (key, data) in enumerate(CATEGORIES.items()):
            self.category_texts[key] = {
                'icon': arcade.Text(data['icon'], 0, 0, (255, 255, 255, 255), 20, 
                                  anchor_x="center", font_name="Segoe UI Emoji"),
                'label': arcade.Text(key[:6], 0, 0, (150, 150, 150, 255), 9, 
                                   anchor_x="center", font_name="Arial")
            }
    
    def draw_analytics_view(self):
        """Draw combined analytics page — histogram + confidence table side-by-side"""
        filtered = self.analytics.filter_by_date(self.start_date, self.end_date)
        data_count = len(filtered)
        W, H = self.width, self.height
        preset_label = DATE_PRESETS[self.date_preset_index][0]

        # ── Header ──
        a_header = self.text_manager.get('a_header', "ANALYTICS & STATISTICS",
                                        W // 2, H - 40,
                                        (255, 255, 255, 255), 26, bold=True)
        a_header.draw()

        # ── Date preset dropdown button ──
        btn_x, btn_y = W // 2, H - 90
        btn_w, btn_h = 260, 30
        btn_color = (50, 60, 80, 255) if not self.dropdown_open else (70, 80, 110, 255)
        self.draw_panel(btn_x, btn_y, btn_w, btn_h, btn_color)
        arcade.draw_rect_outline(arcade.rect.XYWH(btn_x, btn_y, btn_w, btn_h),
                                (100, 200, 255, 200), 1)

        dropdown_label = f"{preset_label}  ({data_count} predictions)  v"
        a_date = self.text_manager.get('a_date', dropdown_label,
                                       btn_x, btn_y - 5,
                                       (100, 200, 255, 255), 13)
        a_date.draw()

        # ── Controls hint ──
        ctrl_text = "R: Reload  |  A / ESC: Close"
        a_ctrl = self.text_manager.get('a_ctrl', ctrl_text,
                                       W // 2, H - 120,
                                       (100, 140, 180, 255), 11)
        a_ctrl.draw()

        # ── Charts area (below header, above bottom margin) ──
        chart_top = H - 140
        chart_bottom = 30
        chart_area_h = chart_top - chart_bottom
        half_w = W // 2

        if self.histogram_sprite and self.stats_sprite:
            # Left: Histogram
            self.histogram_sprite.center_x = half_w // 2 + 10
            self.histogram_sprite.center_y = chart_bottom + chart_area_h // 2
            # Scale to fit
            max_w = half_w - 30
            max_h = chart_area_h - 20
            h_scale = min(max_w / self.histogram_sprite.texture.width,
                          max_h / self.histogram_sprite.texture.height, 1.0)
            self.histogram_sprite.width = self.histogram_sprite.texture.width * h_scale
            self.histogram_sprite.height = self.histogram_sprite.texture.height * h_scale
            arcade.draw_sprite(self.histogram_sprite)

            # Right: Confidence table
            self.stats_sprite.center_x = half_w + half_w // 2 - 10
            self.stats_sprite.center_y = chart_bottom + chart_area_h // 2
            s_scale = min(max_w / self.stats_sprite.texture.width,
                          max_h / self.stats_sprite.texture.height, 1.0)
            self.stats_sprite.width = self.stats_sprite.texture.width * s_scale
            self.stats_sprite.height = self.stats_sprite.texture.height * s_scale
            arcade.draw_sprite(self.stats_sprite)

            # Divider line
            arcade.draw_line(half_w, chart_bottom + 10, half_w, chart_top - 10,
                            (255, 255, 255, 30), 1)
        else:
            a_nodata = self.text_manager.get('a_nodata',
                                            "No data available for selected date range",
                                            W // 2, H // 2,
                                            (150, 150, 150, 255), 20)
            a_nodata.draw()
            a_hint = self.text_manager.get('a_hint',
                                          "Select a wider date range or press R to reload",
                                          W // 2, H // 2 - 35,
                                          (100, 100, 100, 255), 12)
            a_hint.draw()

        # ── Dropdown options (drawn last → on top) ──
        if self.dropdown_open:
            self.dropdown_buttons = []
            item_h = 32
            dd_w = btn_w
            for i, (label, _days) in enumerate(DATE_PRESETS):
                iy = btn_y - btn_h // 2 - item_h // 2 - i * item_h
                is_selected = (i == self.date_preset_index)
                bg = (60, 80, 120, 240) if is_selected else (35, 40, 55, 240)
                self.draw_panel(btn_x, iy, dd_w, item_h - 2, bg)
                txt_col = (255, 255, 255, 255) if is_selected else (180, 200, 230, 255)
                dd_text = self.text_manager.get(f'dd_{i}', label,
                                               btn_x, iy - 5, txt_col, 12,
                                               bold=is_selected)
                dd_text.draw()
                self.dropdown_buttons.append((btn_x, iy, dd_w, item_h))
    
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
                    
                    # Update analytics with new data
                    if self.show_analytics:
                        self.analytics.load_data()
                        self.update_analytics_charts()
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
    
    def on_resize(self, width, height):
        """Update camera when window is resized / fullscreened"""
        super().on_resize(width, height)
        self.camera = arcade.Camera2D()
    
    def on_draw(self):
        self.clear((15, 15, 20, 255))
        
        with self.camera.activate():
            # Show analytics view if enabled
            if self.show_analytics:
                self.draw_analytics_view()
                return

            W = self.width
            H = self.height
            margin = 20

            # ── Layout zones (responsive) ──
            header_h = 70
            bottom_h = 160
            content_h = H - header_h - bottom_h

            # Right panel takes ~30% of width, min 360, max 420
            right_panel_w = max(360, min(420, int(W * 0.30)))
            # Video area fills the rest
            video_area_w = W - right_panel_w - margin * 3

            video_w = min(video_area_w, int(content_h * 4 / 3))  # keep 4:3
            video_h = int(video_w * 3 / 4)
            # Clamp video height to available content area
            if video_h > content_h - 20:
                video_h = content_h - 20
                video_w = int(video_h * 4 / 3)

            video_x = margin + video_w // 2
            video_y = H - header_h - content_h // 2

            right_x = W - margin - right_panel_w // 2
            history_y = bottom_h // 2 + margin

            # ── Grid background ──
            for gx in range(0, W, 60):
                arcade.draw_line(gx, 0, gx, H, (255, 255, 255, 8), 1)
            for gy in range(0, H, 60):
                arcade.draw_line(0, gy, W, gy, (255, 255, 255, 8), 1)

            # ── Header ──
            header_text = self.text_manager.get('header', "WASTE CLASSIFICATION SYSTEM",
                                               W // 2, H - 30,
                                               (255, 255, 255, 255), 24, bold=True)
            header_text.draw()

            status_str = f"Total: {self.total} | {self.connection_status} | Press A for Analytics"
            status_text = self.text_manager.get('status', status_str,
                                               W // 2, H - 58,
                                               self.connection_color, 12)
            status_text.draw()

            # ── Video Panel ──
            self.draw_panel(video_x, video_y, video_w + 20, video_h + 20, (20, 20, 30, 200))
            if self.video_sprite:
                self.video_sprite.center_x = video_x
                self.video_sprite.center_y = video_y
                self.video_sprite.width = video_w
                self.video_sprite.height = video_h
                arcade.draw_sprite(self.video_sprite)

                if CONFIG['enable_scanlines']:
                    for sy in range(int(video_y - video_h // 2), int(video_y + video_h // 2), 4):
                        arcade.draw_line(video_x - video_w // 2, sy,
                                        video_x + video_w // 2, sy, (0, 0, 0, 40), 1)

                arcade.draw_circle_filled(video_x - video_w // 2 + 30,
                                         video_y + video_h // 2 - 30, 8, (255, 0, 0, 200))
                live_text = self.text_manager.get('live', "LIVE",
                                                  video_x - video_w // 2 + 50,
                                                  video_y + video_h // 2 - 35,
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

            # ── Right Panel: Current Prediction + Legend ──
            rpx = right_x  # center of right panel
            rp_left = rpx - right_panel_w // 2
            rp_right = rpx + right_panel_w // 2

            # -- Current prediction box (top of right panel) --
            pred_box_h = 180
            pred_y = H - header_h - 10 - pred_box_h // 2

            if self.current and self.current.category in CATEGORIES:
                cat = CATEGORIES[self.current.category]
                col = cat['color']

                pulse_scale = 1.0 + (self.pulse * 0.03)
                bw = right_panel_w * pulse_scale
                bh = pred_box_h * pulse_scale

                bg_col = (col[0] // 4, col[1] // 4, col[2] // 4, 180)
                self.draw_panel(rpx, pred_y, bw, bh, bg_col)
                arcade.draw_rect_outline(arcade.rect.XYWH(rpx, pred_y, bw + 4, bh + 4),
                                        with_alpha(col, 100), 2)

                icon_text = self.text_manager.get('pred_icon', cat['icon'],
                                                 rpx, pred_y + 35,
                                                 (255, 255, 255, 255), 36)
                icon_text.draw()

                name_text = self.text_manager.get('pred_name', cat['name'].upper(),
                                                 rpx, pred_y - 5, col, 20, bold=True)
                name_text.draw()

                bar_y = pred_y - 45
                bar_w = right_panel_w - 60
                arcade.draw_rect_filled(arcade.rect.XYWH(rpx, bar_y, bar_w, 16),
                                       (60, 60, 70, 255))
                fill_w = self.bar_width * bar_w / 280
                if fill_w > 0:
                    arcade.draw_rect_filled(arcade.rect.XYWH(rpx - bar_w / 2 + fill_w / 2,
                                                             bar_y, fill_w, 16), col)

                conf_text = self.text_manager.get('conf', f"{self.current.confidence:.1%}",
                                                 rpx, bar_y, (255, 255, 255, 255), 11)
                conf_text.draw()
            else:
                self.draw_panel(rpx, pred_y, right_panel_w, pred_box_h, (30, 30, 40, 200))
                no_det_text = self.text_manager.get('no_det', "NO DETECTION",
                                                   rpx, pred_y,
                                                   (100, 100, 100, 255), 18)
                no_det_text.draw()

            # -- Legend panel (below prediction) --
            legend_top = pred_y - pred_box_h // 2 - 15
            legend_bottom = bottom_h + 15
            legend_h = legend_top - legend_bottom
            legend_cy = legend_bottom + legend_h // 2

            self.draw_panel(rpx, legend_cy, right_panel_w, legend_h, (25, 25, 35, 200))

            # Legend title
            leg_title = self.text_manager.get('leg_title', "CATEGORY LEGEND",
                                             rpx, legend_top - 18,
                                             (255, 255, 255, 255), 13, bold=True)
            leg_title.draw()

            # Draw each category as a legend row
            num_cats = len(CATEGORIES)
            row_h = min(38, (legend_h - 40) / num_cats)
            start_y = legend_top - 40

            for i, (key, data) in enumerate(CATEGORIES.items()):
                y = start_y - i * row_h
                count = self.counts[key]
                is_active = self.current and self.current.category == key

                # Color swatch
                swatch_x = rp_left + 25
                swatch_color = data['color'] if is_active else with_alpha(data['color'], 150)
                arcade.draw_rect_filled(arcade.rect.XYWH(swatch_x, y, 14, 14), swatch_color)
                if is_active:
                    arcade.draw_rect_outline(arcade.rect.XYWH(swatch_x, y, 18, 18),
                                           (255, 255, 255, 255), 2)

                # Category name
                name_color = data['color'] if is_active else (200, 200, 200, 255)
                leg_name = self.text_manager.get(f'leg_{key}_name', data['name'],
                                                swatch_x + 20, y - 6,
                                                name_color, 11, anchor_x="left",
                                                bold=is_active)
                leg_name.draw()

                # Count
                leg_count = self.text_manager.get(f'leg_{key}_count', str(count),
                                                 rp_right - 20, y - 6,
                                                 data['color'], 12, bold=True,
                                                 anchor_x="right")
                leg_count.draw()

                # Mini bar (proportional to max count)
                max_count = max(self.counts.values()) if self.counts else 1
                bar_max_w = right_panel_w * 0.30
                bar_filled = (count / max_count) * bar_max_w if max_count > 0 else 0
                bar_x_start = rp_right - 45 - bar_max_w

                arcade.draw_rect_filled(arcade.rect.XYWH(bar_x_start + bar_max_w / 2,
                                       y, bar_max_w, 8), (40, 40, 50, 255))
                if bar_filled > 0:
                    arcade.draw_rect_filled(
                        arcade.rect.XYWH(bar_x_start + bar_filled / 2, y, bar_filled, 8),
                        with_alpha(data['color'], 180))

            # ── Bottom: History ──
            self.draw_panel(W // 2, history_y, W - margin * 2, bottom_h, (25, 25, 35, 200))
            hist_title = self.text_manager.get('hist_title', "RECENT DETECTIONS",
                                              margin + 10, history_y + 50,
                                              (255, 255, 255, 255), 14, bold=True, anchor_x="left")
            hist_title.draw()

            # Calculate how many items fit
            available_w = W - margin * 2 - 80
            item_w = 130
            max_items = max(1, int(available_w / item_w))
            start_x = margin + 80

            for i, pred in enumerate(list(self.predictions)[:max_items]):
                x = start_x + i * item_w
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
        print("WARNING: Using default IP 192.168.1.100")
        print("    Update config.json with your ESP32-CAM IP")
        print("    Stream URL:", f"http://{CONFIG['esp32_ip']}:{CONFIG['stream_port']}/stream")
    
    app = Dashboard()
    arcade.run()