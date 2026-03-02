#!/usr/bin/env python3
"""
GrowUp IoT - LCD Viewer Application
====================================

Real-time camera viewer with ML detection overlay for LCD screen.

Features:
- Live camera feed with bounding boxes
- Detection results panel
- System status monitoring
- Sensor readings display
- Control states display
- Auto-refresh and logging

For Raspberry Pi with LCD touchscreen (480x800 or 480x320)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

# Import project modules
try:
    from camera_ml import CameraML
    from temp_sensor import DS18B20
    from ph_sensor import PHSensor
    from humidity_sensor import BME280Sensor
    from light_sensor import BH1750
    from water_flow_sensor import FlowSensor
    from ammonia_sensor import MQ137
    from hardware_control import HardwareController
    import config
except ImportError as e:
    print(f"⚠️  Warning: Could not import some modules: {e}")
    print("Running in demo mode...")


class LCDViewerApp:
    """Main LCD Viewer Application"""
    
    def __init__(self, root: tk.Tk, demo_mode: bool = False):
        self.root = root
        self.demo_mode = demo_mode
        self.running = True
        
        # System manager reference (for integrated mode)
        self.system_manager = None
        self.external_data_mode = False
        
        # Queues for thread communication
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=10)
        self.log_queue = queue.Queue(maxsize=100)
        
        # Data storage
        self.current_frame = None
        self.latest_detections = []
        self.sensor_data = {}
        self.control_states = {}
        
        # Configure window
        self.setup_window()
        
        # Initialize hardware (if not demo mode)
        if not demo_mode:
            self.init_hardware()
        
        # Create UI
        self.create_ui()
        
        # Start background threads
        self.start_threads()
        
        # Start UI update loop
        self.update_ui()
        
        # Log startup
        self.add_log("🚀 GrowUp IoT Viewer Started", "INFO")
    
    def use_external_data(self, system_manager):
        """Use data from external system manager instead of own threads"""
        self.system_manager = system_manager
        self.external_data_mode = True
        self.add_log("📡 Using integrated system data", "INFO")
    
    def setup_window(self):
        """Configure main window"""
        self.root.title("GrowUp IoT - LCD Viewer")
        
        # Fullscreen for LCD (uncomment for production)
        # self.root.attributes('-fullscreen', True)
        
        # For development: set fixed size
        self.root.geometry("800x480")
        self.root.resizable(False, False)
        
        # Dark theme colors
        self.colors = {
            'bg': '#1a1a1a',
            'fg': '#ffffff',
            'panel': '#2d2d2d',
            'accent': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'info': '#3b82f6',
            'border': '#404040'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background=self.colors['panel'])
        style.configure('Dark.TLabel', 
                       background=self.colors['panel'],
                       foreground=self.colors['fg'],
                       font=('Arial', 9))
        style.configure('Title.TLabel',
                       background=self.colors['panel'],
                       foreground=self.colors['accent'],
                       font=('Arial', 11, 'bold'))
        
    def init_hardware(self):
        """Initialize hardware components"""
        try:
            self.camera_ml = CameraML()
            self.hardware_controller = HardwareController()
            
            # Initialize sensors
            self.sensors = {
                'temp': DS18B20(4),
                'ph': PHSensor(1),
                'humidity': BME280Sensor(),
                'light': BH1750(),
                'flow': FlowSensor(5),
                'ammonia': MQ137(0)
            }
            
            self.add_log("✅ Hardware initialized", "SUCCESS")
        except Exception as e:
            self.add_log(f"❌ Hardware init error: {e}", "ERROR")
            self.demo_mode = True
    
    def create_ui(self):
        """Create main user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Camera feed
        self.create_camera_panel(main_frame)
        
        # Right panel: Info and logs
        self.create_info_panel(main_frame)
        
        # Bottom: Status bar
        self.create_status_bar()
    
    def create_camera_panel(self, parent):
        """Create camera display panel"""
        camera_frame = ttk.Frame(parent, style='Dark.TFrame')
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Title
        title_label = ttk.Label(camera_frame, text="📹 Live Camera Feed",
                               style='Title.TLabel')
        title_label.pack(pady=5)
        
        # Camera canvas
        self.camera_canvas = tk.Canvas(camera_frame, 
                                       width=480, 
                                       height=360,
                                       bg='black',
                                       highlightthickness=1,
                                       highlightbackground=self.colors['border'])
        self.camera_canvas.pack(pady=5)
        
        # Detection count label
        self.detection_label = ttk.Label(camera_frame,
                                         text="Detections: 0 | FPS: 0",
                                         style='Dark.TLabel')
        self.detection_label.pack(pady=5)
    
    def create_info_panel(self, parent):
        """Create information panel (sensors, controls, logs)"""
        info_frame = ttk.Frame(parent, style='Dark.TFrame', width=300)
        info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        info_frame.pack_propagate(False)
        
        # Create notebook (tabs)
        notebook = ttk.Notebook(info_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Tab 1: Detections
        self.create_detections_tab(notebook)
        
        # Tab 2: Sensors
        self.create_sensors_tab(notebook)
        
        # Tab 3: Controls
        self.create_controls_tab(notebook)
        
        # Tab 4: Logs
        self.create_logs_tab(notebook)
    
    def create_detections_tab(self, notebook):
        """Create detections display tab"""
        det_frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(det_frame, text='🎯 Detections')
        
        # Scrollable text area
        self.detections_text = scrolledtext.ScrolledText(
            det_frame,
            wrap=tk.WORD,
            width=35,
            height=20,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Courier', 9),
            insertbackground=self.colors['accent']
        )
        self.detections_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.detections_text.insert('1.0', 'Waiting for detections...\n')
        self.detections_text.config(state=tk.DISABLED)
    
    def create_sensors_tab(self, notebook):
        """Create sensors display tab"""
        sensor_frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(sensor_frame, text='🌡️ Sensors')
        
        # Sensor labels
        self.sensor_labels = {}
        sensors_config = [
            ('waterTemp', 'Water Temp', '°C'),
            ('ph', 'pH Level', ''),
            ('dissolvedO2', 'Dissolved O₂', 'mg/L'),
            ('airTemp', 'Air Temp', '°C'),
            ('humidity', 'Humidity', '%'),
            ('lightIntensity', 'Light', 'lux'),
            ('waterFlow', 'Flow Rate', 'L/min'),
            ('ammonia', 'Ammonia', 'ppm'),
        ]
        
        for i, (key, name, unit) in enumerate(sensors_config):
            frame = tk.Frame(sensor_frame, bg=self.colors['panel'])
            frame.pack(fill=tk.X, padx=5, pady=3)
            
            label = tk.Label(frame, text=f"{name}:",
                           bg=self.colors['panel'],
                           fg=self.colors['fg'],
                           font=('Arial', 9),
                           anchor='w')
            label.pack(side=tk.LEFT)
            
            value_label = tk.Label(frame, text=f"-- {unit}",
                                  bg=self.colors['panel'],
                                  fg=self.colors['accent'],
                                  font=('Arial', 9, 'bold'),
                                  anchor='e')
            value_label.pack(side=tk.RIGHT)
            
            self.sensor_labels[key] = value_label
    
    def create_controls_tab(self, notebook):
        """Create controls display tab"""
        control_frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(control_frame, text='🎮 Controls')
        
        # Control status labels
        self.control_labels = {}
        controls_config = [
            ('pump', '💧 Pump'),
            ('fan', '🌀 Fan'),
            ('phAdjustment', '⚗️ pH Adjuster'),
            ('aerator', '🫧 Aerator'),
            ('growLight', '💡 Grow Light'),
        ]
        
        for key, name in controls_config:
            frame = tk.Frame(control_frame, bg=self.colors['panel'])
            frame.pack(fill=tk.X, padx=5, pady=5)
            
            label = tk.Label(frame, text=name,
                           bg=self.colors['panel'],
                           fg=self.colors['fg'],
                           font=('Arial', 10),
                           anchor='w')
            label.pack(side=tk.LEFT)
            
            status_label = tk.Label(frame, text="●",
                                   bg=self.colors['panel'],
                                   fg='gray',
                                   font=('Arial', 16),
                                   anchor='e')
            status_label.pack(side=tk.RIGHT)
            
            self.control_labels[key] = status_label
    
    def create_logs_tab(self, notebook):
        """Create logs display tab"""
        log_frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(log_frame, text='📋 Logs')
        
        # Scrollable log area
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=35,
            height=20,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Courier', 8),
            insertbackground=self.colors['accent']
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # Configure tags for colored logs
        self.log_text.tag_config('INFO', foreground=self.colors['info'])
        self.log_text.tag_config('SUCCESS', foreground=self.colors['accent'])
        self.log_text.tag_config('WARNING', foreground=self.colors['warning'])
        self.log_text.tag_config('ERROR', foreground=self.colors['error'])
    
    def create_status_bar(self):
        """Create bottom status bar"""
        status_frame = tk.Frame(self.root, bg=self.colors['panel'], height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status labels
        self.status_time = tk.Label(status_frame, text="",
                                   bg=self.colors['panel'],
                                   fg=self.colors['fg'],
                                   font=('Arial', 9))
        self.status_time.pack(side=tk.LEFT, padx=10)
        
        self.status_fps = tk.Label(status_frame, text="FPS: 0",
                                  bg=self.colors['panel'],
                                  fg=self.colors['accent'],
                                  font=('Arial', 9))
        self.status_fps.pack(side=tk.LEFT, padx=10)
        
        self.status_mode = tk.Label(status_frame,
                                   text="🔴 DEMO MODE" if self.demo_mode else "🟢 LIVE",
                                   bg=self.colors['panel'],
                                   fg=self.colors['warning'] if self.demo_mode else self.colors['accent'],
                                   font=('Arial', 9, 'bold'))
        self.status_mode.pack(side=tk.RIGHT, padx=10)
    
    def start_threads(self):
        """Start background worker threads"""
        # Camera thread
        camera_thread = threading.Thread(target=self.camera_worker, daemon=True)
        camera_thread.start()
        
        # Sensor reading thread
        if not self.demo_mode:
            sensor_thread = threading.Thread(target=self.sensor_worker, daemon=True)
            sensor_thread.start()
            
            # Control monitoring thread
            control_thread = threading.Thread(target=self.control_worker, daemon=True)
            control_thread.start()
    
    def camera_worker(self):
        """Background thread for camera capture and ML processing"""
        frame_count = 0
        fps_start = time.time()
        
        while self.running:
            try:
                if self.demo_mode:
                    # Demo mode: generate dummy frame
                    frame = self.generate_demo_frame()
                    detections = self.generate_demo_detections()
                else:
                    # Real mode: capture from camera
                    frame, results = self.camera_ml.read_frame()
                    if frame is None:
                        time.sleep(0.1)
                        continue
                    detections = self.parse_yolo_results(results)
                
                # Draw bounding boxes
                frame_with_boxes = self.draw_detections(frame, detections)
                
                # Update queues
                if not self.frame_queue.full():
                    self.frame_queue.put(frame_with_boxes)
                
                if detections:
                    self.detection_queue.put(detections)
                
                # Calculate FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    fps = 30 / (time.time() - fps_start)
                    self.status_fps.config(text=f"FPS: {fps:.1f}")
                    fps_start = time.time()
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                self.add_log(f"Camera error: {e}", "ERROR")
                time.sleep(1)
    
    def sensor_worker(self):
        """Background thread for reading sensors"""
        while self.running:
            try:
                humidity_data = self.sensors['humidity'].read()
                
                self.sensor_data = {
                    'waterTemp': self.sensors['temp'].read_temp(),
                    'ph': self.sensors['ph'].read(),
                    'dissolvedO2': 7.8,  # TODO: Add DO sensor
                    'airTemp': humidity_data.get('temperature', 24.0),
                    'humidity': humidity_data.get('humidity', 65),
                    'lightIntensity': self.sensors['light'].read_light(),
                    'waterFlow': self.sensors['flow'].get_flow_rate(),
                    'ammonia': self.sensors['ammonia'].read(),
                    'airPressure': humidity_data.get('pressure', 1013.25),
                }
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                self.add_log(f"Sensor error: {e}", "ERROR")
                time.sleep(5)
    
    def control_worker(self):
        """Background thread for monitoring control states"""
        while self.running:
            try:
                self.control_states = self.hardware_controller.get_states()
                time.sleep(1)  # Update every second
                
            except Exception as e:
                self.add_log(f"Control error: {e}", "ERROR")
                time.sleep(5)
    
    def update_ui(self):
        """Main UI update loop (runs on main thread)"""
        if not self.running:
            return
        
        # Update status bar time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.status_time.config(text=f"🕐 {current_time}")
        
        # Update camera feed
        self.update_camera_display()
        
        # Update detections
        self.update_detections_display()
        
        # Update sensors
        self.update_sensors_display()
        
        # Update controls
        self.update_controls_display()
        
        # Update logs
        self.update_logs_display()
        
        # Schedule next update
        self.root.after(100, self.update_ui)  # 10 FPS UI update
    
    def update_camera_display(self):
        """Update camera canvas with latest frame"""
        try:
            frame = self.frame_queue.get_nowait()
            
            # Convert to PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Resize to fit canvas
            pil_image = pil_image.resize((480, 360), Image.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update canvas
            self.camera_canvas.delete("all")
            self.camera_canvas.create_image(240, 180, image=photo)
            self.camera_canvas.image = photo  # Keep reference
            
        except queue.Empty:
            pass
    
    def update_detections_display(self):
        """Update detections text area"""
        try:
            detections = self.detection_queue.get_nowait()
            
            # Format detections
            timestamp = datetime.now().strftime("%H:%M:%S")
            text = f"\n[{timestamp}] {len(detections)} detection(s):\n"
            
            for det in detections:
                text += f"  • {det['class']}: {det['confidence']:.2%}\n"
                text += f"    Box: [{det['box'][0]:.0f}, {det['box'][1]:.0f}, {det['box'][2]:.0f}, {det['box'][3]:.0f}]\n"
            
            # Update text widget
            self.detections_text.config(state=tk.NORMAL)
            self.detections_text.insert('1.0', text)
            
            # Keep only last 1000 characters
            content = self.detections_text.get('1.0', tk.END)
            if len(content) > 1000:
                self.detections_text.delete('1.0', '500.0')
            
            self.detections_text.config(state=tk.DISABLED)
            
            # Update detection label
            self.detection_label.config(text=f"Detections: {len(detections)}")
            
            # Log detection
            classes = [d['class'] for d in detections]
            self.add_log(f"Detected: {', '.join(classes)}", "INFO")
            
        except queue.Empty:
            pass
    
    def update_sensors_display(self):
        """Update sensor value labels"""
        if not self.sensor_data:
            return
        
        format_map = {
            'waterTemp': lambda v: f"{v:.1f} °C",
            'ph': lambda v: f"{v:.1f}",
            'dissolvedO2': lambda v: f"{v:.1f} mg/L",
            'airTemp': lambda v: f"{v:.1f} °C",
            'humidity': lambda v: f"{v:.0f} %",
            'lightIntensity': lambda v: f"{v:.0f} lux",
            'waterFlow': lambda v: f"{v:.1f} L/min",
            'ammonia': lambda v: f"{v:.3f} ppm",
        }
        
        for key, value in self.sensor_data.items():
            if key in self.sensor_labels:
                formatted = format_map.get(key, str)(value)
                self.sensor_labels[key].config(text=formatted)
    
    def update_controls_display(self):
        """Update control status indicators"""
        if not self.control_states:
            return
        
        for key, state in self.control_states.items():
            if key in self.control_labels:
                color = self.colors['accent'] if state else 'gray'
                self.control_labels[key].config(fg=color)
    
    def update_logs_display(self):
        """Update logs text area"""
        updated = False
        while True:
            try:
                log_entry = self.log_queue.get_nowait()
                
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert('1.0', log_entry['text'], log_entry['level'])
                
                # Keep only last 5000 characters
                content = self.log_text.get('1.0', tk.END)
                if len(content) > 5000:
                    self.log_text.delete('1.0', '2500.0')
                
                self.log_text.config(state=tk.DISABLED)
                updated = True
                
            except queue.Empty:
                break
        
        if updated:
            self.log_text.see('1.0')  # Scroll to top
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add log entry to queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {message}\n"
        
        self.log_queue.put({
            'text': log_text,
            'level': level
        })
    
    def draw_detections(self, frame, detections: List[Dict]):
        """Draw bounding boxes and labels on frame"""
        frame_copy = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det['box'])
            label = det['class']
            conf = det['confidence']
            
            # Draw rectangle
            color = (0, 255, 0)  # Green
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            label_text = f"{label} {conf:.2%}"
            (w, h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame_copy, (x1, y1 - h - 10), (x1 + w, y1), color, -1)
            
            # Draw label text
            cv2.putText(frame_copy, label_text, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        return frame_copy
    
    def parse_yolo_results(self, results) -> List[Dict]:
        """Parse YOLO detection results"""
        detections = []
        
        if results is None:
            return detections
        
        try:
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    detections.append({
                        'box': [x1, y1, x2, y2],
                        'confidence': conf,
                        'class': r.names[cls]
                    })
        except Exception as e:
            self.add_log(f"YOLO parse error: {e}", "ERROR")
        
        return detections
    
    def generate_demo_frame(self):
        """Generate demo frame for testing"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add text
        text = "DEMO MODE - Camera Feed"
        cv2.putText(frame, text, (100, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add time
        time_text = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, time_text, (250, 280),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame
    
    def generate_demo_detections(self) -> List[Dict]:
        """Generate demo detections for testing"""
        import random
        
        if random.random() > 0.7:  # 30% chance of detection
            return [{
                'box': [100, 100, 300, 300],
                'confidence': random.uniform(0.7, 0.95),
                'class': random.choice(['lettuce', 'basil', 'tomato'])
            }]
        return []
    
    def cleanup(self):
        """Cleanup resources on exit"""
        self.running = False
        self.add_log("👋 Shutting down viewer...", "INFO")
        
        if not self.demo_mode:
            try:
                self.camera_ml.cap.release()
            except:
                pass
        
        self.root.quit()


def main():
    """Main entry point"""
    import sys
    
    # Check for demo mode
    demo_mode = '--demo' in sys.argv or '-d' in sys.argv
    
    # Create Tkinter root
    root = tk.Tk()
    
    # Create application
    app = LCDViewerApp(root, demo_mode=demo_mode)
    
    # Handle window close
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start Tkinter main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.cleanup()


if __name__ == "__main__":
    main()
