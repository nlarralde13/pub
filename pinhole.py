# Socket server in python using select function

import socket, select
import time

REG_LIST = {}



class pinHoleServer(object):

    def __init__(self, tcpPort=1896, udpPort=1895, recvBufSize=128):
        self.udpCount = 0
        self.tcpPort = tcpPort
        self.udpPort = udpPort
        self.recvBufSize = recvBufSize
        self.REG_LIST = {}
        self.CONNECTION_LIST = []    # list of socket clients
        self.CLIENT_LIST = {}


    def udp_echo(self, address, data='PH'):
        print address
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto( str(self.udpCount), address)
        self.udpCount = self.udpCount + 1

    def response(self, sock, data):
        sock.send(data)


    def parseCmd(self, sock, data):
        data = data.replace('\r', '').replace('\n', '')
        v = data.split(' ')

        #Convert all values to upper case
        v = [x.upper() for x in v]

        resp = ""
        peerName = sock.getpeername()

        if v[0] == 'REG':
            try:
                if self.REG_LIST[v[1]]['REG'][0] == peerName[0]:
                    resp = "OK:RE-REGISTER"
                else:
                    self.response(sock, "ERR:ALREADY ASSIGNED")

            except:
                self.REG_LIST[v[1]] = {}
                self.REG_LIST[v[1]]['REG'] = peerName
                resp = "OK"


        if v[0] == 'CON':
            try:
                if self.REG_LIST[v[1]]:
                    try:
                        if self.REG_LIST[v[1]]['CON'] == peerName:
                            #Send response as OK
                            resp = "OK:ALREADY CONNECTED"
                        else:
                            #Send response as error
                           resp = "ERR:CONNECTED TO ANOTHER DEVICE"

                    except:
                        self.REG_LIST[v[1]]['CON'] = peerName
                        resp = "OK:ACCEPTED"
            except:
                resp = "ERR:NO SUCH REG"


        if v[0] == "IP":
            try:
                if self.REG_LIST[v[1]]['REG'][0] == peerName[0]:
                    resp = "OK:CON=" + str(self.REG_LIST[v[1]]['CON'][0])
                elif self.REG_LIST[v[1]]['CON'][0] == peerName[0]:
                    resp = "OK:REG=" + str(self.REG_LIST[v[1]]['REG'][0])

            except Exception as e:
                print e
                resp = "ERR:NO SUCH REG/CON"

        return resp


    def addConnection(self, sock):
        self.CONNECTION_LIST.append(sock)
        print "Client (%s, %s) connected" % sock.getpeername()


    def delConnection(self, sock):

        self.CONNECTION_LIST.remove(sock)
        address = sock.getpeername()
        sock.close()

        for r in self.REG_LIST:

            print r

            try:
                if self.REG_LIST[r]['REG'] == address:
                    print "Deleting REG_LIST entry %s " % r
                    self.REG_LIST.pop(r)
                    break

                else:
                    if self.REG_LIST[r]['CON'] == address:
                        print "Removing %s %s from REG_LIST CON" % address
                        break

            except:
                pass



    def open(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # this has no effect, why ?
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.tcpPort))
        self.server_socket.listen(10)

        # Add server socket to the list of readable connections
        self.CONNECTION_LIST.append(self.server_socket)

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.udp_socket.bind(("0.0.0.0", self.udpPort))

        # Add UDP listener to our list of connections
        self.CONNECTION_LIST.append(self.udp_socket)

        print "Chat server started on port " + str(self.tcpPort)


    def process(self):
        # Get the list sockets which are ready to be read through select
        read_sockets,write_sockets,error_sockets = select.select(self.CONNECTION_LIST,[],[])

        for sock in read_sockets:

            #New connection
            if sock == self.server_socket:
                # Handle the case in which there is a new connection recieved through server_socket
                sockfd, addr = self.server_socket.accept()
                self.addConnection(sockfd)




            #Some incoming message from a client
            else:
                # Data recieved from client, process it
                try:
                    #In Windows, sometimes when a TCP program closes abruptly,
                    # a "Connection reset by peer" exception will be thrown
                    data, address = sock.recvfrom(self.recvBufSize)
                    if len(data) == 0:
                        raise

                    if sock.type == socket.SOCK_DGRAM:
                        print "UDP",data,address
                        self.udp_echo(address,data)

                        # echo back the client message
                    if sock.type == socket.SOCK_STREAM:
                        if data:
                            resp = self.parseCmd(sock, data)
                            sock.send(resp)

                # client disconnected, so remove from socket list
                except Exception as e:
                    print e
 #                   broadcast_data(sock, "Client (%s, %s) is offline" % addr)
                    address = sock.getpeername()
                    print "Client (%s %s) is offline" % address
                    self.delConnection(sock)
                    continue


    def close(self):
        self.server_socket.close()





class pinHoleClient(object):

    def __init__(self, tcpPort=1896, udpPort=1895):
        self.tcpPort = tcpPort
        self.udpPort = udpPort
        self.registered = False

    def udpOpenPinhole(self):
        status = False
        try:
            dest = self.sock.getpeername()

            qdest = (dest[0], self.udpPort)


            print dest
            udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            for cnt in range(0, 5):
                udpsock.sendto( "open"+ str(cnt), (dest[0], self.udpPort) )
                if len(self.getResponse(udpsock)):
                    time.sleep(.1)
                    status = True

        except Exception as e:
            pass

        return status




    @classmethod
    def registerClient(cls, address):
        pass

    @classmethod
    def keepalive(cls, address):
        pass

    def getResponse(self,sock):
        try:
            response = ''
            sock.setblocking(0)
            ready = select.select([sock], [], [], 2)
            if ready[0]:
                response = sock.recv(4096)
        except:
            raise

        return response

    def sendCmd(self, cmd):
        try:
            response = ''
            self.sock.send(cmd)
            response = self.getResponse(self.sock)

        except Exception as e:
            print e
            pass

        return response


    def open(self, host):
        #create an INET, STREAMing socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            #now connect to the web server
            sock.connect((host, self.tcpPort))
            self.sock = sock
        except:
            print 'Could not connect to ', host


    def register(self, name):
        self.registered = False

        resp = self.sendCmd('REG ' + str(name).upper() )
        if resp == "OK":
            self.registered = self.udpOpenPinhole()



    def connect(self, name):
        self.connected = False

        resp = self.sendCmd('CON ' + str(name).upper() )
        respv = resp.split('=')
        if respv[0] == "OK":
            ph = respv[1].split(':')
            self.pinHole = ( str(ph[0]), str(ph[1]) )
#            self.udpOpenPinhole()

            self.connected = True



    def close(self):
        try:
            self.sock.close()
        except:
            pass


    def sendPinhole(self):

        a=0
        udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
#        udpsock.bind(('0.0.0.0', int(self.pinHole[1])) )
        while True:
            address = (self.pinHole[0], int(self.pinHole[1]) )
            udpsock.sendto( "relay " + str(a), address )
            a = a+1

            time.sleep(1)










if __name__ == "__main__":

    ph = pinHoleClient()

    ph.open('requestion.net')

    ph.connect('Slicer123')

    ph.sendPinhole()



#    phServer = pinHoleServer()

#    phServer.open()
#    while 1:
#        phServer.process()

