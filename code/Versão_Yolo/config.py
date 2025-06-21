# config.py (excerpt)

import yaml, logging
from pathlib import Path
from colorama import Fore, Style, init as colorama_init

# initialize colorama (Windows support + autoreset)
colorama_init(autoreset=True)

_data = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())

class LastRecordFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self._last = None
    def filter(self, record):
        curr = (record.msg, record.args)
        if curr != self._last:
            self._last = curr
            return True
        return False

class ColorFormatter(logging.Formatter):
    """Add colors to level names and messages."""
    LEVEL_COLORS = {
        logging.DEBUG:    Fore.CYAN,
        logging.INFO:     Fore.GREEN,
        logging.WARNING:  Fore.YELLOW,
        logging.ERROR:    Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }
    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, "")
        # decorate levelname
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        # decorate message
        record.msg = f"{color}{record.getMessage()}{Style.RESET_ALL}"
        # clear args so super().format() doesn't re-interpolate
        record.args = ()
        return super().format(record)

def setup_logging():
    level = getattr(logging, _data["logging"]["level"].upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%H:%M:%S"
    handler.setFormatter(ColorFormatter(fmt, datefmt=datefmt))
    handler.addFilter(LastRecordFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


# Motor pins
MOTOR_LEFT_PINS   = tuple(_data["motor"]["left_pins"])
MOTOR_RIGHT_PINS  = tuple(_data["motor"]["right_pins"])
PWM_PINS          = tuple(_data["motor"]["pwm_pins"])

# Sensor settings
SENSOR_FRONT_PINS    = tuple(_data["sensor"]["front_pins"])
SENSOR_REAR_PINS     = tuple(_data["sensor"]["rear_pins"])
SENSOR_TIMEOUT_S     = float(_data["sensor"]["timeout_s"])
SENSOR_POLL_INTERVAL = float(_data["sensor"]["poll_interval_s"])

# Tracker (HSV)
HSV_LOWER    = tuple(_data["tracker"]["hsv_lower"])
HSV_UPPER    = tuple(_data["tracker"]["hsv_upper"])
KERNEL_SIZE  = tuple(_data["tracker"]["kernel_size"])

# Draw styles
BOX_COLOR       = (0, 255, 0) 
GRID_COLOR      = tuple(_data["draw"]["grid_color"])
TEXT_COLOR      = tuple(_data["draw"]["text_color"])
FPS_COLOR       = tuple(_data["draw"]["fps_color"])
FONT_SCALE      = float(_data["draw"]["font_scale"])
THICKNESS       = int(_data["draw"]["thickness"])
QUADRANT_LABELS = _data["draw"]["quadrant_labels"]

# Control
PROXIMITY_LIMIT      = float(_data["control"]["proximity_limit_cm"])

# Camera
CAMERA_FORMAT    = _data["camera"]["format"]
CAMERA_RESOLUTION = tuple(_data["camera"]["resolution"])
CAMERA_FRAMERATE  = float(_data["camera"]["framerate"])
