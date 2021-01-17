#!/usr/bin/env python

import logging
import pickle
import argparse
import time
import socket
import struct
import io
from threading import Thread

import numpy as np
import cv2

from viztools import draw

parser = argparse.ArgumentParser()
parser.add_argument('ip')
parser.add_argument('port')
parser.add_argument('-s',
                    '--send_image',
                    action='store_true')
args = parser.parse_args()
IP = args.ip
PORT = int(args.port)
command = 1 if args.send_image else 0

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s)')
log = logging

class SocketHandler(Thread):

    def __init__(self, image, stop_flag):
        super().__init__()

        self.image = image
        self.stop_flag = stop_flag
        
        self.sock = socket.socket()
        self.sock.bind((IP, PORT))
        self.sock.listen()

    def run(self):
        while True:
            log.info('Waiting for client connection.')
            connection, address = self.sock.accept()
            stream = connection.makefile('rwb')
            log.info('Connection made to {}.'.format(address))

            if self.stop_flag():
                break
            
            while True:
                # write command to connection
                stream.write(struct.pack('<L', command))
                stream.flush()

                # read the message type
                data = stream.read(struct.calcsize('<L'))
                if not data:
                    break
                msg_type = struct.unpack('<L', data)[0]

                # execute appropriate reads based off message type
                if msg_type == 0:  # no image
                    pass
                elif msg_type == 1: # image without box
                    ok = self._read_image_data(stream)
                    if not ok:
                        break
                elif msg_type == 2: # image with box
                    ok = self._read_box(stream)
                    if not ok:
                        log.error('Trouble reading box')
                        break
                    
                    ok = self._read_image_data(stream)
                    if not ok:
                        log.error('trouble reading image')
                        break

                    box = self.image['lbox']['box']
                    self.image['img'] = draw.box_on_image(self.image['img'],
                                                          box)

            stream.close()

        self.sock.close()

    def _read_box(self, stream):
        data = stream.read(struct.calcsize('<L'))
        if not data:
            return False
        size = struct.unpack('<L', data)[0]
        log.debug(f'length of data told {size}.')

        data = stream.read(size)
        log.debug(f'length of data received {len(data)}.')
        if not data:
            return False
        self.image['lbox'] = pickle.loads(data)
        els = len(self.image['lbox'])
        log.debug(f'elements in box: {els}.')
        
        return True
    
    def _read_image_data(self, stream):
        data = stream.read(struct.calcsize('<L'))
        if not data:
            return False
        image_len = struct.unpack('<L', data)[0]
        image_stream = io.BytesIO()
        image_stream.write(stream.read(image_len))
        image_stream.seek(0)
        data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
        self.image['img'] = cv2.imdecode(data, 1)

        return True

    
def main():
    image = {'img': None, 'lbox': None}
    threads_stop = False

    comms = SocketHandler(image, lambda : threads_stop)
    comms.setDaemon(True)
    comms.start()

    try:
        while True:
            if image['img'] is not None:
                cv2.imshow('here', image['img'])
                key = cv2.waitKey(30)
                if key == ord('q'):
                    break
    except KeyboardInterrupt:
        log.warning('Keyboard interrupt.')
                
    threads_stop = True
    time.sleep(.1)


if __name__ == "__main__":
    main()
