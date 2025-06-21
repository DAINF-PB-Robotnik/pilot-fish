import cv2
import time
import logging
from ultralytics import YOLO
from statistics import median
from collections import deque

class Yolov8n:
    def __init__(self, model_path='/home/user/Pilot_Fish/Versão_Yolo/best.pt', fps_window_s=10.0):
        self.model = YOLO(model_path)
        self.prev_time = time.time()
        self.fps_history = deque()
        self.fps_window_s = fps_window_s
        self.last_median_log = self.prev_time
        self.last_detection = None
        
    def track_frame(self, frame):
        results = self.model(frame)

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                self.last_detection = {
                    'class': cls,
                    'confidence': conf,
                    'bbox': (x1, y1, x2, y2),
                    'center': (cx, cy)
                }

                return self.last_detection

        self.last_detection = None
        return None

    def center(self):
        if self.last_detection:
            return self.last_detection['center']
        else:
            return None

    def track_fps(self):
        now = time.time()
        inst = 1.0 / (now - self.prev_time) if now > self.prev_time else 0.0
        self.prev_time = now

        self.fps_history.append((now, inst))
        while self.fps_history and now - self.fps_history[0][0] > self.fps_window_s:
            self.fps_history.popleft()

        med = None
        if now - self.last_median_log >= self.fps_window_s:
            vals = [f for (_, f) in self.fps_history]
            if vals:
                med = median(vals)
                logging.info(f"FPS Medio (últimos {self.fps_window_s}s): {med:.1f}")
            self.last_median_log = now

        return inst, med

