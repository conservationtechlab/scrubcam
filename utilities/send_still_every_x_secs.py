#!/usr/bin/env python
"""Captures an image from the ScrubCam's picamera and sends it to the
server program at a fixed interval in seconds. A common use is to test
functionality of all implicated hardware and systems without invoking
other components such as the Coral.

"""
import time
import logging
import io
import argparse

import yaml
import picamera

from scrubcam.networking import ClientSocketHandler

logging.basicConfig(level='INFO',
                    format='[%(levelname)s] %(message)s')

parser = argparse.ArgumentParser()
parser.add_argument('config_filename')
parser.add_argument('delay_between_sends')
args = parser.parse_args()
CONFIG_FILE = args.config_filename
DELAY_BETWEEN_SENDS = int(args.delay_between_sends)

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

socket_handler = ClientSocketHandler(configs)
stream = io.BytesIO()

camera = picamera.PiCamera()
camera.resolution = configs['CAMERA_RESOLUTION']
camera.rotation = configs['CAMERA_ROTATION']


def main():

    if configs['PREVIEW_ON']:
        camera.start_preview()

    try:
        for _ in camera.capture_continuous(stream, format='jpeg'):

            command = socket_handler.recv_command()
            if command is None:
                break
            logging.info('Command: {}'.format(command))

            time.sleep(DELAY_BETWEEN_SENDS)

            if command == 1:
                socket_handler.send_image(stream)
            else:
                # create dummy lboxes
                lbox = {'class_name': 'person',
                        'confidence': 1.0,
                        'box': (0, 0, 10, 10)}
                lboxes = [lbox]

                socket_handler.send_image_and_boxes(stream, lboxes)

            stream.seek(0)
            stream.truncate()
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt')
        socket_handler.close()


if __name__ == "__main__":
    main()
