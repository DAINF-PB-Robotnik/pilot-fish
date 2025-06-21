#!/usr/bin/env python3
"""
motor_test.py

Test script for the two DC motors:
- both forward
- both backward
- left only (forward/back)
- right only (forward/back)
Each movement lasts 2 seconds, with a 1-second stop between tests.
"""

import time
import logging
import RPi.GPIO as GPIO

from motor import Motor
from pwm   import Pwm
from config import MOTOR_LEFT_PINS, MOTOR_RIGHT_PINS, PWM_PINS

def setup_logging():
    """Configure simple console logging."""
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S"
    )

def main():
    setup_logging()
    logging.info("Starting motor test sequence")

    # Initialize GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Instantiate motors and PWM controllers
    left_motor  = Motor(*MOTOR_LEFT_PINS)
    right_motor = Motor(*MOTOR_RIGHT_PINS)
    left_pwm    = Pwm(PWM_PINS[0])
    right_pwm   = Pwm(PWM_PINS[1])

    try:
        tests = [
            ("Both Forward",  lambda: (left_motor.forward(), right_motor.forward(),
                                      left_pwm.set(100), right_pwm.set(100))),
            ("Stop",          lambda: (left_motor.stop(),    right_motor.stop(),
                                      left_pwm.set(0),   right_pwm.set(0))),
            ("Both Backward", lambda: (left_motor.back(),    right_motor.back(),
                                      left_pwm.set(100), right_pwm.set(100))),
            ("Stop",          lambda: (left_motor.stop(),    right_motor.stop(),
                                      left_pwm.set(0),   right_pwm.set(0))),
            ("Left Forward",  lambda: (left_motor.forward(), right_motor.stop(),
                                      left_pwm.set(100), right_pwm.set(0))),
            ("Stop",          lambda: (left_motor.stop(),    right_motor.stop(),
                                      left_pwm.set(0),   right_pwm.set(0))),
            ("Left Backward", lambda: (left_motor.back(),    right_motor.stop(),
                                      left_pwm.set(100), right_pwm.set(0))),
            ("Stop",          lambda: (left_motor.stop(),    right_motor.stop(),
                                      left_pwm.set(0),   right_pwm.set(0))),
            ("Right Forward", lambda: (left_motor.stop(),    right_motor.forward(),
                                      left_pwm.set(0),   right_pwm.set(100))),
            ("Stop",          lambda: (left_motor.stop(),    right_motor.stop(),
                                      left_pwm.set(0),   right_pwm.set(0))),
            ("Right Backward",lambda: (left_motor.stop(),    right_motor.back(),
                                      left_pwm.set(0),   right_pwm.set(100))),
            ("Stop",          lambda: (left_motor.stop(),    right_motor.stop(),
                                      left_pwm.set(0),   right_pwm.set(0))),
        ]

        for name, action in tests:
            logging.info(f"Test: {name}")
            action()
            # If this is a movement, wait 2s; if it's "Stop", wait 1s
            time.sleep(2 if "Stop" not in name else 1)

        logging.info("Motor test sequence completed")

    finally:
        # Ensure motors are stopped and cleanup
        left_motor.stop(); right_motor.stop()
        left_pwm.set(0);   right_pwm.set(0)
        GPIO.cleanup()
        logging.info("GPIO cleaned up, exiting")

if __name__ == "__main__":
    main()
