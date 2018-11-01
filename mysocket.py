import socket
import sys
import collections
from utils import GetException
from log import Log


HOST = ''   # Symbolic name meaning all available interfaces
PORT = 8888 # Arbitrary non-privileged port

class UDPSocket():

    def __init__(self, port=PORT):
        try:
            self.dq = collections.deque(maxlen=100)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.setblocking(0)
            self.port = int(port)
        except socket.error, msg :
            err =  'Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            raise socket.error(err)

        try:
             self.s.bind((HOST, self.port))
        except socket.error , msg:
            err =  'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            raise Exception(GetException())

        Log.logEvent('UDP OPEN PORT {0}'.format(port), meta={})


    def poll(self):
        try:
            data,address = self.s.recvfrom(25)
            self.dq.append(data)
            print data

        except IndexError:  #Don't think this exception gets thrown when queue is full (by testing)
            print GetException()

        except socket.error, msg:
            pass

        except Exception as e:
            print GetException()

        try:
            c = self.dq.popleft()
        except IndexError:
            c = None

        return c
