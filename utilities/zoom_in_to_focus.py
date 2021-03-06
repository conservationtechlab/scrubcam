#!/usr/bin/env python
"""Utility for digitally zooming central pixels to aid camera focusing

"""
import argparse
import time
from threading import Thread

import RPi.GPIO as GPIO
from picamera import PiCamera

ZOOM_BUTTON = 23
BACKLIGHT_PIN = 18

parser = argparse.ArgumentParser()
parser.add_argument('zoom_factor',
                    help='Factor to zoom in by')
parser.add_argument('-r',
                    '--rotation',
                    default=90,
                    help='Camera rotation angle')
args = parser.parse_args()
ZOOM_FACTOR = args.zoom_factor
ROTATION = args.rotation


class MainApp(Thread):

    def run(self):
        self.camera = PiCamera()
        self.camera.rotation = ROTATION
        self._gpio_setup()

        self.camera.start_preview()

        while True:
            self._handle_buttons()
            time.sleep(.03)

    def _gpio_setup(self):
        self.zoom_on_button = False

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(ZOOM_BUTTON,
                   GPIO.IN,
                   pull_up_down=GPIO.PUD_UP)

        GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)

        self.backlight_pwm = GPIO.PWM(BACKLIGHT_PIN, 1000)
        self.backlight_pwm.start(100)

    def _handle_buttons(self):
        if not GPIO.input(ZOOM_BUTTON):
            width, height = self.camera.resolution
            zoom_factor = 1/float(ZOOM_FACTOR)
            left = 0.5 - zoom_factor/2.
            top = 0.5 - zoom_factor/2.
            self.camera.zoom = (left, top, zoom_factor, zoom_factor)
        else:
            self.camera.zoom = (0, 0, 1.0, 1.0)

#     cam.rotation = 180


def main():
    app = MainApp()
    app.start()


if __name__ == "__main__":
    main()
