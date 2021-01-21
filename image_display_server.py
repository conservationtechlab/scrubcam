#!/usr/bin/env python
import logging
import argparse
import time

import cv2

from display import Viewer
from networking import ServerSocketHandler

parser = argparse.ArgumentParser()
parser.add_argument('ip')
parser.add_argument('port')
args = parser.parse_args()
IP = args.ip
PORT = int(args.port)

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s')
log = logging


def main():
    window = 'Viewer'

    image = {'img': None, 'lboxes': None}
    threads_stop = False

    comms = ServerSocketHandler((IP, PORT), image, lambda : threads_stop)
    comms.setDaemon(True)
    comms.start()

    viewer = Viewer(image, lambda : threads_stop)
    viewer.setDaemon(True)
    viewer.start()
    
    try:
        while True:
            if image['img'] is not None:
                cv2.imshow(window,
                           image['img'])
                key = cv2.waitKey(30)
                if key == ord('q'):
                    stop_flag = True
                    break

        cv2.destroyAllWindows()

    except KeyboardInterrupt:
        log.warning('Keyboard interrupt.')
                
    threads_stop = True
    time.sleep(.1)


if __name__ == "__main__":
    main()
