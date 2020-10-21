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
    
detector = vision.ObjectDetectionSystem(configs)

stream = io.BytesIO()

resolution = (1280, 720)

camera = picamera.PiCamera()
camera.rotation = configs['CAMERA_ANGLE']
camera.resolution = resolution

if configs['PREVIEW_ON']:
    camera.start_preview()

for _ in camera.capture_continuous(stream, format='jpeg'):
    stream.truncate()
    stream.seek(0)

    detector.infer(stream)
    detector.print_report()



