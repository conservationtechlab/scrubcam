"""Grabs camera frame, runs both detection and classification on it.

Script to quickly check functioning of vision system elements of the
scrubcam package and also see and evaluate output from object detector
models and image classification models.

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
log.info("This script grabs a single frame from scrubcam's picamera "
         + "and runs a detector and a classifer on it")

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
    camera.rotation = configs['CAMERA_ROTATION']
    if configs['PREVIEW_ON']:
        camera.start_preview()
        time.sleep(2)
    else:
        time.sleep(.1)
    camera.capture(stream, format='jpeg')

log.info('***RUNNING OBJECT DETECTION***')
detection_system.infer(stream)
detection_system.print_report()

log.info('***RUNNING IMAGE CLASSIFICATION***')
classification_system.infer(stream)
classification_system.print_report()
