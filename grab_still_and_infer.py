"""Grabs camera frame, runs object detector and classification on it.

"""
import logging
import io
import time
import argparse
import yaml

import picamera

from scrubcam import vision

logging.basicConfig(level='INFO',
                    format='[%(levelname)s] %(message)s (%(name)s)')
log = logging.getLogger()
log.info("Grabs a single frame from scrubcam's picamera "
        + "and runs an object detector on it")

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

detection_system = vision.ObjectDetectionSystem(configs)
classification_system = vision.ImageClassificationSystem(configs)

stream = io.BytesIO()

with picamera.PiCamera() as camera:
    camera.rotation = configs['CAMERA_ANGLE']
    if configs['PREVIEW_ON']:
        camera.start_preview()
        time.sleep(2)
    else:
        time.sleep(.1)
    camera.capture(stream, format='jpeg')

log.info('Running object detection.')
detection_system.infer(stream)
detection_system.print_report()

log.info('Running image classification.')
classification_system.infer(stream)
classification_system.print_report()
