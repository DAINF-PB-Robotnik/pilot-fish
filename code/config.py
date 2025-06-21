# config.py

import yaml
import logging
from pathlib import Path
from colorama import Fore, Style, init as colorama_init

# initialize colorama
colorama_init(autoreset=True)

# load config.yaml
_data = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())

# --- Logging helpers (unchanged) ---
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
    LEVEL_COLORS = {
        logging.DEBUG:    Fore.CYAN,
        logging.INFO:     Fore.GREEN,
        logging.WARNING:  Fore.YELLOW,
        logging.ERROR:    Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }
    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        record.msg       = f"{color}{record.getMessage()}{Style.RESET_ALL}"
        record.args      = ()
        return super().format(record)

def setup_logging():
    level   = getattr(logging, _data["logging"]["level"].upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    fmt     = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%H:%M:%S"
    handler.setFormatter(ColorFormatter(fmt, datefmt=datefmt))
    handler.addFilter(LastRecordFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

# --- Motor pins ---
MOTOR_LEFT_PINS   = tuple(_data["motor"]["left_pins"])
MOTOR_RIGHT_PINS  = tuple(_data["motor"]["right_pins"])
PWM_PINS          = tuple(_data["motor"]["pwm_pins"])

# --- Tracker ---
HSV_LOWER   = tuple(_data["tracker"]["hsv_lower"])
HSV_UPPER   = tuple(_data["tracker"]["hsv_upper"])
KERNEL_SIZE = tuple(_data["tracker"]["kernel_size"])

# --- Draw ---
GRID_COLOR      = tuple(_data["draw"]["grid_color"])
TEXT_COLOR      = tuple(_data["draw"]["text_color"])
FPS_COLOR       = tuple(_data["draw"]["fps_color"])
FONT_SCALE      = float(_data["draw"]["font_scale"])
THICKNESS       = int(_data["draw"]["thickness"])
QUADRANT_LABELS = _data["draw"]["quadrant_labels"]

# --- Control ---
PROXIMITY_LIMIT = float(_data["control"]["proximity_limit_cm"])

# --- Camera ---
CAMERA_FORMAT     = _data["camera"]["format"]
CAMERA_RESOLUTION = tuple(_data["camera"]["resolution"])
CAMERA_FRAMERATE  = float(_data["camera"]["framerate"])
CAMERA_ROTATION   = int(_data["camera"]["rotation"]) % 360

def rotate_index(r: int, c: int) -> (int, int):
    """Rotate a 3×3 index by CAMERA_ROTATION degrees."""
    if CAMERA_ROTATION == 90:
        return c, 2 - r
    if CAMERA_ROTATION == 180:
        return 2 - r, 2 - c
    if CAMERA_ROTATION == 270:
        return 2 - c, r
    return r, c

def rotate_labels(labels):
    """Rotate 3×3 label matrix to compensate camera rotation."""
    out = [[None]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            ri, rj = rotate_index(i, j)
            out[i][j] = labels[ri][rj]
    return out

# --- Serial sensor ---
SERIAL_PORT       = _data["serial"]["port"]
SERIAL_BAUDRATE   = int(_data["serial"]["baudrate"])
SERIAL_TIMEOUT_S  = float(_data["serial"]["timeout_s"])

# --- Polling ---
SENSOR_NUM        = int(_data["sensor_read"]["num_sensors"])
SENSOR_INTERVAL   = float(_data["sensor_read"]["interval_s"])
SENSOR_LABELS     = tuple(_data["sensor_read"]["labels"])

# --- Grid→sensor map ---
SENSOR_MAP = [
    [None if v is None else int(v) for v in row]
    for row in _data["sensor_map"]
]

# --- Braitenberg ---
BRAITENBERG_BASE         = float(_data["braitenberg"]["base_speed"])
BRAITENBERG_WEIGHTS_LEFT = tuple(_data["braitenberg"]["weights_left"])
BRAITENBERG_WEIGHTS_RIGHT= tuple(_data["braitenberg"]["weights_right"])
