#!/usr/bin/env python3
"""Run the Flask REST API server"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.api.server import app

if __name__ == '__main__':
    print("🚀 GrowUp IoT - Flask API Server")
    print("=" * 50)
    print("📡 Endpoints:")
    print("   GET  /sensors          - Sensor readings")
    print("   GET  /controls         - Control states")
    print("   POST /controls         - Update controls")
    print("   GET  /status           - System status")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
