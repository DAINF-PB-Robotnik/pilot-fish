# direction.py

import time
import logging
from motor import Motor
from pwm   import Pwm
from config import PWM_PINS, MOTOR_LEFT_PINS, MOTOR_RIGHT_PINS

# Motor instances
_left_motor  = Motor(*MOTOR_LEFT_PINS)
_right_motor = Motor(*MOTOR_RIGHT_PINS)
_left_pwm    = Pwm(PWM_PINS[0])
_right_pwm   = Pwm(PWM_PINS[1])

class Direction:
    """
    Motor control with internal ramping to smooth transitions.
    """
    # Last commanded speeds for ramping
    _last_left = 0.0
    _last_right = 0.0
    _last_time = time.time()
    MAX_ACCEL = 100.0  # PWM units per second

    @classmethod
    def _ramp(cls, target_left: float, target_right: float):
        now = time.time()
        dt = now - cls._last_time
        cls._last_time = now

        max_delta = cls.MAX_ACCEL * dt

        # compute delta for left motor
        delta_l = target_left - cls._last_left
        if abs(delta_l) > max_delta:
            delta_l = max_delta if delta_l > 0 else -max_delta
        new_l = cls._last_left + delta_l

        # compute delta for right motor
        delta_r = target_right - cls._last_right
        if abs(delta_r) > max_delta:
            delta_r = max_delta if delta_r > 0 else -max_delta
        new_r = cls._last_right + delta_r

        # apply directions based on sign
        if new_l >= 0:
            _left_motor.forward()
        else:
            _left_motor.back()
        if new_r >= 0:
            _right_motor.forward()
        else:
            _right_motor.back()

        # set PWM duty cycles (abs, clamped)
        _left_pwm.set(min(abs(new_l), 100))
        _right_pwm.set(min(abs(new_r), 100))

        # save for next ramp
        cls._last_left = new_l
        cls._last_right = new_r

    @staticmethod
    def forward(speed: float = 100.0):
        logging.info("Forward")
        Direction._ramp(speed, speed)

    @staticmethod
    def back(speed: float = 100.0):
        logging.info("Back")
        Direction._ramp(-speed, -speed)

    @staticmethod
    def left(speed: float = 100.0):
        logging.info("Left")
        Direction._ramp(-speed, speed)

    @staticmethod
    def right(speed: float = 100.0):
        logging.info("Right")
        Direction._ramp(speed, -speed)

    @staticmethod
    def stop():
        logging.info("Stop")
        Direction._ramp(0.0, 0.0)

    @staticmethod
    def up_left(speed: float = 100.0):
        logging.info("Up-Left")
        Direction._ramp(speed/2, speed)

    @staticmethod
    def up_right(speed: float = 100.0):
        logging.info("Up-Right")
        Direction._ramp(speed, speed/2)

    @staticmethod
    def down_left(speed: float = 100.0):
        logging.info("Down-Left")
        Direction._ramp(-speed/2, -speed)

    @staticmethod
    def down_right(speed: float = 100.0):
        logging.info("Down-Right")
        Direction._ramp(-speed, -speed/2)
