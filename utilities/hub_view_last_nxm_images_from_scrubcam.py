#!/usr/bin/env python
import logging
import argparse
import time

import cv2
import numpy as np
import imutils

from viztools.visualization import FlyingPicBox
from viztools.visualization import init_pics, create_layout, GridDisplay
from viztools import draw

from scrubcam.networking import ServerSocketHandler, create_image_dict

parser = argparse.ArgumentParser()
parser.add_argument('ip')
parser.add_argument('port')
args = parser.parse_args()
IP = args.ip
PORT = int(args.port)

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s (%(name)s)')
log = logging.getLogger('main')

JUMP_SCREENS = False
NUM_COLS = 4
NUM_ROWS = 4
COL_WIDTH = 700
ROW_HEIGHT = 400
IMAGE_WIDTH = 600


def main():
    flypics = []
    layout = create_layout(NUM_ROWS,
                           NUM_COLS,
                           COL_WIDTH,
                           ROW_HEIGHT,
                           upside_down=False)

    print('Grid: ' + str(NUM_COLS) + 'x' + str(NUM_ROWS))
    window = 'Viewer'
    display = GridDisplay(window, JUMP_SCREENS, layout)
    display_pics = init_pics(layout)
    spot = 0
    spot_count = 0

    image = create_image_dict()
    threads_stop = False

    comms = ServerSocketHandler((IP, PORT), image, lambda: threads_stop)
    comms.setDaemon(True)
    comms.start()

    # viewer = Viewer(image, lambda: threads_stop)
    # viewer.setDaemon(True)
    # viewer.start()

    try:
        while True:
            display.refresh_canvas()

            for flypic in flypics:
                flypic.update()
                flypic.display(display.canvas)
            if len(flypics) > 10:
                flypics = flypics[1:]

            key = display.draw(display_pics)
            if key == ord('q'):
                threads_stop = True
                break

            if image['img'] is not None:
                if image['lboxes'] is not None:
                    box = image['lboxes'][0]['box']
                    label = image['lboxes'][0]['class_name']
                    # 'confidence' 'class_name'
                    image['img'] = draw.labeled_box_on_image(image['img'],
                                                             box,
                                                             label,
                                                             font_size=3.0)

                resized_image = imutils.resize(image['img'], width=IMAGE_WIDTH)
                flypics.append(FlyingPicBox(resized_image,
                                            np.array([layout[spot_count][0], 0]),
                                            np.array(layout[spot_count])))
                spot_count += 1
                if spot_count >= len(layout):
                    spot_count = 0

                display_pics[spot].append(resized_image)
                spot += 1
                if spot >= len(layout):
                    spot = 0

                image['img'] = None

                # cv2.imshow(window,
                #            image['img'])
                # key = cv2.waitKey(30)
                # if key == ord('q'):
                #     threads_stop = True
                #     break

        cv2.destroyAllWindows()

    except KeyboardInterrupt:
        log.warning('Keyboard interrupt.')

    threads_stop = True
    time.sleep(.1)


if __name__ == "__main__":
    main()
