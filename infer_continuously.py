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

# vision = vision.VisionSystem(configs)
vision = vision.ImageClassificationSystem(configs)

# Create the in-memory
stream = io.BytesIO()

camera = picamera.PiCamera()
camera.rotation = configs['CAMERA_ANGLE']
if configs['PREVIEW_ON']:
    camera.start_preview()

for _ in camera.capture_continuous(stream, format='jpeg'):
    stream.truncate()
    stream.seek(0)

    vision.infer(stream)
    vision.print_report()