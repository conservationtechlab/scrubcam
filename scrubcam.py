"""Control code for ScrubCam

Target is a Raspberry Pi single board computer with a Picamera-style
camera and the AdaFruit PiTFTscreen (2.8" resistive touch model with 4
GPIO-connected buttons) attached.

"""

import os
import time
import subprocess

import yaml

import tkinter as tk
import tkinter.font as tkFont

from threading import Thread
from datetime import datetime

import RPi.GPIO as GPIO
from picamera import PiCamera

CONFIG_FILE = '/home/pi/projects/dencam/config.yaml'
with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
VIDEO_PATH = configs['VIDEO_PATH']
RECORD_LENGTH = configs['RECORD_LENGTH']
PAUSE_BEFORE_RECORD = configs['PAUSE_BEFORE_RECORD']
OFF_BUTTON_DELAY = configs['OFF_BUTTON_DELAY']
CAMERA_RESOLUTION = configs['CAMERA_RESOLUTION']
CAMERA_ROTATION = configs['CAMERA_ROTATION']
VIDEO_QUALITY = configs['VIDEO_QUALITY']
FRAME_RATE = configs['FRAME_RATE']

# Button pin number mappings
SCREEN_BUTTON = 27
PREVIEW_BUTTON = 23
RECORD_BUTTON = 22
OFF_BUTTON = 17


class DenCamApp(Thread):
    def run(self):
        self.initial_pause_complete = False

        # camera setup
        self.camera = PiCamera(framerate=FRAME_RATE)
        self.camera.rotation = CAMERA_ROTATION
        self.camera.resolution = CAMERA_RESOLUTION
        self.preview_on = False
        # recording setup
        self.recording = False
        self.record_start_time = time.time()  # also used in initial countdown
        self.vid_count = 0
        # interface setup
        self._gpio_setup()
        # tkinter setup
        self.window = tk.Tk()
        self._layout_window()
        self.window.attributes('-fullscreen', True)

        self.window.after(200, self._update)
        self.window.mainloop()

    def _layout_window(self):
        """Layout the information elements to be rendered to the screen.

        """
        self.window.title('DenCam Control')
        frame = tk.Frame(self.window, bg='black')
        frame.pack(fill=tk.BOTH, expand=1)
        frame.configure(bg='black')

        scrn_height = self.window.winfo_screenheight()
        small_font = tkFont.Font(family='Courier New',
                                 size=-int(scrn_height/9))

        error_font = tkFont.Font(family='Courier New',
                                 size=-int(scrn_height/12))

        big_font = tkFont.Font(family='Courier New',
                               size=-int(scrn_height/5))

        self.vid_count_label = tk.Label(frame,
                                        text='|',
                                        font=small_font,
                                        fg='blue',
                                        bg='black')
        self.vid_count_label.pack(fill=tk.X)

        self.storage_label = tk.Label(frame,
                                      text='|',
                                      font=small_font,
                                      fg='blue',
                                      bg='black')
        self.storage_label.pack(fill=tk.X)

        self.time_label = tk.Label(frame,
                                   text='|',
                                   font=small_font,
                                   fg='blue',
                                   bg='black')
        self.time_label.pack(fill=tk.X)

        self.recording_label = tk.Label(frame,
                                        text='|',
                                        font=big_font,
                                        fg='blue',
                                        bg='black')
        self.recording_label.pack(fill=tk.X)

        self.error_label = tk.Label(frame,
                                    text=' ',
                                    font=error_font,
                                    fg='red',
                                    bg='black')
        self.error_label.pack(fill=tk.X)

    def _gpio_setup(self):
        """Sets up the GPIO pins on the pi that are being used.

        Includes the 4 buttons on PiTFT that are connected to Pi GPIO
        pins and the pin that control the brightness of the backlight
        on the screen.

        """
        self.latch_screen_button = False
        self.latch_record_button = False
        self.latch_preview_button = False

        GPIO.setmode(GPIO.BCM)

        # button pins
        GPIO.setup(SCREEN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(RECORD_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(OFF_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PREVIEW_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # screen backlight control pin and related
        GPIO.setup(18, GPIO.OUT)
        self.backlight_pwm = GPIO.PWM(18, 1000)
        self.backlight_pwm.start(0)
        self.screen_on = False

        self.off_countdown = 0

    def _handle_buttons(self):
        """Handles button presses and the associated responses.
        """

        if not GPIO.input(SCREEN_BUTTON):
            if not self.latch_screen_button:
                self.latch_screen_button = True
                if self.screen_on:
                    # turn off screen
                    self.backlight_pwm.ChangeDutyCycle(0)
                    self.screen_on = False
                else:
                    # turn on screen
                    self.backlight_pwm.ChangeDutyCycle(100)
                    self.screen_on = True
        else:
            self.latch_screen_button = False

        if not GPIO.input(RECORD_BUTTON) and self.initial_pause_complete:
            if not self.latch_record_button:
                self.latch_record_button = True
                if self.recording:
                    self._stop_recording()
                else:
                    self._start_recording()
        else:
            self.latch_record_button = False

        if not GPIO.input(OFF_BUTTON):
            button_pressed_time = time.time() - self.off_button_start
            if button_pressed_time > OFF_BUTTON_DELAY:
                self.backlight_pwm.ChangeDutyCycle(0)
                subprocess.call("sudo shutdown now", shell=True)
        else:
            self.off_button_start = time.time()

        if not GPIO.input(PREVIEW_BUTTON):
            if not self.latch_preview_button:
                self.latch_preview_button = True
                if not self.preview_on:
                    self.camera.start_preview()
                else:
                    self.camera.stop_preview()
                self.preview_on = not self.preview_on
        else:
            self.latch_preview_button = False

    def _get_free_space(self):
        """Get the remaining space on SD card in gigabytes

        """
        try:
            statvfs = os.statvfs(VIDEO_PATH)
            bytes_available = statvfs.f_frsize * statvfs.f_bavail
            gigabytes_available = bytes_available/1000000000
            return gigabytes_available
        except FileNotFoundError:
            return 0

    def _get_time(self):
        """Retrieve current time and format it for screen display

        """
        local_time = time.localtime()

        hours = local_time.tm_hour
        mins = local_time.tm_min
        secs = local_time.tm_sec
        
        shours = str(hours)
        smins = str(mins)
        ssecs = str(secs)
        
        if hours < 10:
            shours = '0' + shours
        if mins < 10:
            smins = '0' + smins
        if secs < 10:
            ssecs = '0' + ssecs

        return shours + ':' + smins + ':' + ssecs

    def _start_recording(self):
        global VIDEO_PATH
        
        self.recording = True
        self.vid_count += 1

        now = datetime.now()
        date_string = now.strftime("%Y-%m-%d")

        if not os.path.exists(VIDEO_PATH):
            self.error_label['text'] = 'ERROR: \n Video path broken. \n Recording to /home/pi'
            VIDEO_PATH = '/home/pi/'
            print('[ERROR] Video path does not exist. Writing files to /home/pi')

        todays_dir = os.path.join(VIDEO_PATH, date_string)
        
        if not os.path.exists(todays_dir):
            os.makedirs(todays_dir)
        date_time_string = now.strftime("%Y-%m-%d_%H%M%S")
        filename = os.path.join(todays_dir, date_time_string + '.h264')
        self.camera.start_recording(filename, quality=VIDEO_QUALITY)
        self.record_start_time = time.time()

    def _stop_recording(self):
        self.recording = False
        self.camera.stop_recording()

    def _update(self):
        """Core loop method run at 10 Hz using tkinters "after" method.

        """
        self.elapsed_time = time.time() - self.record_start_time

        if (self.elapsed_time > PAUSE_BEFORE_RECORD) and not self.initial_pause_complete:
            self.initial_pause_complete = True
            self._start_recording()
        elif self.elapsed_time > RECORD_LENGTH and self.recording:
            self._stop_recording()
            self._start_recording()

        self._handle_buttons()

        self._draw_readout()
        self.window.after(100, self._update)

    def _draw_readout(self):
        """Draw the readout for the user to the screen.

        """

        self.vid_count_label['text'] = "Vids this run: " + str(self.vid_count)

        free_space = self._get_free_space()
        storage_string = 'Free: ' + '{0:.2f}'.format(free_space) + ' GB'
        self.storage_label['text'] = storage_string

        self.time_label['text'] = 'Time: ' + self._get_time()

        if not self.initial_pause_complete:
            rec_text = '{0:.0f}'.format(PAUSE_BEFORE_RECORD - self.elapsed_time)
        else:
            rec_text = '{}'.format('Recording' if self.recording else 'Idle')
        self.recording_label['text'] = rec_text


def main():
    app = DenCamApp()
    app.start()


if __name__ == "__main__":
    main()
