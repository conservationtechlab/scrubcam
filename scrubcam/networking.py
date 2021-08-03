import logging
import io
import socket
import struct
import pickle
from threading import Thread

import cv2
import numpy as np

log = logging.getLogger(__name__)


def create_image_dict():
    """Creates the image dictionary that we are using as the way a
    ServerSocketHandler (and perhaps other things) share what they
    receive from the socket with other parts of the program.

    """
    return {'img': None, 'lboxes': None}


class ServerSocketHandler(Thread):

    def __init__(self, address, image, stop_flag):
        super().__init__()

        self.image = image
        self.stop_flag = stop_flag

        self.sock = socket.socket()
        self.sock.bind(address)
        self.sock.listen()

        # command to send image no matter what. so far no real control
        # of this is implemented as evidenced in its here being just set
        self.command = 0

    def run(self):
        while True:
            log.info('Waiting for client connection.')
            connection, address = self.sock.accept()
            stream = connection.makefile('rwb')
            log.info('Connection made to {}'.format(address))

            if self.stop_flag():
                break

            while True:
                # write command to connection
                stream.write(struct.pack('<L', self.command))
                stream.flush()

                # read the message type
                data = stream.read(struct.calcsize('<L'))
                if not data:
                    break
                msg_type = struct.unpack('<L', data)[0]

                # execute appropriate reads based off message type
                if msg_type == 0:  # no image
                    pass
                elif msg_type == 1:  # image without box
                    ok = self._read_image_data(stream)
                    if not ok:
                        break
                elif msg_type == 2:  # image with boxes
                    log.info('Receiving image with boxes.')
                    ok = self._read_box(stream)
                    if not ok:
                        log.error('Trouble reading boxes')
                        break

                    ok = self._read_image_data(stream)
                    if not ok:
                        log.error('trouble reading image')
                        break

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
        self.image['lboxes'] = pickle.loads(data)

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


class ClientSocketHandler():

    def __init__(self, configs):
        REMOTE_SERVER_IP = configs['REMOTE_SERVER_IP']
        PORT = configs['REMOTE_SERVER_PORT']

        strg = 'Attempting to connect to server at: {} {}'
        strg = strg.format(REMOTE_SERVER_IP,
                           PORT)
        log.info(strg)

        self.sock = socket.socket()
        self.sock.connect((REMOTE_SERVER_IP, PORT))
        self.socket_stream = self.sock.makefile('rwb')

    def send_no_image(self):
        self.socket_stream.write(struct.pack('<L', 0))
        self.socket_stream.flush()

    def send_image(self, image_stream):
        self.socket_stream.write(struct.pack('<L', 1))
        self.socket_stream.flush()

        self._send_image_data(image_stream)

    # def send_image_and_box(self, image_stream, box):
    #     self.socket_stream.write(struct.pack('<L', 2))
    #     self.socket_stream.flush()

    #     self._send_object(box)
    #     self._send_image_data(image_stream)

    def send_image_and_boxes(self, image_stream, boxes):
        # creating header
        header = "IMAGE"
        header_bytes = header.encode()

        # send header size
        self.socket_stream.write(struct.pack('<L', len(header_bytes)))
        self.socket_stream.flush()
        # send header bytes
        self.socket_stream.write(header_bytes)
        self.socket_stream.flush()

        self._send_object(boxes)
        self._send_image_data(image_stream)

    def _send_image_data(self, image_stream):
        # send size of data in image image_stream
        image_stream.seek(0, 2)
        self.socket_stream.write(struct.pack('<L', image_stream.tell()))
        self.socket_stream.flush()
        # send image data
        image_stream.seek(0)
        self.socket_stream.write(image_stream.read())
        self.socket_stream.flush()

    def _send_object(self, a_object):
        data = pickle.dumps(a_object)
        size = len(data)
        self.socket_stream.write(struct.pack('<L', size))
        self.socket_stream.flush()
        self.socket_stream.write(data)
        self.socket_stream.flush()

    def recv_command(self):
        message = self.socket_stream.read(struct.calcsize('<L'))
        if not message:
            return None
        command = struct.unpack('<L', message)[0]
        return command

    def send_image_classes(self, filter_classes):
        # creating header
        header = "CLASSES"
        header_bytes = header.encode()

        # send header size
        self.socket_stream.write(struct.pack('<L', len(header_bytes)))
        self.socket_stream.flush()
        # send header bytes
        self.socket_stream.write(header_bytes)
        self.socket_stream.flush()

        # convert classes list into a bytestream
        log.debug(filter_classes)
        classes_bytes = pickle.dumps(filter_classes)

        # send size of image classes list
        self.socket_stream.write(struct.pack('<L', len(classes_bytes)))
        self.socket_stream.flush()
        # send image classes list
        self.socket_stream.write(classes_bytes)
        self.socket_stream.flush()

        log.info('Classes sent to Scrubdash')

    def close(self):
        log.info('Cleaning up SocketHandler')
        self.socket_stream.close()
        self.sock.close()


# class CommandsSocketHandler():

#     def __init__(self, configs):
#         REMOTE_SERVER_IP = configs['REMOTE_SERVER_IP']
#         PORT = 65442

#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.connect((REMOTE_SERVER_IP, PORT))

#         self.command = 'w'

#     def recv_command(self):
