#!/usr/bin/env python

import logging
import io
import argparse
import yaml

from datetime import datetime
import picamera

from scrubcam.vision import ObjectDetectionSystem
from scrubcam.display import Display

logging.basicConfig(level='INFO',
                    format='[%(levelname)s] %(message)s (%(name)s)')
log = logging.getLogger('main')

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
RECORD_CONF_THRESHOLD = configs['RECORD_CONF_THRESHOLD']

detector = ObjectDetectionSystem(configs)

stream = io.BytesIO()

camera = picamera.PiCamera()
camera.rotation = configs['CAMERA_ANGLE']
camera.resolution = configs['CAMERA_RESOLUTION']
display = Display(configs, camera)

for _ in camera.capture_continuous(stream, format='jpeg'):

    detector.infer(stream)
    detector.print_report()

    lboxes = detector.labeled_boxes
    display.update(lboxes)

    if len(lboxes) > 0:
        if RECORD and lboxes[0]['confidence'] > RECORD_CONF_THRESHOLD:
            top_class = detector.class_of_box(lboxes[0])
            detector.save_current_frame(top_class)
            with open('what_was_seen.log', 'a+') as f:
                tstamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                f.write('{} | {}\n'.format(tstamp,
                                           top_class))

    # reset the stream for the next capture
    stream.seek(0)
    stream.truncate()
