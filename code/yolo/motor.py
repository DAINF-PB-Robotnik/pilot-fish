import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class Motor:
    def __init__(self, p1: int, p2: int):
        for p in (p1, p2):
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.LOW)
        self._p1, self._p2 = p1, p2

    def forward(self):
        GPIO.output(self._p1, GPIO.HIGH)
        GPIO.output(self._p2, GPIO.LOW)

    def back(self):
        GPIO.output(self._p1, GPIO.LOW)
        GPIO.output(self._p2, GPIO.HIGH)

    def brake(self):
        GPIO.output(self._p1, GPIO.HIGH)
        GPIO.output(self._p2, GPIO.HIGH)

    def stop(self):
        GPIO.output(self._p1, GPIO.LOW)
        GPIO.output(self._p2, GPIO.LOW)