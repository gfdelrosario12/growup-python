#!/usr/bin/env python3
"""Run the Camera WebSocket server"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.camera_ws import start_server

if __name__ == '__main__':
    print("🚀 GrowUp IoT - Camera WebSocket Server")
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print('\n🛑 Server stopped')
