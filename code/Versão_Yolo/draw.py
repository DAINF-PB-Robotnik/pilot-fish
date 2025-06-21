# draw.py

import cv2
import numpy as np
from config import (
    GRID_COLOR, TEXT_COLOR, FPS_COLOR, BOX_COLOR,
    FONT_SCALE, THICKNESS, QUADRANT_LABELS,
    CAMERA_RESOLUTION
)

class Draw:
    def __init__(self):
        self.grid_color = GRID_COLOR
        self.text_color = TEXT_COLOR
        self.fps_color  = FPS_COLOR
        self.box_color  = BOX_COLOR
        self.font       = cv2.FONT_HERSHEY_SIMPLEX
        self.scale      = FONT_SCALE
        self.thk        = THICKNESS
        self.labels     = QUADRANT_LABELS

        # Precompute grid lines for resolution
        w, h = CAMERA_RESOLUTION
        self.w = w
        self.h = h
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

    def render(self, frame: np.ndarray, center: tuple, bbox: tuple, fps: float):
        output = frame.copy()

        # 1) Draw grid
        for pt1, pt2 in self._grid_lines:
            cv2.line(output, pt1, pt2, self.grid_color, 2)

        # 2) Draw quadrant labels
        for text, org in self._labels:
            cv2.putText(output, text, org, self.font, self.scale, self.text_color, self.thk, cv2.LINE_AA)

        # 3) Draw bounding box if exists
        if bbox is not None:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(output, (x1, y1), (x2, y2), self.box_color, 2)

        # 4) Draw center point if exists
        if center is not None:
            x, y = center
            cv2.circle(output, (x, y), 6, (0, 0, 255), -1)  # Red dot at center

            # Draw fish coordinates
            coord_text = f"X: {x}  Y: {y}"
            cv2.putText(
                output,
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
        org = (self.w - tw - 10, self.h - 10)
        cv2.putText(output, fps_text, org, self.font, self.scale, self.fps_color, self.thk, cv2.LINE_AA)

        return output
