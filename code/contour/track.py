import time
import cv2
import numpy as np
import logging
from collections import deque
from statistics     import median
from config import HSV_LOWER, HSV_UPPER, KERNEL_SIZE

class Track:
    def __init__(self,
                 min_contour_area: float = 100.0,
                 roi_margin: int        = 20,
                 fps_window_s: float    = 10.0):
        # HSV / morphology
        self.lower      = HSV_LOWER
        self.upper      = HSV_UPPER
        self.kernel     = cv2.getStructuringElement(cv2.MORPH_CROSS, KERNEL_SIZE)
        self.min_area   = min_contour_area
        self.roi_margin = roi_margin
        self.prev_bbox  = None

        # FPS tracking
        self.prev_time       = time.time()
        self.fps_history     = deque()
        self.fps_window_s    = fps_window_s
        self.last_median_log = self.prev_time

    @staticmethod
    def contour_center(cnt: np.ndarray):
        M = cv2.moments(cnt)
        if M["m00"]:
            return int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
        return None, None

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        """One‐call BGR→HSV→mask→close pipeline."""
        hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)

    def _find_valid(self, mask: np.ndarray):
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in cnts if cv2.contourArea(c) >= self.min_area]

    def track_frame(self, frame: np.ndarray):
        """
        Detection pipeline with ROI‐fallback and area‐filter.
        Returns (contour_or_None, full_frame_mask).
        """
        h, w = frame.shape[:2]
        roi_bounds = None

        # 1) ROI
        if self.prev_bbox:
            x,y,bw,bh = self.prev_bbox
            x0 = max(x - self.roi_margin, 0)
            y0 = max(y - self.roi_margin, 0)
            x1 = min(x + bw + self.roi_margin, w)
            y1 = min(y + bh + self.roi_margin, h)
            roi = frame[y0:y1, x0:x1]
            roi_bounds = (x0, y0)
        else:
            roi = frame

        # 2) Preprocess + find in ROI
        mask_roi = self._preprocess(roi)
        cnts     = self._find_valid(mask_roi)

        # 3) Fallback to full frame
        use_full = False
        if not cnts:
            mask_full = self._preprocess(frame)
            cnts      = self._find_valid(mask_full)
            use_full  = True
        else:
            mask_full = self._preprocess(frame)

        # 4) Select largest
        main = max(cnts, key=cv2.contourArea) if cnts else None

        # 5) Update bounding box
        if main is not None:
            if roi_bounds and not use_full:
                x0,y0 = roi_bounds
                main = main + np.array([[x0,y0]])
            x2,y2,w2,h2 = cv2.boundingRect(main)
            self.prev_bbox = (x2,y2,w2,h2)
        else:
            self.prev_bbox = None

        return main, mask_full

    def track_fps(self):
        """
        Call once per frame. Returns (instant_fps, median_fps_or_None),
        logging median only every fps_window_s seconds.
        """
        now = time.time()
        # instantaneous
        inst = 1.0/(now - self.prev_time) if now>self.prev_time else 0.0
        self.prev_time = now

        # history
        self.fps_history.append((now, inst))
        while self.fps_history and now - self.fps_history[0][0] > self.fps_window_s:
            self.fps_history.popleft()

        # median every window
        med = None
        if now - self.last_median_log >= self.fps_window_s:
            vals = [f for (_,f) in self.fps_history]
            if vals:
                med = median(vals)
                logging.info(f"Median FPS (last {self.fps_window_s}s): {med:.1f}")
            self.last_median_log = now

        return inst, med
