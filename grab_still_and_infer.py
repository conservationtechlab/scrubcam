# grabs a single frame from the picamera runs an object detector on it

import os
import io
import time
import argparse
import yaml

import picamera
import cv2
import numpy as np

from dnntools import neuralnetwork_coral as nn

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# CV constants
# TRACKED_CLASS = configs['TRACKED_CLASS']
CONF_THRESHOLD = configs['CONF_THRESHOLD']
NMS_THRESHOLD = configs['NMS_THRESHOLD']
INPUT_WIDTH = configs['INPUT_WIDTH']
INPUT_HEIGHT = configs['INPUT_HEIGHT']

MODEL_PATH = configs['MODEL_PATH']
MODEL_CONFIG = os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
MODEL_WEIGHTS = os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
CLASSES_FILE = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
CLASSES = nn.read_classes_from_file(CLASSES_FILE)

# prepaer neural network
network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                   MODEL_WEIGHTS,
                                   INPUT_WIDTH,
                                   INPUT_HEIGHT)

# Create the in-memory
stream = io.BytesIO()

with picamera.PiCamera() as camera:
    camera.start_preview()
    time.sleep(2)
    camera.capture(stream, format='jpeg')

# Construct a numpy array from the stream
data = np.fromstring(stream.getvalue(), dtype=np.uint8)

# "Decode" the image from the array, preserving color
frame = cv2.imdecode(data, 1)

outs, inference_time = network.infer(frame)

lboxes = network.filter_boxes(outs,
                              frame,
                              CONF_THRESHOLD,
                              NMS_THRESHOLD)

for lbox in lboxes:
    detected_class = CLASSES[lbox['class_id']]
    score = 100 * lbox['confidence']
    print('Detected: '
          + '{} with confidence {:.1f}'.format(detected_class,
                                              score))
else:
    print('No boxes detected')
