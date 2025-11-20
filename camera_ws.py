import asyncio, base64, cv2, websockets
from camera_ml import CameraML

camera = CameraML()

async def camera_server(websocket, path):
    while True:
        frame, _ = camera.read_frame()
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            await websocket.send(jpg_as_text)
        await asyncio.sleep(0.03)

async def start_server():
    async with websockets.serve(camera_server, "0.0.0.0", 8765):
        await asyncio.Future()
