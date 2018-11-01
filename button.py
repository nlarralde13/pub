import RPi.GPIO as GPIO
from myserial import MySerial
from utils import GetException
from log import Log


OPEN = 0
CLOSED = 1
IDLE = 0
PRESSED=1
ACTIVE=2
UNPRESSED=3

DEBUG_OK = True

#Physical button input/output
class Button_GPIO:
    def __init__(self, bid, direction=GPIO.IN):

        Log.logEvent('PB OPEN {0} {1}'.format(bid, direction), meta={})

        self.bid = int(bid)
        self.direction = direction
        self.debug = False
        self.init = False

        #Set board pin numbering system
        GPIO.setmode(GPIO.BOARD)

        #Create the file descriptor
        if direction == GPIO.IN:
            GPIO.setup(self.bid, GPIO.IN)
        else:
            GPIO.setup(self.bid, GPIO.OUT)

        self.init = True

    def get(self):
        try:
            if self.debug == True:
                return self.debugValue
            elif self.init:
                value = GPIO.input(self.bid)
        except Exception, msg:
            print GetException()

    def set(self,value):
        try:
            if self.init:
                if value == 0:
                    GPIO.output(self.bid, GPIO.LOW)
                else:
                    GPIO.output(self.bid, GPIO.HIGH)

        except Exception, msg:
            print GetException()


    def setDebug(self,debug, value):
        if DEBUG_OK:
            self.debug = debug
            self.debugValue = value

    def close(self):
        self.init = False



class Button_RS232:
    def __init__(self, interface, bid):
        try:
            Log.logEvent('RS232 OPEN {0}'.format(bid),  meta={})
            self.serial = MySerial(interface)
            self.serial.dtr(1)
            self.bid = bid
            self.direction = GPIO.IN
            self.debug = False
            self.init = True
        except Exception, msg:
            raise Exception(GetException())


    def get(self):
        try:
            if self.debug == True:
                return self.debugValue
            elif self.init:
                cnt = 0
                for loop in range(0,5):
                    if self.serial.get(self.bid):
                        cnt = cnt + 1
                if cnt < 3:
                    return 0
                else:
                    return 1

        except Exception, msg:
            print GetException()

    def set(self,value):
        try:
            if self.init:
                self.serial.set(self.bid, value)

        except Exception, msg:
            msg = GetException()
            raise Exception(msg)


    def setDebug(self,debug, value):
        if DEBUG_OK:
            self.debug = debug
            self.debugValue = value

    def close(self):
        self.init = False




class Button:

    def __init__(self, interfaceList, iopin='', actionOpen='', actionClose='', index='',  debounce=0, now=0):
            try:
                #Split the button ID into an interface and an id
                type = iopin.split('_')

                if type[0].upper() == 'GPIO':
                    self.io = Button_GPIO(type[1])

                #check for RS232 interface
                #Format of the intrace list is
                # Interface type, interface name, path to device
                for iface in interfaceList:
                    if iface[0].upper() == 'RS232':
                        if iface[1].upper() == type[0].upper():
                            self.io = Button_RS232(iface[2], type[1])
                            break
                else:
                    raise Exception('BAD IO TYPE ' + iopin)

                self.id = iopin
                self.actionClose = actionClose
                self.actionOpen = actionOpen
                self.index = index
                self.debounce = debounce
                self.pressedTS = 0
                self.lastTS =  now              #Timestamp of last state
                if self.io.get() == OPEN:
                    self.status = IDLE
                else:
                    self.status = ACTIVE
                self.debug = False
                Log.logEvent("BUTTON OPEN - ", meta={'index':index,
                             'actionClose': actionClose, 'actionOpen': actionOpen, 'iopin':iopin} )

            except Exception, msg:
                print msg
                raise Exception(msg)

    def setDebug(self,debug, value):
        self.io.setDebug(debug,value)
        self.debug = debug


    def pressedTime(self):
        value = 0
        if self.status == ACTIVE:
            value = self.pressedTS
        return value


    def updateStatus(self, newStatus, now):
        self.status = newStatus
        self.lastTS = now

        if newStatus == ACTIVE:
            self.pressedTS = now

        if self.debug:
            print self.lookup(newStatus),'   ',now



    def poll(self, now):

        value = IDLE
        new = self.io.get()

        if self.status == IDLE:
            if new == CLOSED:
                self.updateStatus(PRESSED, now)
            else:
                self.updateStatus(IDLE,now)

        elif self.status == PRESSED:
            if new == OPEN:
                self.updateStatus(IDLE, now)

            if (now - self.lastTS) >= self.debounce:
                self.updateStatus(ACTIVE,now)
                value = PRESSED
                print self.id,'pressed'

        elif self.status == ACTIVE:
            value = ACTIVE
            if new == CLOSED:
                self.updateStatus(ACTIVE, now)
            else:
                if (now - self.lastTS) >= self.debounce:
                    self.updateStatus(IDLE, now)
                    print self.id, 'unpressed'
                    value = UNPRESSED

        return value


    def lookup(self,value):
        try:
            lutable =  { IDLE:'IDLE',  PRESSED:'PRESSED', ACTIVE:'ACTIVE', UNPRESSED:'UNPRESSED'}
            return lutable[int(value)]

        except Exception as e:
            print e
            return 'ERROR'


    def reset(self):
        self.updateStatus(IDLE,0)



