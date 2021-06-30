#!/usr/bin/env python
""" Dashboard for viewing images coming in over network from a scrubcam.

"""
import logging
import argparse
import time

import cv2
import numpy as np
import imutils

from viztools.visualization import FlyingPicBox
from viztools.visualization import init_pics, create_layout, GridDisplay
from viztools.draw import labeled_box_on_image

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
NUM_ROWS = 3
IMAGE_WIDTH = 700
COL_WIDTH = IMAGE_WIDTH + 10
ROW_HEIGHT = int(IMAGE_WIDTH * 9/16 + 10)

CONF_THRESHOLD = .35


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

    image = create_image_dict()
    threads_stop = False

    comms = ServerSocketHandler((IP, PORT), image, lambda: threads_stop)
    comms.setDaemon(True)
    comms.start()

    # viewer = Viewer(image, lambda: threads_stop)
    # viewer.setDaemon(True)
    # viewer.start()

    spots = {'giraffe': 0,
             'person': 1,
             'cat': 2,
             'elephant': 3,
             'zebra': 4,
             'horse': 5,
             'dog': 6,
             'bird': 7,
             'cow': 8,
             'sheep': 9,
             'bear': 10}

    inverted = {v: k for k, v in spots.items()}
    for spot in range(len(spots)):
        blank = 255 * np.ones((int(IMAGE_WIDTH * 9/16), IMAGE_WIDTH, 3))
        holder = cv2.putText(blank,
                             inverted[spot],
                             (50, 50),
                             cv2.FONT_HERSHEY_SIMPLEX,
                             1,
                             (0, 0, 0),
                             2,
                             cv2.LINE_AA)

        display_pics[spot].append(holder)

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

                    for lbox in image['lboxes']:
                        confidence = lbox['confidence']
                        if confidence > CONF_THRESHOLD:
                            box = lbox['box']
                            label = '{} {:.2f}'
                            label = label.format(lbox['class_name'],
                                                 confidence)
                            image['img'] = labeled_box_on_image(image['img'],
                                                                box,
                                                                label,
                                                                font_size=2.0)

                for lbox in image['lboxes']:
                    if lbox['class_name'] in spots.keys():
                        top_label = lbox['class_name']
                        break

                image['img'] = cv2.putText(image['img'],
                                           top_label,
                                           (50, 90),
                                           cv2.FONT_HERSHEY_SIMPLEX,
                                           3,
                                           (255, 255, 255),
                                           4,
                                           cv2.LINE_AA)

                spot = spots[top_label]
                resized_image = imutils.resize(image['img'], width=IMAGE_WIDTH)
                flypics.append(FlyingPicBox(resized_image,
                                            np.array([layout[spot][0], 0]),
                                            np.array(layout[spot])))

                if display_pics[spot]:
                    display_pics[spot].pop()
                display_pics[spot].append(resized_image)
                # spot += 1
                # if spot >= len(layout):
                #     spot = 0

                # spot = spots[label]
                # display_pics[spot].append(resized_image)

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
