import socket
import struct

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
        self.connection.write(struct.pack('<L', 7))
        self.connection.flush()

    def send_image(self, stream):
        stream.seek(0, 2)
        self.connection.write(struct.pack('<L', stream.tell()))
        self.connection.flush()
        stream.seek(0)
        self.connection.write(stream.read())

    def recv_command(self):
        message = self.connection.read(struct.calcsize('<L'))
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
        
    
