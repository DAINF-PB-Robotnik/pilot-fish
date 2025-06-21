
# control.py

import time
import logging
from sensor    import Sensor
from yolov8n     import Yolov8n
from direction import Direction
from config    import PROXIMITY_LIMIT, SENSOR_POLL_INTERVAL

class Control:
    def __init__(self, yolov8n):
        self.sensor         = Sensor()
        self.limit          = PROXIMITY_LIMIT
        self.interval       = SENSOR_POLL_INTERVAL
        self.last_time      = 0
        self.dist_front     = float("inf")
        self.dist_rear      = float("inf")
        self.last_action    = None
        self.double_stopped = False
        self.yolov8n        = yolov8n

        self.quad_names = [
            ["Up-Left",   "Up",      "Up-Right"],
            ["Left",      "Center",  "Right"],
            ["Down-Left", "Down",    "Down-Right"],
        ]

    def move(self, frame, contour):
        h, w = frame.shape[:2]
        x1, x2 = w//3, 2*w//3
        y1, y2 = h//3, 2*h//3

        # 1) Atualiza sensores 1×/s
        now = time.time()
        if now - self.last_time >= self.interval:
            f = self.sensor.front()
            r = self.sensor.rear()
            if f is not None: self.dist_front = f
            else:             logging.warning("Front sensor failed")
            if r is not None: self.dist_rear  = r
            else:             logging.warning("Rear sensor failed")

            # log sensores + quadrante
            quad = ""
            if contour is not None:
                xq, yq = self.yolov8n.center();
                if xq is not None:
                    row = 0 if yq < y1 else 1 if yq < y2 else 2
                    col = 0 if xq < x1 else 1 if xq < x2 else 2
                    quad = self.quad_names[row][col]
            logging.info(f"Sensor F:{self.dist_front:.1f}cm R:{self.dist_rear:.1f}cm | Fish:{quad}")
            self.last_time = now

        obst_f = self.dist_front < self.limit
        obst_r = self.dist_rear  < self.limit

        action = None
        cmd    = None

        # 2) Decisão de movimento
        if contour is None:
            action, cmd = ("warning","No contour"), Direction.stop
        else:
            x, y = self.yolov8n.center()
            if x is None:
                action, cmd = ("warning","Center failed"), Direction.stop
            else:
                row = 0 if y < y1 else 1 if y < y2 else 2
                col = 0 if x < x1 else 1 if x < x2 else 2

                # override lateral
                if row == 1 and col == 0:
                    action, cmd = ("info","Move Left"), Direction.left
                    self.double_stopped = False
                elif row == 1 and col == 2:
                    action, cmd = ("info","Move Right"), Direction.right
                    self.double_stopped = False

                else:
                    # ambos bloqueados
                    if obst_f and obst_r:
                        if not self.double_stopped:
                            action, cmd = ("warning","Stop"), Direction.stop
                            self.double_stopped = True
                        else:
                            action, cmd = ("info","Stopped"), Direction.stop

                    # só frontal bloqueado — agora trata diagonais corretamente
                    elif obst_f:
                        if row == 2:
                            if col == 0:
                                action, cmd = ("info","Move Down-Left"),  Direction.down_left
                            elif col == 1:
                                action, cmd = ("info","Move Back"),       Direction.back
                            else:  # col == 2
                                action, cmd = ("info","Move Down-Right"), Direction.down_right
                        else:
                            action, cmd = ("info","Stopped"), Direction.stop

                    # só traseiro bloqueado
                    elif obst_r:
                        if row == 0:
                            if col == 0:
                                action, cmd = ("info","Move Up-Left"),  Direction.up_left
                            elif col == 1:
                                action, cmd = ("info","Move Up"),        Direction.forward
                            else:
                                action, cmd = ("info","Move Up-Right"), Direction.up_right
                        else:
                            action, cmd = ("info","Stopped"), Direction.stop

                    # livre
                    else:
                        mapping = {
                            (0,0):("info","Move Up-Left",   Direction.up_left),
                            (0,1):("info","Move Up",        Direction.forward),
                            (0,2):("info","Move Up-Right",  Direction.up_right),
                            (1,0):("info","Move Left",      Direction.left),
                            (1,1):("info","Stopped",        Direction.stop),
                            (1,2):("info","Move Right",     Direction.right),
                            (2,0):("info","Move Down-Left", Direction.down_left),
                            (2,1):("info","Move Down",      Direction.back),
                            (2,2):("info","Move Down-Right",Direction.down_right),
                        }
                        lvl, txt, fn = mapping.get((row,col),(None,None,None))
                        if lvl:
                            action, cmd = (lvl, txt), fn

        # 3) Log on change
        if action and action[1] != self.last_action:
            getattr(logging, action[0])(action[1])
            self.last_action = action[1]

        # 4) Execute
        if cmd:
            cmd()
