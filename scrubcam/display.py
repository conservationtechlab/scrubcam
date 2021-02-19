import time
import logging
from threading import Thread

from viztools import draw

log = logging.getLogger(__name__)


class Viewer(Thread):

    def __init__(self, image, stop_flag):
        super().__init__()
        self.image = image
        self.stop_flag = stop_flag

    def run(self):
        while True:
            log.debug('Viewer loop')
            if self.image['lboxes'] is not None:
                box = self.image['lboxes'][0]['box']
                self.image['img'] = draw.box_on_image(self.image['img'],
                                                      box)

            time.sleep(1)
