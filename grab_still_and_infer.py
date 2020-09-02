# grabs a single frame from the picamera runs an object detector on it

import io
import time
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

vision = vision.VisionSystem(configs)

# Create the in-memory
stream = io.BytesIO()

with picamera.PiCamera() as camera:
    camera.rotation = configs['CAMERA_ANGLE']
    camera.start_preview()
    time.sleep(2)
    camera.capture(stream, format='jpeg')

vision.infer(stream)
