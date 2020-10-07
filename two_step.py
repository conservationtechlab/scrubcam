# grabs stills, inferring on each, going as fast as it can

import io
import argparse
import yaml

import picamera

import vision

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
FILTER_CLASS = configs['FILTER_CLASS']

detector = vision.ObjectDetectionSystem(configs)
classifier = vision.ImageClassificationSystem(configs)

stream = io.BytesIO()

camera = picamera.PiCamera()
camera.rotation = configs['CAMERA_ANGLE']
if configs['PREVIEW_ON']:
    camera.start_preview()

for _ in camera.capture_continuous(stream, format='jpeg'):
    stream.truncate()
    stream.seek(0)

    detector.infer(stream)
    detector.print_report(5)
    for box in detector.labeled_boxes:
        # if detector.top_class() == FILTER_CLASS:
        if detector.class_of_box(box) in FILTER_CLASS:
            # x, y, w, h = detector.top_box()
            x, y, w, h = box['box']
            
            cropped_frame = detector.frame[y:y+h, x:x+w]
            classifier.infer_on_frame(cropped_frame)
            classifier.print_report()


            if RECORD:
                classifier.save_image_of_anything_but('background')
