import RPi.GPIO as GPIO

class Pwm:
    def __init__(self, pin: int):
        GPIO.setup(pin, GPIO.OUT)
        self._pwm = GPIO.PWM(pin, 100)
        self._pwm.start(0)

    def set(self, duty: float):
        self._pwm.ChangeDutyCycle(duty)

    def stop(self):
        self._pwm.ChangeDutyCycle(0)
        self._pwm.stop()