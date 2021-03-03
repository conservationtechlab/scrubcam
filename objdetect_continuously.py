#!/usr/bin/env python

import time
import logging
import io
import argparse
import yaml

from datetime import datetime

from dencam.buttons import ButtonHandler
from dencam.gui import State, Controller
from dencam.recorder import BaseRecorder

from scrubcam.vision import ObjectDetectionSystem
from scrubcam.display import Display

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
RECORD_CONF_THRESHOLD = configs['RECORD_CONF_THRESHOLD']
FILTER_CLASSES = configs['FILTER_CLASSES']


class Recorder(BaseRecorder):
    def __init__(self, configs):
        super().__init__(configs)

        self.vid_count = 0

    def start_recording(self):
        self.recording = True
        log.info('Recording turned on.')

    def stop_recording(self):
        self.recording = False
        log.info('Recording turned off.')

    def update(self, lboxes):
        self.vid_count += 1
        with open('what_was_seen.log', 'a+') as f:
            time_strg = '%Y-%m-%d %H:%M:%S'
            tstamp = str(datetime.now().strftime(time_strg))
            top_class = lboxes[0]['class_name']
            f.write('{} | {}\n'.format(tstamp,
                                       top_class))


def main():
    log.info(f'Confidence threshold to save image: {RECORD_CONF_THRESHOLD}')
    log.info(f'\n{"-"*40}\nTARGET CLASSES: {" | ".join(FILTER_CLASSES)}\n{"-"*40}')

    try:
        flags = {'stop_buttons_flag': False}

        def cleanup(flags):
            flags['stop_button_flag'] = True
            time.sleep(.1)

        detector = ObjectDetectionSystem(configs)

        stream = io.BytesIO()

        recorder = Recorder(configs)
        state = State(4)
        state.value = 1
        display = Display(configs, recorder.camera, state)

        button_handler = ButtonHandler(recorder,
                                       state,
                                       lambda: flags['stop_buttons_flag'])
        button_handler.setDaemon(True)
        button_handler.start()

        controller = Controller(configs, recorder, state)
        controller.setDaemon(True)
        controller.start()

        for _ in recorder.camera.capture_continuous(stream, format='jpeg'):

            detector.infer(stream)
            detector.print_report()

            lboxes = detector.labeled_boxes
            display.update(lboxes)

            if len(lboxes) > 0:
                class_names = [lbox['class_name'] for lbox in lboxes]
                if (recorder.recording
                    and any(item in FILTER_CLASSES for item in class_names)
                    and lboxes[0]['confidence'] > RECORD_CONF_THRESHOLD):
                    detector.save_current_frame(None, lboxes=lboxes)
                    recorder.update(lboxes)

            # reset the stream for the next capture
            stream.seek(0)
            stream.truncate()
    except KeyboardInterrupt:
        log.debug('Keyboard Interrupt.')
        cleanup(flags)
    except Exception:
        log.exception('Exception in primary try block.')
        cleanup(flags)


if __name__ == '__main__':
    main()
