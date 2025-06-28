import logging
from motor import Motor
from pwm   import Pwm
from config import MOTOR_LEFT_PINS, MOTOR_RIGHT_PINS, PWM_PINS

# instantiate once
_left_motor  = Motor(*MOTOR_LEFT_PINS)
_right_motor = Motor(*MOTOR_RIGHT_PINS)
_left_pwm    = Pwm(PWM_PINS[0])
_right_pwm   = Pwm(PWM_PINS[1])

class Direction:
    @staticmethod
    def forward(speed: int = 100):
        logging.info("Forward")
        _left_motor.forward();  _right_motor.forward()
        _left_pwm.set(speed);   _right_pwm.set(speed)

    @staticmethod
    def back(speed: int = 100):
        logging.info("Back")
        _left_motor.back();     _right_motor.back()
        _left_pwm.set(speed);   _right_pwm.set(speed)

    @staticmethod
    def left(speed: int = 100):
        logging.info("Left")
        _left_motor.back();     _right_motor.forward()
        _left_pwm.set(speed);   _right_pwm.set(speed)

    @staticmethod
    def right(speed: int = 100):
        logging.info("Right")
        _left_motor.forward();  _right_motor.back()
        _left_pwm.set(speed);   _right_pwm.set(speed)

    @staticmethod
    def stop():
        logging.info("Stop")
        _left_motor.stop();     _right_motor.stop()
        _left_pwm.set(0);       _right_pwm.set(0)

    @staticmethod
    def up_left(speed: int = 100):
        logging.info("Up-Left")
        # direct diagonal: both forward, left wheel half speed
        _left_motor.forward();  _right_motor.forward()
        _left_pwm.set(speed//2);_right_pwm.set(speed)

    @staticmethod
    def up_right(speed: int = 100):
        logging.info("Up-Right")
        # both forward, right wheel half speed
        _left_motor.forward();  _right_motor.forward()
        _left_pwm.set(speed);   _right_pwm.set(speed//2)

    @staticmethod
    def down_left(speed: int = 100):
        logging.info("Down-Left")
        # both back, left wheel half speed
        _left_motor.back();     _right_motor.back()
        _left_pwm.set(speed//2);_right_pwm.set(speed)

    @staticmethod
    def down_right(speed: int = 100):
        logging.info("Down-Right")
        # both back, right wheel half speed
        _left_motor.back();     _right_motor.back()
        _left_pwm.set(speed);   _right_pwm.set(speed//2)