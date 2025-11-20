import threading, asyncio
from server import app, get_sensors, camera_ml
from camera.camera_ws import start_server
from apscheduler.schedulers.background import BackgroundScheduler
from influxdb_client import save_weekly_data

# HTTP server
threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()

# Camera WebSocket server
threading.Thread(target=lambda: asyncio.run(start_server()), daemon=True).start()

# Weekly logging
def log_weekly():
    sensors = get_sensors().get_json()
    ml_result = camera_ml.last_result
    save_weekly_data(sensors, ml_result)

scheduler = BackgroundScheduler()
scheduler.add_job(log_weekly, 'interval', weeks=1)
scheduler.start()

print("IoT system running. Weekly logging enabled.")
