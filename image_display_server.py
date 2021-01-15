import argparse
import time
import socket
import struct
import io
from threading import Thread

import numpy as np
import cv2

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
            print('[INFO] Waiting for client connection.')
            connection, address = self.sock.accept()
            stream = connection.makefile('rwb')
            print('[INFO] Connection made to {}.'.format(address))

            if self.stop_flag():
                break
            
            while True:
                start = time.time()

                stream.write(struct.pack('<L', command))
                stream.flush()

                data = stream.read(struct.calcsize('<L'))
                if not data:
                    break
                image_len = struct.unpack('<L', data)[0]

                if not image_len:
                    break

                if image_len == 7:
                    pass
                else:
                    image_stream = io.BytesIO()
                    image_stream.write(stream.read(image_len))
                    image_stream.seek(0)

                elapsed = time.time() - start
                print('Got image. Took {} seconds'.format(elapsed))

                data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
                self.image[0] = cv2.imdecode(data, 1)

            stream.close()

        self.sock.close()


def main():
    image = [None]
    threads_stop = False

    comms = SocketHandler(image, lambda : threads_stop)
    comms.setDaemon(True)
    comms.start()

    while True:
        if image[0] is not None:
            cv2.imshow('here', image[0])
            key = cv2.waitKey(30)
            if key == ord('q'):
                break

            threads_stop = True
    time.sleep(.1)


if __name__ == "__main__":
    main()
