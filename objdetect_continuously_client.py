#!/usr/bin/env python

import logging
import io
import argparse
import yaml

from datetime import datetime
import picamera

from dencam.gui import State

from scrubcam.vision import ObjectDetectionSystem
from scrubcam.networking import ClientSocketHandler
from scrubcam.display import Display

logging.basicConfig(level='INFO',
                    format='[%(levelname)s] %(message)s (%(name)s)')
log = logging.getLogger('main')

parser = argparse.ArgumentParser()
parser.add_argument('config_filename')
args = parser.parse_args()
CONFIG_FILE = args.config_filename

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
RECORD_CONF_THRESHOLD = configs['RECORD_CONF_THRESHOLD']
CAMERA_RESOLUTION = configs['CAMERA_RESOLUTION']
CAMERA_ANGLE = configs['CAMERA_ANGLE']
FILTER_CLASSES = configs['FILTER_CLASSES']


def main():
    detector = ObjectDetectionSystem(configs)
    socket_handler = ClientSocketHandler(configs)
    stream = io.BytesIO()

    camera = picamera.PiCamera()
    camera.rotation = CAMERA_ANGLE
    camera.resolution = CAMERA_RESOLUTION

    state = State(4)
    display = Display(configs, camera, state)

    try:
        for _ in camera.capture_continuous(stream, format='jpeg'):

            command = socket_handler.recv_command()
            if command is None:
                break
            log.info('Command from server is {}'.format(command))

            detector.infer(stream)
            detector.print_report()

            lboxes = detector.labeled_boxes
            display.update(lboxes)

            if command == 1:
                socket_handler.send_image(stream)

            elif len(lboxes) > 0:
                if RECORD and lboxes[0]['confidence'] > RECORD_CONF_THRESHOLD:
                    # send image over socket
                    # socket_handler.send_image(stream)

                    top_class = lboxes[0]['class_name']
                    if top_class in FILTER_CLASSES:
                        socket_handler.send_image_and_boxes(stream, lboxes)
                    else:
                        socket_handler.send_no_image()

                    detector.save_current_frame(None, lboxes=lboxes)
                    with open('what_was_seen.log', 'a+') as f:
                        time_format = '%Y-%m-%d %H:%M:%S'
                        tstamp = str(datetime.now().strftime(time_format))
                        f.write('{} | {}\n'.format(tstamp,
                                                   top_class))
                else:
                    socket_handler.send_no_image()

            else:
                socket_handler.send_no_image()

            stream.seek(0)
            stream.truncate()
    except KeyboardInterrupt:
        log.warning('KeyboardInterrupt')
        socket_handler.close()


if __name__ == "__main__":
    main()
