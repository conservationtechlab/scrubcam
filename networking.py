import socket
import struct
import pickle

import yaml


class ImageSocketHandler():

    def __init__(self, configs):
        REMOTE_SERVER_IP = configs['REMOTE_SERVER_IP']
        PORT = configs['REMOTE_SERVER_PORT']

        print('[INFO] {} {}'.format(REMOTE_SERVER_IP, PORT))
        
        self.sock = socket.socket()
        self.sock.connect((REMOTE_SERVER_IP, PORT))
        self.connection = self.sock.makefile('rwb')

    def send_no_image(self):
        self.connection.write(struct.pack('<L', 0))
        self.connection.flush()

    def send_image(self, stream):
        self.connection.write(struct.pack('<L', 1))
        self.connection.flush()

        self._send_image_data(stream)

    def send_image_and_box(self, stream, box):
        self.connection.write(struct.pack('<L', 2))
        self.connection.flush()

        self._send_box(box)
        self._send_image_data(stream)

    def _send_image_data(self, stream):
        # send size of data in image stream
        stream.seek(0, 2)
        self.connection.write(struct.pack('<L', stream.tell()))
        self.connection.flush()
        # send image data
        stream.seek(0)
        self.connection.write(stream.read())
        self.connection.flush()

    def _send_box(self, box):
        data = pickle.dumps(box)
        size = len(data)
        self.connection.write(struct.pack('<L', size))
        self.connection.flush()
        self.connection.write(data)
        self.connection.flush()

    def recv_command(self):
        message = self.connection.read(struct.calcsize('<L'))
        if not message:
            return None
        command = struct.unpack('<L', message)[0]
        return command
        
    def close(self):
        print('Cleaning up SocketHandler')
        self.connection.close()
        self.sock.close()


# class CommandsSocketHandler():

#     def __init__(self, configs):
#         REMOTE_SERVER_IP = configs['REMOTE_SERVER_IP']
#         PORT = 65442

#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.connect((REMOTE_SERVER_IP, PORT))

#         self.command = 'w'
        
#     def recv_command(self):
        
    
