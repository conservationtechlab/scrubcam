import argparse
import time
import socket
import struct
import io

import numpy as np
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('ip')
parser.add_argument('port')
args = parser.parse_args()
ip = args.ip
port = int(args.port)

command = 0

with socket.socket() as server_socket:
    server_socket.bind((ip, port))
    server_socket.listen()

    while True:
        print('[INFO] Waiting for client connection.')
        connection, address = server_socket.accept()
        stream = connection.makefile('rwb')
        print('[INFO] Connection made to {}.'.format(address))

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


                data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
                image = cv2.imdecode(data, 1)

                elapsed = time.time() - start
                print('Got image. Took {} seconds. Displaying'.format(elapsed))
                cv2.imshow('here', image)
                cv2.waitKey(1)

        stream.close()
