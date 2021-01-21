import logging
import socket
import struct
import pickle

import yaml

log = logging


class ImageSocketHandler():

    def __init__(self, configs):
        REMOTE_SERVER_IP = configs['REMOTE_SERVER_IP']
        PORT = configs['REMOTE_SERVER_PORT']

        log.info('{} {}'.format(REMOTE_SERVER_IP, PORT))
        
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
        self.socket_stream.write(struct.pack('<L', 2))
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
        
    
