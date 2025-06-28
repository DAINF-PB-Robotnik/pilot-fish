import RPi.GPIO as GPIO
import time
import logging
from config import SENSOR_FRONT_PINS, SENSOR_REAR_PINS, SENSOR_TIMEOUT_S

class Sensor:
    def __init__(self):
        front_trig, front_echo = SENSOR_FRONT_PINS
        rear_trig, rear_echo   = SENSOR_REAR_PINS

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(front_trig, GPIO.OUT)
        GPIO.setup(front_echo, GPIO.IN)
        GPIO.setup(rear_trig, GPIO.OUT)
        GPIO.setup(rear_echo, GPIO.IN)
        GPIO.output(front_trig, False)
        GPIO.output(rear_trig,  False)
        time.sleep(2)

        self.front_trig = front_trig
        self.front_echo = front_echo
        self.rear_trig  = rear_trig
        self.rear_echo  = rear_echo

    def _measure(self, trig, echo):
        GPIO.output(trig, True)
        time.sleep(1e-5)
        GPIO.output(trig, False)

        start = time.time()
        while GPIO.input(echo) == 0:
            if time.time() - start > SENSOR_TIMEOUT_S:
                logging.warning("Sensor timeout")
                return None
        t0 = time.time()
        while GPIO.input(echo) == 1:
            if time.time() - t0 > SENSOR_TIMEOUT_S:
                logging.warning("Sensor timeout")
                return None
        t1 = time.time()
        return (t1 - t0) * 17150  # cm

    def front(self):
        return self._measure(self.front_trig, self.front_echo)

    def rear(self):
        return self._measure(self.rear_trig, self.rear_echo)