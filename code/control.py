# control.py

import time
import logging
from sensor    import Sensor
from track     import Track
from direction import Direction
from config    import (
    PROXIMITY_LIMIT,
    SENSOR_INTERVAL,
    rotate_index,
    SENSOR_MAP,
    SENSOR_LABELS,
    BRAITENBERG_BASE,
    BRAITENBERG_WEIGHTS_LEFT,
    BRAITENBERG_WEIGHTS_RIGHT
)

class Control:
    """
    Controller:
      1) global stop if ALL directions blocked,
      2) avoid obstacle by picking the clearest sensor direction,
      3) Braitenberg in fish direction if blocked,
      4) fish-follow grid otherwise.
    """
    def __init__(self):
        self.sensor     = Sensor()
        self.limit      = PROXIMITY_LIMIT
        self.interval   = SENSOR_INTERVAL
        self._last_time = 0.0
        self._last_act  = None

    def move(self, frame, contour):
        # 1) Read & log sensors periodically
        now = time.time()
        if now - self._last_time >= self.interval:
            dists = self.sensor.get()
            logging.info(" | ".join(f"{lab}={d:.1f}cm" for lab, d in zip(SENSOR_LABELS, dists)))
            self._last_time = now
        else:
            dists = self.sensor.get()

        # 2) Global stop if every sensor < limit
        if all(d < self.limit for d in dists):
            Direction.stop()
            return self._act("All directions blocked, stopping")

        # 3) No fish contour? stop.
        if contour is None:
            Direction.stop()
            return self._act("No contour detected")

        # 4) Fish centroid
        x, y = Track.contour_center(contour)
        if x is None or y is None:
            Direction.stop()
            return self._act("Centroid calculation failed")

        # 5) Grid cell on rotated frame, then undo camera rotation
        h, w    = frame.shape[:2]
        raw_row = min(2, int(y / (h/3)))
        raw_col = min(2, int(x / (w/3)))
        row, col = rotate_index(raw_row, raw_col)

        # 6) If fish direction blocked → pick best escape
        primary_idx = SENSOR_MAP[row][col]
        if primary_idx is not None and dists[primary_idx] < self.limit:
            # find all clear sensors
            clear = [(i, d) for i, d in enumerate(dists) if d >= self.limit]
            if clear:
                # choose the clearest
                best_idx, _ = max(clear, key=lambda x: x[1])
                # map back to grid cell
                inv = {v:(r,c) for r, rowm in enumerate(SENSOR_MAP) for c, v in enumerate(rowm) if v is not None}
                br, bc = inv[best_idx]
                # command that cell
                ACTIONS = {
                    (0,0):Direction.up_left,   (0,1):Direction.forward,  (0,2):Direction.up_right,
                    (1,0):Direction.left,      (1,1):Direction.stop,     (1,2):Direction.right,
                    (2,0):Direction.down_left, (2,1):Direction.back,     (2,2):Direction.down_right,
                }
                ACTIONS[(br,bc)]()
                return self._act(f"Avoid via {(br,bc)}")
            else:
                Direction.stop()
                return self._act("All directions blocked, stopping")

        # 7) Otherwise, fish-follow grid
        ACTIONS = {
            (0,0):Direction.up_left,   (0,1):Direction.forward,  (0,2):Direction.up_right,
            (1,0):Direction.left,      (1,1):Direction.stop,     (1,2):Direction.right,
            (2,0):Direction.down_left, (2,1):Direction.back,     (2,2):Direction.down_right,
        }
        ACTIONS.get((row,col), Direction.stop)()
        return self._act(f"Fish move {(row,col)}")

    def _act(self, message):
        """Log only when the message changes."""
        if message != self._last_act:
            logging.info(message)
            self._last_act = message
