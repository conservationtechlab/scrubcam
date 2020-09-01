import os

import numpy as np
import cv2

from dnntools import neuralnetwork_coral as nn


class VisionSystem():

    def __init__(self, configs):
        # CV constants
        # TRACKED_CLASS = configs['TRACKED_CLASS']
        self.CONF_THRESHOLD = configs['CONF_THRESHOLD']
        self.NMS_THRESHOLD = configs['NMS_THRESHOLD']
        INPUT_WIDTH = configs['INPUT_WIDTH']
        INPUT_HEIGHT = configs['INPUT_HEIGHT']

        MODEL_PATH = configs['MODEL_PATH']
        MODEL_CONFIG = os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
        MODEL_WEIGHTS = os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
        CLASSES_FILE = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
        self.CLASSES = nn.read_classes_from_file(CLASSES_FILE)

        # prepare neural network
        self.network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                                MODEL_WEIGHTS,
                                                INPUT_WIDTH,
                                                INPUT_HEIGHT)

    def infer(self, stream):
        # Construct a numpy array from the stream
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        # "Decode" the image from the array, preserving color
        frame = cv2.imdecode(data, 1)

        outs, inference_time = self.network.infer(frame)

        labeled_boxes = self.network.filter_boxes(outs,
                                                  frame,
                                                  self.CONF_THRESHOLD,
                                                  self.NMS_THRESHOLD)
        if labeled_boxes:
            for box in labeled_boxes:
                detected_class = self.CLASSES[box['class_id']]
                score = 100 * box['confidence']
                print('Detected: '
                      + '{} with confidence {:.1f}'.format(detected_class,
                                                           score))
        else:
            print('No boxes detected')
