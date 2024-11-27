"""Tools for handling ML inference on image data 

"""
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
    """Base class for inference systems

    Note: is an abstract base class

    """

    def __init__(self, configs):
        # CV constants
        self.conf_threshold = configs['CONF_THRESHOLD']
        self.model_path = configs['MODEL_PATH']
        self.model_weights = 'N/A'  # not applicable
        self.record_folder = configs['RECORD_FOLDER']
        self.recorded_image_count = 0
        self.frame = None
        self._ensure_record_folder()

    def infer_on_frame(self, frame):
        """Run inference on a single frame

        """
        raise NotImplementedError

    def infer(self, stream):
        """Run inference on stream

        Is built around the stream that comes in from a picamera
        """
        # may not be necessary since using .getvalue()
        stream.seek(0)
        # Construct a numpy array from the stream
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        # "Decode" the image from the array, preserving color
        self.frame = cv2.imdecode(data, 1)
        self.infer_on_frame(self.frame)

    def _write_boxes_file(self, timestamp, lboxes):
        """Write a list of lboxes to a CSV

        The CSV is given timestamp as its name

        """
        filename = f"{timestamp}.csv"
        full_filename = os.path.join(self.record_folder, filename)
        with open(full_filename, 'w', encoding="utf8") as f:
            csv_writer = csv.writer(f,
                                    delimiter=',',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
            for lbox in lboxes:
                csv_writer.writerow([lbox['class_name'],
                                     lbox['confidence'],
                                     *lbox['box']])

    def save_current_frame(self, label, lboxes=None):
        """Save current frame to disk as JPG image

        """
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%Hh%Mm%Ss.%f")[:-3]
        if label is None:
            label = lboxes[0]['class_name']
        filename = f"{timestamp}_{label}.jpeg"
        self.recorded_image_count += 1
        full_filename = os.path.join(self.record_folder, filename)
        log.info('Saving image.')
        log.debug("Image filename is %s", full_filename)
        ok = cv2.imwrite(full_filename, self.frame)
        if not ok:
            log.warning('Did not succeed in image saving.')

        if lboxes is not None:
            log.debug('Writing csv files of boxes.')
            self._write_boxes_file(timestamp, lboxes)

    def _ensure_record_folder(self):
        """Ensure recording folder in configurations exists

        """
        folder_exists = os.path.exists(self.record_folder)

        if not folder_exists:
            os.mkdir(self.record_folder)


class ImageClassificationSystem(InferenceSystem):
    """Inference system that handles image classification

    """

    def __init__(self, configs):
        super().__init__(configs)
        self.model = os.path.join(self.model_path,
                                  configs['MODEL_CONFIG_FILE'])
        classes_file = os.path.join(self.model_path,
                                    configs['CLASS_NAMES_FILE'])

        self.classes = nn.read_classes_from_file(classes_file)
        # prepare neural network
        self.network = nn.ImageClassifierHandler(self.model)

        self.result = None

    def infer_on_frame(self, frame):
        self.result, _ = self.network.infer(frame)

    def _extract_label_and_score(self):
        label = self.classes[self.result[0][0]]
        score = self.result[0][1]

        return label, score

    def print_report(self):
        """Log the Top-1 label and score

        """
        if len(self.result) > 0:
            label, score = self._extract_label_and_score()
            strg = "***%s*** is classification (Top 1) with score: %.2f"
            log.info(strg, label, score)
        else:
            log.info('Inference resulted in no class label.')

    def save_image_of_anything_but(self, excluded_class):
        """Save current frame to disk unless its label is excluded class

        """
        # also thresholds on score threshold defined in config file
        if len(self.result) > 0:
            label, score = self._extract_label_and_score()
            if label != excluded_class and score >= self.conf_threshold:
                label = re.sub('[()]', '', label)
                label = '_'.join(label.split(' '))
                log.debug(label)
                self.save_current_frame(label)


class ObjectDetectionSystem(InferenceSystem):
    """Handles object detection

    """

    def __init__(self, configs):
        super().__init__(configs)
        # CV constants
        # TRACKED_CLASS = configs['TRACKED_CLASS']
        input_width = configs['INPUT_WIDTH']
        input_height = configs['INPUT_HEIGHT']
        model_config = os.path.join(self.model_path,
                                    configs['OBJ_MODEL_CONFIG_FILE'])
        obj_classes_file = os.path.join(self.model_path,
                                        configs['OBJ_CLASS_NAMES_FILE'])

        self.obj_classes = []
        self.labeled_boxes = None
        with open(obj_classes_file, 'r', encoding="utf8") as f:
            for row in f:
                self.obj_classes.append(row.strip())

        self.nms_threshold = configs['NMS_THRESHOLD']
        # prepare neural network
        self.network = nn.ObjectDetectorHandler(model_config,
                                                self.model_weights,
                                                input_width,
                                                input_height)

    def infer_on_frame(self, frame):
        outs, _ = self.network.infer(frame)
        self.labeled_boxes = self.network.filter_boxes(outs,
                                                       frame,
                                                       self.conf_threshold,
                                                       self.nms_threshold)
        for lbox in self.labeled_boxes:
            lbox['class_name'] = self.class_of_box(lbox)

    def class_of_box(self, lbox):
        """Return class of current lbox

        """
        return self.obj_classes[lbox['class_id']]

    def print_report(self, max_boxes=None):
        """Log information about detected boxes

        """
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
        """Return top class

        """
        top_class = None
        if self.labeled_boxes:
            top_class =  self.class_of_box(self.labeled_boxes[0])
        return top_class

    def top_box(self):
        """Return top box

        """
        top_box = None
        if self.labeled_boxes:
            top_box = self.labeled_boxes[0]['box']
        return top_box
