import re
import os
from datetime import datetime

import numpy as np
import cv2

from dnntools import neuralnetwork_coral as nn

class InferenceSystem():
    def __init__(self, configs):
        # CV constants
        self.CONF_THRESHOLD = configs['CONF_THRESHOLD']

        MODEL_PATH = configs['MODEL_PATH']
        self.MODEL = os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
        CLASSES_FILE = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
        self.RECORD_FOLDER = configs['RECORD_FOLDER']
        self.CLASSES = nn.read_classes_from_file(CLASSES_FILE)

        self.recorded_image_count = 0

        self.frame = None
        
    def infer_on_frame(self, frame):
        self.frame = frame
        self.result, inference_time = self.network.infer(self.frame)
        
    def infer(self, stream):
        # Construct a numpy array from the stream
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        # "Decode" the image from the array, preserving color
        self.frame = cv2.imdecode(data, 1)

        self.infer_on_frame(self, self.frame)

class ImageClassificationSystem(InferenceSystem):

    def __init__(self, configs):
        super().__init__(configs)

        # prepare neural network
        self.network = nn.ImageClassifierHandler(self.MODEL)

    def _extract_label_and_score(self):
        label = self.CLASSES[self.result[0][0]]
        score = self.result[0][1]

        return label, score
        
    def print_report(self):
        if len(self.result) > 0:
            label, score = self._extract_label_and_score()
            print('***{}*** is classification (Top 1) with score: {}'.format(label,
                                                                             score))
        else:
            print('Inference resulted in no class label.')

    def save_image_of_anything_but(self, excluded_class):
        # also thresholds on score threshold defined in config file
        if len(self.result) > 0:
            label, score = self._extract_label_and_score()
            if label != excluded_class and score >= self.CONF_THRESHOLD:
                label = re.sub('[()]', '', label)
                label = '_'.join(label.split(' '))
                print(label)
                now = datetime.now()
                timestamp = now.strftime("%Y-%m-%dT%Hh%Mm%Ss.%f")[:-3]
                filename = '{}_{}.jpeg'.format(timestamp, label)
                self.recorded_image_count += 1
                full_filename = os.path.join(self.RECORD_FOLDER, filename)
                print('[INFO] Saving image to {}'.format(full_filename))
                ok = cv2.imwrite(full_filename, self.frame)
                if not ok:
                    print('[WARNING]: did not succeed in image saving.')


class ObjectDetectionSystem():

    def __init__(self, configs):
        # CV constants
        # TRACKED_CLASS = configs['TRACKED_CLASS']
        self.CONF_THRESHOLD = configs['CONF_THRESHOLD']
        self.NMS_THRESHOLD = configs['NMS_THRESHOLD']
        INPUT_WIDTH = configs['INPUT_WIDTH']
        INPUT_HEIGHT = configs['INPUT_HEIGHT']

        MODEL_PATH = configs['MODEL_PATH']
        MODEL_CONFIG = os.path.join(MODEL_PATH, configs['OBJ_MODEL_CONFIG_FILE'])
        MODEL_WEIGHTS = os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
        CLASSES_FILE = os.path.join(MODEL_PATH, configs['OBJ_CLASS_NAMES_FILE'])
        self.CLASSES = nn.read_classes_from_file(CLASSES_FILE)

        self.frame = None
        
        # prepare neural network
        self.network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                                MODEL_WEIGHTS,
                                                INPUT_WIDTH,
                                                INPUT_HEIGHT)

    def infer(self, stream):
        # Construct a numpy array from the stream
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        # "Decode" the image from the array, preserving color
        self.frame = cv2.imdecode(data, 1)

        outs, inference_time = self.network.infer(self.frame)

        self.labeled_boxes = self.network.filter_boxes(outs,
                                                       self.frame,
                                                       self.CONF_THRESHOLD,
                                                       self.NMS_THRESHOLD)

    def class_of_box(self, box):
        return self.CLASSES[box['class_id']]
        
    def print_report(self, max_boxes=None):
        if self.labeled_boxes:
            if max_boxes is None:
                max_boxes = len(self.labeled_boxes)
            for i, box in enumerate(self.labeled_boxes[:max_boxes]):
                detected_class = self.class_of_box(box)
                score = 100 * box['confidence']
                print('{} ***{}*** detected. With confidence {:.1f}'.format(i,
                                                                            detected_class,
                                                                            score))
        else:
            print('No boxes detected')

    def top_class(self):
        if self.labeled_boxes:
            return self.class_of_box(self.labeled_boxes[0])

    def top_box(self):
        if self.labeled_boxes:
            return self.labeled_boxes[0]['box']
