import cv2
from ultralytics import YOLO

class CameraML:
    def __init__(self, model_path="yolov8n.pt", source=0):
        self.cap = cv2.VideoCapture(source)
        self.model = YOLO(model_path)
        self.last_result = None

    def read_frame(self):
        ret, frame = self.cap.read()
        if ret:
            results = self.model(frame)
            self.last_result = results
            return frame, results
        return None, None
