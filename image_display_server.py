import sys
import time
import socket
import struct
import io

import numpy as np
import cv2

ip = sys.argv[1]

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((ip, 65432))
server_socket.listen()

print('[INFO] Waiting for client connection.')
connection, address = server_socket.accept()
socket_stream = connection.makefile('rb')
print('[INFO] Connection made to {}.'.format(address))

try:
    while True:
        start = time.time()
        image_len = struct.unpack('<L',
                                  socket_stream.read(struct.calcsize('<L')))[0]
        if not image_len:
            break
        image_stream = io.BytesIO()
        image_stream.write(socket_stream.read(image_len))
        image_stream.seek(0)

        data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, 1)

        elapsed = time.time() - start
        print('Got image. Took {} seconds. Displaying'.format(elapsed))
        cv2.imshow('here', image)
        cv2.waitKey(1)
finally:
    socket_stream.close()
    server_socket.close()
