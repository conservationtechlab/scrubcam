import sys
import time
import socket
import struct
import io

import numpy as np
import cv2

ip = sys.argv[1]
port = int(sys.argv[2])

command = 0

with socket.socket() as server_socket:
    server_socket.bind((ip, port))
    server_socket.listen()

    print('[INFO] Waiting for client connection.')
    connection, address = server_socket.accept()
    socket_stream = connection.makefile('rwb')
    print('[INFO] Connection made to {}.'.format(address))

    while True:
        start = time.time()

        socket_stream.write(struct.pack('<L', command))
        socket_stream.flush()
        
        message = socket_stream.read(struct.calcsize('<L'))
        image_len = struct.unpack('<L', message)[0]

        if not image_len:
            break

        if image_len == 7:
            pass
        else:
            image_stream = io.BytesIO()
            image_stream.write(socket_stream.read(image_len))
            image_stream.seek(0)

        
            data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
            image = cv2.imdecode(data, 1)

            elapsed = time.time() - start
            print('Got image. Took {} seconds. Displaying'.format(elapsed))
            cv2.imshow('here', image)
            cv2.waitKey(1)
