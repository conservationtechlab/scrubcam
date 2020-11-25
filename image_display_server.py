import io
import socket
import struct
import time

import numpy as np
import cv2

server_socket = socket.socket()
server_socket.bind(('192.168.1.66', 65432))
server_socket.listen()

print('[INFO] Waiting for client connection.')
connection = server_socket.accept()[0].makefile('rb')
print('[INFO] Connection made.')

try:
    while True:
        start = time.time()
        image_len = struct.unpack('<L',
                                  connection.read(struct.calcsize('<L')))[0]
        if not image_len:
            break
        image_stream = io.BytesIO()
        image_stream.write(connection.read(image_len))
        image_stream.seek(0)

        data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, 1)

        elapsed = time.time() - start
        print('Got image. Took {} seconds. Displaying'.format(elapsed))
        cv2.imshow('here', image)
        cv2.waitKey(1)
finally:
    connection.close()
    server_socket.close()
