# draw.py

import cv2
import numpy as np
from track import Track
from config import (
    GRID_COLOR, TEXT_COLOR, FPS_COLOR,
    FONT_SCALE, THICKNESS, QUADRANT_LABELS,
    CAMERA_RESOLUTION, rotate_labels
)

class Draw:
    def __init__(self):
        self.grid_color = GRID_COLOR
        self.text_color = TEXT_COLOR
        self.fps_color  = FPS_COLOR
        self.font       = cv2.FONT_HERSHEY_SIMPLEX
        self.scale      = FONT_SCALE
        self.thk        = THICKNESS
        self.labels     = rotate_labels(QUADRANT_LABELS)

        # Precompute grid lines for resolution
        w, h = CAMERA_RESOLUTION
        thirds = (w//3, h//3)
        self._grid_lines = []
        for i in (1, 2):
            # horizontal
            y = i * h // 3
            self._grid_lines.append(((0, y), (w, y)))
            # vertical
            x = i * w // 3
            self._grid_lines.append(((x, 0), (x, h)))

        # Precompute label positions and text sizes
        self._labels = []
        for i, row in enumerate(self.labels):
            for j, text in enumerate(row):
                cx = int((j + 0.5) * w / 3)
                cy = int((i + 0.5) * h / 3)
                (tw, th), _ = cv2.getTextSize(text, self.font, self.scale, self.thk)
                org = (cx - tw//2, cy + th//2)
                self._labels.append((text, org))

        # Fixed origin for fish‐coordinates display
        self._coord_origin = (10, 30)

    def render(self, frame: np.ndarray, contour: np.ndarray, mask: np.ndarray, fps: float):
        # 1) Draw grid
        for pt1, pt2 in self._grid_lines:
            cv2.line(frame, pt1, pt2, self.grid_color, 2)

        # 2) Draw quadrant labels
        for text, org in self._labels:
            cv2.putText(frame, text, org, self.font, self.scale, self.text_color, self.thk, cv2.LINE_AA)

        # 3) Draw contour & centroid
        if contour is not None:
            hull = cv2.convexHull(contour)
            cv2.drawContours(frame, [hull], -1, self.grid_color, 1)

            x, y = Track.contour_center(contour)
            if x is not None and y is not None:
                cv2.circle(frame, (x, y), 5, (0,0,255), -1)
                # 4) Draw fish coordinates
                coord_text = f"X:{x}  Y:{y}"
                cv2.putText(
                    frame,
                    coord_text,
                    self._coord_origin,
                    self.font,
                    self.scale,
                    self.text_color,
                    self.thk,
                    cv2.LINE_AA
                )

        # 5) Draw FPS (bottom‐right)
        fps_text = f"FPS: {fps:.1f}"
        (tw, th), _ = cv2.getTextSize(fps_text, self.font, self.scale, self.thk)
        h, w = frame.shape[:2]
        org = (w - tw - 10, h - 10)
        cv2.putText(frame, fps_text, org, self.font, self.scale, self.fps_color, self.thk, cv2.LINE_AA)

        return frame, mask
