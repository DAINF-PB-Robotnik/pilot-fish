import logging
import cv2
import RPi.GPIO as GPIO
import torch
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules.conv import Conv
from ultralytics.nn.modules.block import C2f, Bottleneck, SPPF
from ultralytics.nn.modules.conv import Concat
from ultralytics.nn.modules.head import Detect
from ultralytics.nn.modules.block import DFL
from torch.nn import (
    Sequential, ModuleList, ModuleDict,
    Conv2d, BatchNorm2d, SiLU,
    MaxPool2d, Upsample, AdaptiveAvgPool2d,
    Sigmoid, Hardswish, Dropout
)
from torch.serialization import add_safe_globals

add_safe_globals([
    DetectionModel, Sequential, ModuleList, ModuleDict,
    Conv, C2f, Bottleneck, SPPF,
    Conv2d, BatchNorm2d, SiLU,
    MaxPool2d, Upsample, AdaptiveAvgPool2d,
    Sigmoid, Hardswish, Dropout, Concat, Detect,
    DFL
])

from picamera2 import Picamera2

from config    import setup_logging, CAMERA_FORMAT, CAMERA_RESOLUTION, CAMERA_FRAMERATE
from yolov8n     import Yolov8n
from draw      import Draw
from control   import Control
from direction import Direction

class Main:
    def __init__(self):
        setup_logging()
        logging.info("Initialization successful.")

        self.yolov8n    = Yolov8n()
        self.control = Control(self.yolov8n)
        self.drawer     = Draw()

        # Configure & start camera entirely from config
        self.camera = Picamera2()
        self.camera.configure(
            self.camera.create_preview_configuration(
                main     = {"format": CAMERA_FORMAT, "size": CAMERA_RESOLUTION},
                controls = {"FrameRate": CAMERA_FRAMERATE}
            )
        )
        self.camera.start()
        logging.info("Camera started")

    def run(self):
        while True:
            frame = self.camera.capture_array()
            
            # Remove o canal alpha se existir
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)


            # 1) FPS tracking moved into Track
            inst_fps, _ = self.yolov8n.track_fps()

            # 2) Detection + movement
            result = self.yolov8n.track_frame(frame)

            if result:
                center = result['center']
                bbox = result['bbox']
            #contour, mask = self.yolov8n.track_frame(frame)
            self.control.move(frame, center)

            # 3) Draw overlays (instantaneous FPS only)
            #out, bin_mask = self.drawer.render(frame, center, inst_fps)
            out = self.drawer.render(frame, center, bbox, inst_fps)

            # 4) Display
            #cv2.imshow("BINARY", bin_mask)
            cv2.imshow("MAIN",   out)
            if cv2.waitKey(1) != -1:
                break

        self.camera.stop()
        cv2.destroyAllWindows()
        GPIO.cleanup()

if __name__ == "__main__":
    Main().run()
