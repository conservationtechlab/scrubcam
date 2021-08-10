import csv
import logging
import re
import os
from datetime import datetime

import numpy as np
import cv2

from camml import coral as nn

log = logging.getLogger(__name__)


class InferenceSystem():
    def __init__(self, configs):
        # CV constants
        self.CONF_THRESHOLD = configs['CONF_THRESHOLD']
        self.MODEL_PATH = configs['MODEL_PATH']
        self.MODEL_WEIGHTS = 'N/A'  # not applicable
        self.RECORD_FOLDER = configs['RECORD_FOLDER']
        self.recorded_image_count = 0
        self.frame = None

    def infer_on_frame(self, frame):
        raise NotImplementedError

    def infer(self, stream):
        # may not be necessary since using .getvalue()
        stream.seek(0)
        # Construct a numpy array from the stream
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        # "Decode" the image from the array, preserving color
        self.frame = cv2.imdecode(data, 1)
        self.infer_on_frame(self.frame)

    def _write_boxes_file(self, timestamp, lboxes):
        filename = '{}.csv'.format(timestamp)
        full_filename = os.path.join(self.RECORD_FOLDER, filename)
        with open(full_filename, 'w') as f:
            self.csv_writer = csv.writer(f,
                                         delimiter=',',
                                         quotechar='"',
                                         quoting=csv.QUOTE_MINIMAL)
            for lbox in lboxes:
                self.csv_writer.writerow([lbox['class_name'],
                                          lbox['confidence'],
                                          *lbox['box']])

    def save_current_frame(self, label, lboxes=None):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%Hh%Mm%Ss.%f")[:-3]
        if label is None:
            label = lboxes[0]['class_name']
        filename = '{}_{}.jpeg'.format(timestamp, label)
        self.recorded_image_count += 1
        full_filename = os.path.join(self.RECORD_FOLDER, filename)
        log.info('Saving image.')
        log.debug('Image filename is {}'.format(full_filename))
        ok = cv2.imwrite(full_filename, self.frame)
        if not ok:
            log.warning('Did not succeed in image saving.')

        if lboxes is not None:
            log.debug('Writing csv files of boxes.')
            self._write_boxes_file(timestamp, lboxes)


class ImageClassificationSystem(InferenceSystem):

    def __init__(self, configs):
        super().__init__(configs)
        self.MODEL = os.path.join(self.MODEL_PATH,
                                  configs['MODEL_CONFIG_FILE'])
        CLASSES_FILE = os.path.join(self.MODEL_PATH,
                                    configs['CLASS_NAMES_FILE'])
        self.CLASSES = nn.read_classes_from_file(CLASSES_FILE)
        # prepare neural network
        self.network = nn.ImageClassifierHandler(self.MODEL)

    def infer_on_frame(self, frame):
        self.result, inference_time = self.network.infer(frame)

    def _extract_label_and_score(self):
        label = self.CLASSES[self.result[0][0]]
        score = self.result[0][1]

        return label, score

    def print_report(self):
        if len(self.result) > 0:
            label, score = self._extract_label_and_score()
            strg = '***{}*** is classification (Top 1) with score: {}'
            log.info(strg.format(label,
                                 score))
        else:
            log.info('Inference resulted in no class label.')

    def save_image_of_anything_but(self, excluded_class):
        # also thresholds on score threshold defined in config file
        if len(self.result) > 0:
            label, score = self._extract_label_and_score()
            if label != excluded_class and score >= self.CONF_THRESHOLD:
                label = re.sub('[()]', '', label)
                label = '_'.join(label.split(' '))
                log.debug(label)
                self.save_current_frame(label)


class ObjectDetectionSystem(InferenceSystem):

    def __init__(self, configs):
        super().__init__(configs)
        # CV constants
        # TRACKED_CLASS = configs['TRACKED_CLASS']
        INPUT_WIDTH = configs['INPUT_WIDTH']
        INPUT_HEIGHT = configs['INPUT_HEIGHT']
        MODEL_CONFIG = os.path.join(self.MODEL_PATH,
                                    configs['OBJ_MODEL_CONFIG_FILE'])
        OBJ_CLASSES_FILE = os.path.join(self.MODEL_PATH,
                                        configs['OBJ_CLASS_NAMES_FILE'])
        self.OBJ_CLASSES = nn.read_classes_from_file(OBJ_CLASSES_FILE)

        self.NMS_THRESHOLD = configs['NMS_THRESHOLD']
        # prepare neural network
        self.network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                                self.MODEL_WEIGHTS,
                                                INPUT_WIDTH,
                                                INPUT_HEIGHT)

    def infer_on_frame(self, frame):
        outs, inference_time = self.network.infer(frame)
        self.labeled_boxes = self.network.filter_boxes(outs,
                                                       frame,
                                                       self.CONF_THRESHOLD,
                                                       self.NMS_THRESHOLD)
        for lbox in self.labeled_boxes:
            lbox['class_name'] = self.class_of_box(lbox)

    def class_of_box(self, lbox):
        return self.OBJ_CLASSES[lbox['class_id']]

    def print_report(self, max_boxes=None):
        if self.labeled_boxes:
            if max_boxes is None:
                max_boxes = len(self.labeled_boxes)
            for i, box in enumerate(self.labeled_boxes[:max_boxes]):
                detected_class = self.class_of_box(box)
                score = 100 * box['confidence']
                strng = 'Box {}: {}. With confidence {:.1f}'
                log.info(strng.format(i,
                                      detected_class,
                                      score))
        else:
            log.debug('No boxes detected')

    def top_class(self):
        if self.labeled_boxes:
            return self.class_of_box(self.labeled_boxes[0])

    def top_box(self):
        if self.labeled_boxes:
            return self.labeled_boxes[0]['box']

    # def coords_of_top_box(self):
    #     return self.labeled_boxes[0][
