import os
import asyncio
import base64
import cv2
import websockets
from camera_ml import CameraML

camera = CameraML()

async def camera_server(websocket, path):
    while True:
        frame, _ = camera.read_frame()
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            try:
                await websocket.send(jpg_as_text)
            except websockets.ConnectionClosed:
                break
        await asyncio.sleep(0.03)


async def start_server(host: str = None, port: int = None):
    """Start the websocket server. Host and port can be provided via env variables.
    Defaults: host=0.0.0.0, port=8765
    """
    host = host or os.getenv('WS_HOST', '0.0.0.0')
    port = port or int(os.getenv('WS_PORT', '8765'))

    print(f"🚀 Starting camera websocket server on {host}:{port}")
    async with websockets.serve(camera_server, host, port):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    # Allow overrides via environment variables
    host = os.getenv('WS_HOST', '0.0.0.0')
    port = int(os.getenv('WS_PORT', '8765'))

    try:
        asyncio.run(start_server(host, port))
    except KeyboardInterrupt:
        print('\n🛑 Camera websocket server stopped by user')
