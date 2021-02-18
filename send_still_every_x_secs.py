#!/usr/bin/env python

import time
import logging
import io
import argparse
import yaml

from datetime import datetime
import picamera

from scrubcam.networking import ClientSocketHandler

logging.basicConfig(level='INFO',
                    format='[%(levelname)s] %(message)s')
log = logging

parser = argparse.ArgumentParser()
parser.add_argument('config_filename')
parser.add_argument('delay_between_sends')
args = parser.parse_args()
CONFIG_FILE = args.config_filename
DELAY_BETWEEN_SENDS = int(args.delay_between_sends)

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
CAMERA_RESOLUTION = configs['CAMERA_RESOLUTION']
CAMERA_ANGLE = configs['CAMERA_ANGLE']

socket_handler = ClientSocketHandler(configs)
stream = io.BytesIO()

camera = picamera.PiCamera()
camera.rotation = CAMERA_ANGLE
camera.resolution = CAMERA_RESOLUTION


def main():

    if configs['PREVIEW_ON']:
        camera.start_preview()

    try:
        for _ in camera.capture_continuous(stream, format='jpeg'):

            command = socket_handler.recv_command()
            if command is None:
                break
            log.info('Command: {}'.format(command))

            time.sleep(DELAY_BETWEEN_SENDS)
            socket_handler.send_image(stream)

            stream.seek(0)
            stream.truncate()
    except KeyboardInterrupt:
        log.warning('KeyboardInterrupt')
        socket_handler.close()


if __name__ == "__main__":
    main()
