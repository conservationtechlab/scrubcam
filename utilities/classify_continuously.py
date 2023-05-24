"""Runs image classifier on each , inferring on each, going as fast as it can


"""
import logging
import io
import argparse
import yaml

import picamera

from scrubcam import vision

logging.basicConfig(level='INFO',
                    format='[%(levelname)s] %(message)s (%(name)s)')
log = logging.getLogger('main')

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']

classifier = vision.ImageClassificationSystem(configs)

stream = io.BytesIO()

camera = picamera.PiCamera()
camera.rotation = configs['CAMERA_ROTATION']
if configs['PREVIEW_ON']:
    camera.start_preview()

for _ in camera.capture_continuous(stream, format='jpeg'):
    stream.truncate()
    stream.seek(0)

    classifier.infer(stream)
    classifier.print_report()

    if RECORD:
        classifier.save_image_of_anything_but('background')
