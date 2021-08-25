#!/usr/bin/env python
"""Code for ScrubCam field device

The code that runs on the Scrubcam field device.  Gets configuration
information from a YAML file provided as a command line argument.
There is an example configuration file at:

cfgs/config.yaml.example

To run:

./scrubcam.py cfgs/YOUR_CONFIGURATION_FILE.yaml

"""
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
parser.add_argument('-c', '--continue', dest='cont', action='store_true')
args = parser.parse_args()
CONFIG_FILE = args.config_filename
CONTINUE_RUN = args.cont

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
RECORD_CONF_THRESHOLD = configs['RECORD_CONF_THRESHOLD']
CAMERA_RESOLUTION = configs['CAMERA_RESOLUTION']
CAMERA_ROTATION = configs['CAMERA_ROTATION']
FILTER_CLASSES = configs['FILTER_CLASSES']

HEADLESS = configs['HEADLESS']
SEND_IMAGES = configs['SEND_IMAGES']


def main():
    detector = ObjectDetectionSystem(configs)
    stream = io.BytesIO()

    camera = picamera.PiCamera()
    camera.rotation = CAMERA_ROTATION
    camera.resolution = CAMERA_RESOLUTION

    if SEND_IMAGES:
        log.info('Connecting to server enabled')
        socket_handler = ClientSocketHandler(configs)
        socket_handler.send_host_configs(FILTER_CLASSES, CONTINUE_RUN)
    else:
        log.info('Connecting to server ***DISABLED***\n\n')

    if not HEADLESS:
        state = State(4)
        display = Display(configs, camera, state)

    try:
        for _ in camera.capture_continuous(stream, format='jpeg'):
            socket_handler.send_heartbeat_every_15s()            
            detector.infer(stream)
            detector.print_report()

            lboxes = detector.labeled_boxes
            if not HEADLESS:
                display.update(lboxes)

            if len(lboxes) > 0:
                if RECORD and lboxes[0]['confidence'] > RECORD_CONF_THRESHOLD:
                    detected_classes = [lbox['class_name'] for lbox in lboxes]
                    if any(itm in FILTER_CLASSES for itm in detected_classes):
                        if SEND_IMAGES:
                            socket_handler.send_image_and_boxes(stream, lboxes)
                        detector.save_current_frame(None, lboxes=lboxes)
                        log.debug('Image sent')

                    with open('what_was_seen.log', 'a+') as f:
                        time_format = '%Y-%m-%d %H:%M:%S'
                        tstamp = str(datetime.now().strftime(time_format))
                        top_class = lboxes[0]['class_name']
                        f.write('{} | {}\n'.format(tstamp,
                                                   top_class))

            stream.seek(0)
            stream.truncate()
    except KeyboardInterrupt:
        log.warning('KeyboardInterrupt')
        if SEND_IMAGES:
            socket_handler.close()


if __name__ == "__main__":
    main()
