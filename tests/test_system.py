#!/usr/bin/env python3
"""
GrowUp IoT System - System Test & Fix
=====================================
Tests all imports and provides diagnostics
"""

import sys
import os

print("="*60)
print("GrowUp IoT System - Diagnostic Test")
print("="*60)
print()

# Test 1: Python version
print(f"✅ Python Version: {sys.version}")
print()

# Test 2: Working directory
print(f"📁 Working Directory: {os.getcwd()}")
print()

# Test 3: Config import
print("Testing config.py import...")
try:
    from config import BACKEND_HOST, GPIO_PINS, print_config
    print("✅ config.py imported successfully")
    print(f"   Backend: {BACKEND_HOST}")
    print(f"   GPIO Pins: {list(GPIO_PINS.keys())}")
except Exception as e:
    print(f"❌ config.py import failed: {e}")
print()

# Test 4: Hardware control import
print("Testing hardware_control.py import...")
try:
    from hardware_control import get_hardware_controller, GPIO_AVAILABLE
    print("✅ hardware_control.py imported successfully")
    if GPIO_AVAILABLE:
        print("   🔌 Real GPIO available")
    else:
        print("   🔌 Using Mock GPIO (development mode)")
except Exception as e:
    print(f"❌ hardware_control.py import failed: {e}")
print()

# Test 5: Server import
print("Testing server.py import...")
try:
    from server import read_all_sensors
    print("✅ server.py imported successfully")
except Exception as e:
    print(f"❌ server.py import failed: {e}")
print()

# Test 6: LCD viewer import
print("Testing lcd_viewer.py import...")
try:
    from lcd_viewer import LCDViewer
    print("✅ lcd_viewer.py imported successfully")
except Exception as e:
    print(f"⚠️  lcd_viewer.py import failed: {e}")
    print("   This is OK if running without GUI")
print()

# Test 7: Main orchestrator import
print("Testing main.py classes...")
try:
    from main import GrowUpSystem
    print("✅ main.py imported successfully")
except Exception as e:
    print(f"❌ main.py import failed: {e}")
print()

# Test 8: New architecture
print("Testing new architecture (src/)...")
try:
    from src.config.settings import get_settings
    settings = get_settings()
    print("✅ src/config/settings.py working")
    print(f"   Backend: {settings.backend.base_url}")
except Exception as e:
    print(f"⚠️  New architecture not ready: {e}")
    print("   This is expected during migration")
print()

# Test 9: Required packages
print("Testing required packages...")
packages = {
    'requests': 'requests',
    'flask': 'Flask',
    'numpy': 'numpy',
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'ultralytics': 'ultralytics',
}

for module, package in packages.items():
    try:
        __import__(module)
        print(f"✅ {package} installed")
    except ImportError:
        print(f"⚠️  {package} not installed (pip install {package})")
print()

print("="*60)
print("Diagnostic Complete")
print("="*60)
print()

# Suggest next steps
print("📋 Next Steps:")
print()
if os.path.exists('config.py'):
    print("✅ config.py exists")
else:
    print("❌ config.py missing - system will use defaults")
print()

print("To run the system:")
print("  python3 main.py --lcd --demo")
print()
print("To install missing packages:")
print("  pip install -r requirements.txt")
print()
