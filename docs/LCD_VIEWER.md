# LCD Viewer Application

## Overview

A Tkinter-based application for displaying real-time system monitoring on an LCD screen connected to the Raspberry Pi.

## Features

- **Live Camera Feed** with YOLO object detection and bounding boxes
- **Detection Logs** showing detected objects with timestamps
- **Sensor Readings** from all connected sensors
- **Hardware Control States** (pump, fan, pH adjuster, aerator, grow light)
- **System Logs** with color-coded messages

## Usage

### Run Live Mode (with hardware)
```bash
python3 lcd_viewer.py
```

### Run Demo Mode (without hardware)
```bash
python3 lcd_viewer.py --demo
```

Or use the interactive launcher:
```bash
./start_lcd_viewer.sh
```

## Requirements

### System Packages
```bash
sudo apt-get install python3-tk python3-pil python3-pil.imagetk
```

### Python Dependencies
All dependencies are in `requirements.txt`:
- tkinter (built-in)
- Pillow (PIL)
- opencv-python
- numpy
- ultralytics (YOLOv8)

### Hardware
- Raspberry Pi (3B+ or newer recommended)
- LCD touchscreen (800x480 or similar)
- Camera module or USB camera
- Configured sensors and GPIO relays

## Configuration

### Display Resolution
Edit `lcd_viewer.py` line 72:
```python
self.root.geometry("800x480")  # Change to your LCD size
```

### Fullscreen Mode
Uncomment line 74 in `lcd_viewer.py` for fullscreen:
```python
self.root.attributes('-fullscreen', True)
```

### Camera Settings
Edit `config.py`:
```python
CAMERA_RESOLUTION = (640, 480)
CAMERA_FPS = 15
```

## UI Layout

### Left Panel
- Live camera feed with bounding boxes
- Detection count and FPS display

### Right Panel (Tabbed)
1. **Detections** - Detection logs with timestamps
2. **Sensors** - Live readings from 8 sensors
3. **Controls** - Status of 5 hardware controls
4. **Logs** - Color-coded system logs

### Status Bar
- Current time
- FPS counter
- System mode (LIVE/DEMO)

## Architecture

The app uses a multi-threaded architecture:
- **Main Thread** - Tkinter UI loop
- **Camera Thread** - Captures frames and runs YOLO detection
- **Sensor Thread** - Reads sensor data every 2 seconds
- **Control Thread** - Monitors GPIO states every 1 second

Data flows through queues to prevent UI blocking.

## Performance Tips

### Raspberry Pi 4
- Resolution: 640x480
- FPS: 30
- Model: yolov8n.pt or yolov8s.pt

### Raspberry Pi 3B+
- Resolution: 480x320
- FPS: 15-20
- Model: yolov8n.pt

### Raspberry Pi 3B
- Resolution: 320x240
- FPS: 10-15
- Model: yolov8n.pt

## Troubleshooting

### Camera Not Found
```bash
# Test camera
raspistill -o test.jpg
ls /dev/video*

# Add user to video group
sudo usermod -a -G video $USER
```

### GPIO Permission Denied
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

### Display Issues
```bash
export DISPLAY=:0
xhost +
```

### Import Errors
Run in demo mode to test without hardware:
```bash
python3 lcd_viewer.py --demo
```

## Files

- `lcd_viewer.py` - Main application
- `start_lcd_viewer.sh` - Interactive launcher script
- `camera_ml.py` - Camera and YOLO integration
- `hardware_control.py` - GPIO control interface
- `*_sensor.py` - Individual sensor modules
- `config.py` - System configuration

## Notes

- The LCD viewer is **read-only** and does not send control commands
- Hardware controls are managed via the Flask API in `server.py`
- The viewer only monitors and displays system state
- Demo mode is useful for testing UI without actual hardware
