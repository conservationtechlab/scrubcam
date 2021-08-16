"""Runs detector on frame, then classifier on detected boxes

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

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
FILTER_CLASSES = configs['FILTER_CLASSES']

detector = vision.ObjectDetectionSystem(configs)
classifier = vision.ImageClassificationSystem(configs)

stream = io.BytesIO()

camera = picamera.PiCamera()
camera.rotation = configs['CAMERA_ROTATION']
if configs['PREVIEW_ON']:
    camera.start_preview()

for _ in camera.capture_continuous(stream, format='jpeg'):
    stream.truncate()
    stream.seek(0)

    log.info('Running detector.')
    detector.infer(stream)
    detector.print_report(5)
    for box in detector.labeled_boxes:
        if detector.class_of_box(box) in FILTER_CLASSES:
            x, y, w, h = box['box']

            cropped_frame = detector.frame[y:y+h, x:x+w]
            label = box['class_name']
            log.info(f'Running classifier on filtered box with label {label}')
            classifier.infer_on_frame(cropped_frame)
            classifier.print_report()

            if RECORD:
                classifier.save_image_of_anything_but('background')
