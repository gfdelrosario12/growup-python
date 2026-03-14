import asyncio
import json
import os
import threading
import time
import base64
import requests
from io import BytesIO
from collections import deque

import cv2
import numpy as np

import websockets

try:
    import paho.mqtt.client as mqtt
    _HAS_MQTT = True
except Exception:
    _HAS_MQTT = False

from camera.ml_classification import MLClassifier

# Configuration via environment
WS_HOST = os.getenv("CAM_WS_HOST", "0.0.0.0")
WS_PORT = int(os.getenv("CAM_WS_PORT", "8765"))
CAM_INDEX = int(os.getenv("CAM_INDEX", "0"))
MODEL_PATH = os.getenv("CAM_MODEL_PATH", "yolov8n.pt")
SEND_FRAMES = os.getenv("CAM_SEND_FRAMES", "false").lower() in ("1", "true", "yes")
MQTT_BROKER = os.getenv("MQTT_BROKER", "")
MQTT_TOPIC = os.getenv("MQTT_DETECTIONS_TOPIC", "camera/detections")
FRAME_SCALE = float(os.getenv("CAM_FRAME_SCALE", "0.5"))  # scale down frames before sending to save bandwidth
CAPTURE_FPS = float(os.getenv("CAM_CAPTURE_FPS", "5"))
ML_RESULTS_ENDPOINT = os.getenv("ML_RESULTS_ENDPOINT", "http://localhost:8080/api/ml-results")
DEVICE_ID = os.getenv("DEVICE_ID", "pi-001")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
SEND_ML_RESULTS = os.getenv("SEND_ML_RESULTS", "true").lower() in ("1", "true", "yes")

_clients = set()
_broadcast_queue = asyncio.Queue(maxsize=10)
_stop_event = threading.Event()


class PlantTracker:
    """
    Track plants across frames with persistent IDs.
    Computes health scores, detects anomalies (missing/new plants).
    """
    def __init__(self, max_history=30, confidence_threshold=0.5):
        self.plants = {}  # {plant_id: {"bbox": [...], "confidence": float, "last_seen": timestamp, "history": deque}}
        self.next_id = 0
        self.max_history = max_history
        self.confidence_threshold = confidence_threshold
        self.stats = {
            "total_detected": 0,
            "total_plants": 0,
            "avg_confidence": 0.0,
            "missing_plants": [],
            "new_plants": []
        }

    def _bbox_center(self, bbox):
        """Calculate center of bounding box."""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def _bbox_distance(self, bbox1, bbox2):
        """Euclidean distance between bbox centers."""
        c1 = self._bbox_center(bbox1)
        c2 = self._bbox_center(bbox2)
        return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5

    def _bbox_area(self, bbox):
        """Bounding box area."""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)

    def update(self, detections):
        """
        Update plant tracking with new detections.
        Returns enriched detections with plant_id and stats.
        """
        current_time = time.time()
        matched_ids = set()
        enriched_detections = []

        # Try to match each detection to an existing plant
        for det in detections:
            best_match_id = None
            best_distance = float('inf')
            best_area_similarity = 0

            for plant_id, plant_data in self.plants.items():
                if plant_id in matched_ids:
                    continue

                # Distance-based matching + area similarity
                dist = self._bbox_distance(det["bbox"], plant_data["bbox"])
                old_area = self._bbox_area(plant_data["bbox"])
                new_area = self._bbox_area(det["bbox"])
                area_ratio = min(old_area, new_area) / max(old_area, new_area) if max(old_area, new_area) > 0 else 0

                # Prefer matches with low distance and high area similarity
                if dist < 100 and area_ratio > 0.5 and dist < best_distance:
                    best_distance = dist
                    best_area_similarity = area_ratio
                    best_match_id = plant_id

            if best_match_id is not None:
                # Update existing plant
                plant_id = best_match_id
                matched_ids.add(plant_id)
                self.plants[plant_id]["bbox"] = det["bbox"]
                self.plants[plant_id]["confidence"] = det["confidence"]
                self.plants[plant_id]["last_seen"] = current_time
                self.plants[plant_id]["history"].append({
                    "timestamp": current_time,
                    "confidence": det["confidence"],
                    "bbox": det["bbox"]
                })
                if len(self.plants[plant_id]["history"]) > self.max_history:
                    self.plants[plant_id]["history"].popleft()
            else:
                # New plant detected
                plant_id = self.next_id
                self.next_id += 1
                self.plants[plant_id] = {
                    "bbox": det["bbox"],
                    "confidence": det["confidence"],
                    "class_name": det["class_name"],
                    "last_seen": current_time,
                    "first_seen": current_time,
                    "history": deque([{
                        "timestamp": current_time,
                        "confidence": det["confidence"],
                        "bbox": det["bbox"]
                    }], maxlen=self.max_history)
                }
                matched_ids.add(plant_id)
                self.stats["new_plants"].append({"plant_id": plant_id, "timestamp": current_time})

            # Enrich detection with plant_id and tracking info
            enriched_detections.append({
                "plant_id": plant_id,
                "bbox": det["bbox"],
                "confidence": det["confidence"],
                "class_name": det["class_name"],
                "age_seconds": int(current_time - self.plants[plant_id]["first_seen"]),
                "tracking_frames": len(self.plants[plant_id]["history"])
            })

        # Detect missing plants (not seen recently)
        missing_threshold = 5.0  # seconds
        for plant_id, plant_data in list(self.plants.items()):
            if plant_id not in matched_ids:
                if current_time - plant_data["last_seen"] > missing_threshold:
                    self.stats["missing_plants"].append({"plant_id": plant_id, "timestamp": current_time})
                    del self.plants[plant_id]

        # Update statistics
        self.stats["total_detected"] = len(enriched_detections)
        self.stats["total_plants"] = len(self.plants)
        if enriched_detections:
            self.stats["avg_confidence"] = sum(d["confidence"] for d in enriched_detections) / len(enriched_detections)

        return enriched_detections, self.stats

    def get_health_score(self):
        """
        Compute overall plant health based on detection confidence and consistency.
        Returns a score 0-100.
        """
        if not self.plants:
            return 0

        scores = []
        for plant_data in self.plants.values():
            # Confidence-based score
            confidence_score = plant_data["confidence"] * 100
            
            # Consistency score (high if plant is consistently detected)
            if plant_data["history"]:
                avg_hist_conf = sum(h["confidence"] for h in plant_data["history"]) / len(plant_data["history"])
                consistency_score = avg_hist_conf * 100
            else:
                consistency_score = 0

            # Weighted average
            plant_score = 0.6 * confidence_score + 0.4 * consistency_score
            scores.append(plant_score)

        return int(sum(scores) / len(scores)) if scores else 0


class MQTTBridge:
    def __init__(self, broker_url):
        self.broker_url = broker_url
        self.client = None
        if _HAS_MQTT and broker_url:
            self.client = mqtt.Client()
            try:
                self.client.connect(broker_url)
                self.client.loop_start()
            except Exception as e:
                print(f"⚠️  MQTT connect failed: {e}")
                self.client = None

    def publish(self, topic, payload):
        if not self.client:
            return
        try:
            self.client.publish(topic, payload)
        except Exception as e:
            print(f"⚠️  MQTT publish error: {e}")


def send_ml_results_to_backend(detections, health_score, tracker_stats):
    """
    Send ML detection results to /api/ml-results backend endpoint.
    
    Args:
        detections: list of detection dicts
        health_score: overall health score (0-100)
        tracker_stats: dict with total_detected, total_plants, avg_confidence
    """
    if not SEND_ML_RESULTS:
        return
    
    try:
        payload = {
            "deviceId": DEVICE_ID,
            "timestamp": int(time.time()),
            "detections": detections,
            "health_score": health_score,
            "totalPlants": tracker_stats.get("total_plants", 0),
            "avgConfidence": round(tracker_stats.get("avg_confidence", 0), 3)
        }
        
        response = requests.post(
            ML_RESULTS_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"⚠️  ML results endpoint returned {response.status_code}")
    except Exception as e:
        print(f"⚠️  Error sending ML results: {e}")


def _encode_frame_to_jpeg_b64(frame):
    # frame is an OpenCV BGR image
    ret, jpg = cv2.imencode('.jpg', frame)
    if not ret:
        return None
    b64 = base64.b64encode(jpg.tobytes()).decode('ascii')
    return b64


def _prepare_message(detections, frame=None):
    message = {
        "timestamp": int(time.time()),
        "detections": detections
    }
    if SEND_FRAMES and frame is not None:
        try:
            b64 = _encode_frame_to_jpeg_b64(frame)
            if b64:
                message["frame_jpg_b64"] = b64
        except Exception as e:
            print(f"⚠️  Frame encode error: {e}")
    return json.dumps(message)


def camera_capture_loop(classifier: MLClassifier, ws_queue: asyncio.Queue, mqtt_bridge, stop_event: threading.Event):
    """
    Unified camera capture + ML inference + plant tracking loop.
    Runs inference ONCE per frame, tracks plants, computes health scores.
    Efficient: no duplicate inference.
    """
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        print(f"❌ Unable to open camera index {CAM_INDEX}")
        return

    # Try to set a reasonable resolution on Pi to save CPU/bandwidth
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    except Exception:
        pass

    tracker = PlantTracker(max_history=30, confidence_threshold=0.5)
    print(f"📷 Camera initialized (index={CAM_INDEX}, fps={CAPTURE_FPS}, scale={FRAME_SCALE})")
    interval = 1.0 / max(0.1, CAPTURE_FPS)
    frame_count = 0
    
    while not stop_event.is_set():
        start = time.time()
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        frame_count += 1

        # Scale frame for faster inference / smaller transfer
        inference_frame = frame
        if FRAME_SCALE != 1.0:
            try:
                h, w = frame.shape[:2]
                inference_frame = cv2.resize(frame, (int(w * FRAME_SCALE), int(h * FRAME_SCALE)))
            except Exception:
                pass

        # Single ML inference
        detections = []
        try:
            detections = classifier.classify_frame(inference_frame)
        except Exception as e:
            print(f"❌ ML error: {e}")

        # Track plants across frames
        enriched_detections, tracker_stats = tracker.update(detections)
        health_score = tracker.get_health_score()

        # Prepare enriched message for WebSocket
        try:
            ws_message_data = {
                "timestamp": int(time.time()),
                "frame_count": frame_count,
                "detections": enriched_detections,
                "health_score": health_score,
                "tracking_stats": {
                    "total_detected": tracker_stats["total_detected"],
                    "total_plants": tracker_stats["total_plants"],
                    "avg_confidence": round(tracker_stats["avg_confidence"], 3)
                }
            }
            
            if SEND_FRAMES:
                try:
                    b64 = _encode_frame_to_jpeg_b64(frame)
                    if b64:
                        ws_message_data["frame_jpg_b64"] = b64
                except Exception as e:
                    print(f"⚠️  Frame encode error: {e}")

            ws_message = json.dumps(ws_message_data)
            
            # Broadcast to WebSocket queue (drop old if full)
            try:
                ws_queue.put_nowait(ws_message)
            except asyncio.QueueFull:
                try:
                    _ = ws_queue.get_nowait()
                    ws_queue.put_nowait(ws_message)
                except Exception:
                    pass
            
            # Also publish detections to MQTT (lightweight: no frame)
            if mqtt_bridge:
                try:
                    mqtt_message = json.dumps({
                        "timestamp": int(time.time()),
                        "frame_count": frame_count,
                        "detections": enriched_detections,
                        "health_score": health_score,
                        "tracking_stats": {
                            "total_detected": tracker_stats["total_detected"],
                            "total_plants": tracker_stats["total_plants"],
                            "avg_confidence": round(tracker_stats["avg_confidence"], 3)
                        }
                    })
                    mqtt_bridge.publish(MQTT_TOPIC, mqtt_message)
                except Exception as e:
                    print(f"⚠️  MQTT publish error: {e}")
            
            # Send ML results to backend
            try:
                send_ml_results_to_backend(enriched_detections, health_score, tracker_stats)
            except Exception as e:
                print(f"⚠️  Error in ML results backend call: {e}")
                    
        except Exception as e:
            print(f"❌ Message prep error: {e}")

        elapsed = time.time() - start
        to_sleep = max(0, interval - elapsed)
        time.sleep(to_sleep)

    cap.release()
    print("📷 Camera capture loop stopped")


async def _broadcaster(queue: asyncio.Queue):
    while True:
        try:
            message = await queue.get()
            if not message:
                continue
            if not _clients:
                continue
            coros = []
            to_remove = []
            for ws in list(_clients):
                coros.append(_send_safe(ws, message, to_remove))
            if coros:
                await asyncio.gather(*coros, return_exceptions=True)
            if to_remove:
                for ws in to_remove:
                    _clients.discard(ws)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ Broadcaster error: {e}")


async def _send_safe(ws, message, to_remove):
    try:
        await ws.send(message)
    except Exception:
        to_remove.append(ws)


async def ws_handler(websocket, path):
    # Register client
    _clients.add(websocket)
    print(f"➕ Client connected: {websocket.remote_address}")
    try:
        # Keep connection open; allow clients to send pings or request status
        async for _ in websocket:
            # Ignore incoming messages; clients can send a keep-alive
            pass
    finally:
        _clients.discard(websocket)
        print(f"➖ Client disconnected: {websocket.remote_address}")


def start_server():
    classifier = MLClassifier(MODEL_PATH)
    mqtt_bridge = MQTTBridge(MQTT_BROKER) if MQTT_BROKER and _HAS_MQTT else None

    loop = asyncio.get_event_loop()

    # Start camera capture thread with consolidated ML + MQTT + WS broadcast
    capture_thread = threading.Thread(
        target=camera_capture_loop,
        args=(classifier, _broadcast_queue, mqtt_bridge, _stop_event),
        daemon=True
    )
    capture_thread.start()

    # Start websocket server
    ws_server = websockets.serve(ws_handler, WS_HOST, WS_PORT)
    server = loop.run_until_complete(ws_server)
    print(f"🚀 Camera WebSocket server listening on ws://{WS_HOST}:{WS_PORT}")

    try:
        # Start broadcaster task
        broadcaster_task = loop.create_task(_broadcaster(_broadcast_queue))

        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down WebSocket server...")
    finally:
        _stop_event.set()
        broadcaster_task.cancel()
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.run_until_complete(asyncio.sleep(0.1))


if __name__ == '__main__':
    start_server()
