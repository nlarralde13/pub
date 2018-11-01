import serial
from utils import GetException

class MySerial():

    def __init__(self, port, timeout=0):
        try:
            self.serial = serial.Serial(port, timeout=timeout)
        except Exception, msg:
            msg = GetException()
            raise Exception(msg)

    def ri(self):
        return int(self.serial.getRI())

    def dcd(self):
        return int(self.serial.getCD())

    def cts(self):
        return int(self.serial.getCTS())

    def dsr(self):
        return int(self.serial.getDSR())

    def dtr(self, v):
        self.serial.setDTR(bool(v&1))

    def rts(self, v):
        self.serial.setRTS(bool(v&1))

    def get(self, bid):
        if bid == 'RI':
            return self.ri()
        elif bid == 'CTS':
            return self.cts()
        elif bid == 'DCD':
            return self.dcd()
        elif bid == 'DSR':
            return self.dsr()
        else:
            raise Exception('Invalid pin ' + bid)


    def set(self, bid, value):
        if bid == 'DTR':
            self.dtr(value)
        elif bid == 'RTS':
            self.rts(value)
        else:
            raise Exception('Invalid pin ' + bid)


