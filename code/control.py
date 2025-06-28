# control.py

import time
import logging

from sensor    import Sensor
from track     import Track
from direction import Direction
from config    import (
    PROXIMITY_LIMIT,
    SENSOR_NUM,
    SENSOR_LABELS,
    SENSOR_SMOOTHING_ALPHA,
    CENTROID_SMOOTHING_ALPHA,
    CRITICAL_DISTANCE,
    STATE_DEBOUNCE_INTERVAL,
    CLEAR_THRESHOLD,
    BASE_SENSOR_INTERVAL,
    MIN_SENSOR_INTERVAL,
    AVOID_MIN_TIME,
    rotate_index,
    SENSOR_MAP,
)

class Control:
    """
    - 3-sensor groups per heading (CRITICAL_GUARDS).
    - Dynamic read interval ∈ [MIN, BASE], but MIN when in AVOID.
    - Follow-speed ∈ [0–100%] ∝ min(group_distance)/PROXIMITY_LIMIT.
    - Hard-stop → AVOID if any group sensor ≤ CRITICAL_DISTANCE.
    - Center cell (1,1) → only stop (no AVOID) until fish moves.
    - Remain in AVOID ≥ AVOID_MIN_TIME before FOLLOW.
    - Debounced FOLLOW⇄AVOID via STATE_DEBOUNCE_INTERVAL & CLEAR_THRESHOLD.
    - Centroid smoothing via CENTROID_SMOOTHING_ALPHA.
    """

    CRITICAL_GUARDS = {
        (0,1): [0,1,7], (1,0): [6,5,7],
        (1,2): [2,1,3], (2,1): [4,3,5],
        (0,0): [7,0,6], (0,2): [1,0,2],
        (2,0): [5,4,6], (2,2): [3,4,2],
    }
    DIAG_FALLBACKS = {
        (0,0): [(2,2),(0,1),(1,0)],
        (0,2): [(2,0),(0,1),(1,2)],
        (2,0): [(0,2),(2,1),(1,0)],
        (2,2): [(0,0),(2,1),(1,2)],
    }

    def __init__(self):
        self.sensor            = Sensor()
        self.limit             = PROXIMITY_LIMIT

        # sensor‐read timing
        self._read_interval    = BASE_SENSOR_INTERVAL
        self._last_read_time   = 0.0

        # logging helper
        self._last_action_msg  = None

        # smoothing buffers
        self._sensor_smoothed  = None
        self._cx, self._cy     = None, None

        # Finite State Machine
        self.state             = 'FOLLOW'
        self._state_time       = 0.0
        self._clear_count      = 0

    def move(self, frame, contour):
        now = time.time()

        # 1) Fish detection → raw heading cell
        if contour is None:
            self._enter_avoid(now)
            Direction.stop()
            return self._log("[BRAITE] No contour")

        x, y = Track.contour_center(contour)
        if x is None or y is None:
            self._enter_avoid(now)
            Direction.stop()
            return self._log("[BRAITE] Centroid failed")

        h, w     = frame.shape[:2]
        raw_r    = max(0, min(2, int(y / (h/3))))
        raw_c    = max(0, min(2, int(x / (w/3))))
        raw_cell = rotate_index(raw_r, raw_c)

        # 1a) Center-cell override: stop only
        if raw_cell == (1,1):
            Direction.stop()
            return self._log("[FISH] Center stop")

        # 2) Compute ratio from heading group
        idxs      = Control.CRITICAL_GUARDS.get(raw_cell, [])
        dists     = self._sensor_smoothed or [self.limit]*SENSOR_NUM
        group_min = min(dists[i] for i in idxs) if idxs else self.limit
        ratio     = max(0.0, min(1.0, group_min / self.limit))

        # 2a) Override interval when in AVOID
        if self.state == 'AVOID':
            self._read_interval = MIN_SENSOR_INTERVAL
        else:
            self._read_interval = max(
                MIN_SENSOR_INTERVAL,
                BASE_SENSOR_INTERVAL * ratio
            )

        # 3) Read & smooth sensors when due
        if now - self._last_read_time >= self._read_interval:
            raw_vals = self.sensor.get()
            self._last_read_time = now

            if self._sensor_smoothed is None:
                # first time: Err→inf, else raw
                self._sensor_smoothed = [
                    float('inf') if d < 0 else d
                    for d in raw_vals
                ]
            else:
                αs = SENSOR_SMOOTHING_ALPHA
                for i, d in enumerate(raw_vals):
                    if d < 0:
                        # keep previous value
                        continue
                    prev = self._sensor_smoothed[i]
                    if prev == float('inf'):
                        # first valid after inf → instant replace
                        self._sensor_smoothed[i] = d
                    else:
                        # normal exponential smoothing
                        self._sensor_smoothed[i] = prev*αs + d*(1-αs)

            logging.info(" | ".join(
                f"{lab}={dist:.1f}cm"
                for lab, dist in zip(SENSOR_LABELS, self._sensor_smoothed)
            ))

        dists = self._sensor_smoothed or [float('inf')]*SENSOR_NUM

        # 4) Hard-stop → enter AVOID if any critical sensor ≤ CRITICAL_DISTANCE
        if any(dists[i] <= CRITICAL_DISTANCE for i in idxs):
            self._enter_avoid(now)

        # 5) Global stop if all directions blocked
        if all(d < self.limit for d in dists):
            self._enter_avoid(now)
            Direction.stop()
            return self._log("[BRAITE] All blocked")

        # 6) Debounce FOLLOW⇄AVOID + enforce minimal AVOID time
        elapsed = now - self._state_time
        primary = SENSOR_MAP[raw_cell[0]][raw_cell[1]]
        if elapsed >= STATE_DEBOUNCE_INTERVAL:
            if self.state == 'FOLLOW':
                if primary is not None and dists[primary] < self.limit:
                    self._enter_avoid(now)
            else:
                if primary is not None and dists[primary] >= self.limit:
                    self._clear_count += 1
                else:
                    self._clear_count = 0

                if (self._clear_count >= CLEAR_THRESHOLD and
                    now - self._state_time >= AVOID_MIN_TIME):
                    self.state       = 'FOLLOW'
                    self._state_time = now

        # 7) Centroid smoothing for FOLLOW movement
        αc = CENTROID_SMOOTHING_ALPHA
        if self._cx is None:
            self._cx, self._cy = x, y
        else:
            self._cx = self._cx*αc + x*(1-αc)
            self._cy = self._cy*αc + y*(1-αc)

        sm_r = max(0, min(2, int(self._cy / (h/3))))
        sm_c = max(0, min(2, int(self._cx / (w/3))))
        smooth_cell = rotate_index(sm_r, sm_c)
        follow_speed = int(ratio * 100)

        # 8) Execute movement
        ACTIONS = {
            (0,0): Direction.up_left,   (0,1): Direction.forward,  (0,2): Direction.up_right,
            (1,0): Direction.left,      (1,1): Direction.stop,     (1,2): Direction.right,
            (2,0): Direction.down_left, (2,1): Direction.back,     (2,2): Direction.down_right,
        }

        if self.state == 'AVOID':
            # diagonal fallback
            if raw_cell in Control.DIAG_FALLBACKS:
                for fb in Control.DIAG_FALLBACKS[raw_cell]:
                    idx = SENSOR_MAP[fb[0]][fb[1]]
                    if idx is not None and dists[idx] >= self.limit:
                        ACTIONS[fb]()
                        return self._log(f"[BRAITE] Avoid via {fb}")
            # generic fallback
            clear = [(i,d) for i,d in enumerate(dists) if d >= self.limit]
            if clear:
                best,_ = max(clear, key=lambda x: x[1])
                inv = {
                    v:(r,c)
                    for r,rm in enumerate(SENSOR_MAP)
                    for c,v in enumerate(rm) if v is not None
                }
                br, bc = inv[best]
                ACTIONS[(br,bc)]()
                return self._log(f"[BRAITE] Avoid via {(br,bc)}")
            Direction.stop()
            return self._log("[BRAITE] All blocked")

        # FOLLOW: use smooth_cell at scaled speed
        ACTIONS.get(smooth_cell, Direction.stop)(follow_speed)
        return self._log(f"[FISH] Move {smooth_cell} @ {follow_speed}%")

    def _enter_avoid(self, now):
        """Switch to AVOID and reset timers."""
        if self.state != 'AVOID':
            self.state        = 'AVOID'
            self._state_time  = now
            self._clear_count = 0

    def _log(self, msg):
        """Log only on action transitions."""
        if msg != self._last_action_msg:
            logging.info(msg)
            self._last_action_msg = msg
