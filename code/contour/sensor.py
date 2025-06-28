# sensor.py

import threading
import time
import logging
import serial
from config import (
    SERIAL_PORT,
    SERIAL_BAUDRATE,
    SERIAL_TIMEOUT_S,
    SENSOR_NUM,
    SENSOR_INTERVAL
)

class Sensor:
    """
    Background reader for SENSOR_NUM ultrasonic sensors
    from an Arduino Mega over USB. Sends 'R' every SENSOR_INTERVAL
    seconds, parses a line of 'x.x;y.y;Err;…', and stores floats (Err→-1.0).
    """

    def __init__(self):
        try:
            self.ser = serial.Serial(
                SERIAL_PORT,
                SERIAL_BAUDRATE,
                timeout=SERIAL_TIMEOUT_S
            )
        except serial.SerialException as e:
            logging.error(f"Cannot open serial {SERIAL_PORT}: {e}")
            raise

        time.sleep(2)  # allow Arduino reset
        self.distances = [-1.0] * SENSOR_NUM
        self._stop = threading.Event()
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self):
        while not self._stop.is_set():
            try:
                self.ser.write(b'R')
                line = self.ser.readline().decode(errors='ignore').strip()
                parts = line.split(';')
                if len(parts) == SENSOR_NUM:
                    new = []
                    for p in parts:
                        if p.lower() == 'err':
                            new.append(-1.0)
                        else:
                            try:
                                new.append(float(p))
                            except ValueError:
                                new.append(-1.0)
                    self.distances = new
                else:
                    logging.warning(f"Expected {SENSOR_NUM} values, got {len(parts)}: {line}")
            except Exception as e:
                logging.error(f"Sensor read error: {e}")
            time.sleep(SENSOR_INTERVAL)

    def get(self) -> list[float]:
        """Return the latest distances list (cm)."""
        return self.distances.copy()

    def stop(self):
        """Stop background thread and close serial port."""
        self._stop.set()
        try:
            self.ser.close()
        except:
            pass
