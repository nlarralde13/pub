import os
import ast
import time
import ConfigParser
import json
from decimal import Decimal

from log import Log
from button import Button, PRESSED, UNPRESSED
from slicer import Slicer
from mysocket import UDPSocket
from utils import GetException, isRunningInPyCharm

from myserial import MySerial


class Config:



    params =  {      #Set up default config values
        'PUB' : '1',
        'VERSION' : 'Pub Version 0.1  April 15, 2016',
        'UDPPORT' : '1895',
        'WEBSERVER' : '',
        'MINPODTIME' : '10',        #Default value
        'MAXPODTIME' : '30',       #Default value
    }

    @classmethod
    def readConfig(cls):
            cfgJson = {}
            name = 'default.cfg'
            section = 'pub'
            mydir = os.path.dirname(os.path.realpath(__file__))
            fname = os.path.join( mydir, name)
            cfg = ConfigParser.SafeConfigParser()
            cfg.readfp(open(fname))
            try:
                for item in cfg.items(section):
                    cls.params[item[0].upper()] = item[1]
            except Exception, msg:
                Log.logError(msg)

            for i in cls.params:
                cfgJson[i] = cls.params[i]

            with open('default.json', 'w') as outfile:
                json.dump(cfgJson, outfile, indent=4)

    @classmethod
    def get(cls, key):
        try:
            if key.upper() == 'IOMAP' or key.upper()=='INTERFACE' or key.upper()=='BUTTONMAP':
                value = ast.literal_eval(cls.params[key.upper()])
            else:
                value = str(cls.params[key.upper()]).upper()

            return value

        except Exception, msg:
            Log.logError(msg)
            return None

    @classmethod
    def buttonLookup(cls, c):

        if str(c) == 'A':
            return 'POD_ABORT'

        buttonMap = cls.get('BUTTONMAP')
        action = None
        for button in buttonMap:
            if str(c[0]) == str(button[0]):
                if c[1].upper() == 'C':
                    action = button[1]
                    break
                if c[1].upper() == 'O':
                    action = button[2]
                    break

        return action





class Pub:

    def __init__(self):
        self.buttonList = []
        self.udpInit()
        self.slicerInit()
        self.pbInit()


    def udpInit(self):
        self.udpsocket = UDPSocket(port=Config.get('UDPPORT'))


    def pbInit(self):
        #First we delete the old list
        del self.buttonList[:]

        interfaceList = Config.get('INTERFACE')
        ioMap = Config.get('IOMAP')
        buttonMap = Config.get('BUTTONMAP')
        debouncetime = Decimal(Config.get('DEBOUNCETIME'))

        try:
            for item in ioMap:
                if isRunningInPyCharm:
                    print 'Configure ',item

                index = item[0]
                iopin = item[1]
                actionOpen = None
                actionClose = None

                #Find the action associated with the pin
                for action in buttonMap:
                    if index == action[0]:
                        actionClose = action[1]
                        actionOpen = action[2]
                        break

                button = Button(interfaceList, iopin=iopin, actionOpen=actionOpen, actionClose=actionClose, index=index,
                                debounce=Decimal(debouncetime))
                self.buttonList.append(button)
        except:
            pass

    def setSlicerConfig(self, now):
        self.slicer.setConfig(now,Config.get('SLICER_IP'),
                     Config.get('SLICER_PORT'),
                     Config.get('SLICER_AUTH_REQD'),
                     Config.get('SLICER_KEY'),
                     int(Config.get('MINPODTIME')),
                     int(Config.get('MAXPODTIME')),
                     int(Config.get('ENCDELAY')),
                     Config.get('BOUNDARYTYPE')
                     )


    def slicerInit(self):
        now = time.time()
        self.slicer = Slicer()
        self.slicer.setPingTime(now=now, interval=60, timeout=3600)
        self.setSlicerConfig(now)
        self.slicer.run()
        time.sleep(1)   #Wait for threads to start up


    def pbPoll(self, now):
        try:
            for button in self.buttonList:
                status = button.poll(now)
                if status == PRESSED :
                    print 'button pressed'
                    Log.logEvent('BUTTON_PRESS', meta={'index': button.index, 'action':button.actionClose, 'type':'IO'})
                    self.slicer.processAction(button.actionClose, now, type='IO')

                if status == UNPRESSED :
                    print 'button unpressed'
                    Log.logEvent('BUTTON_UNPRESS', meta={'index': button.index, 'action':button.actionOpen, 'type':'IO'})
                    self.slicer.processAction(button.actionOpen, now, type='IO')


        except Exception:
            Log.logError(GetException())


    def udpPoll(self, now):
        try:
            c = self.udpsocket.poll()
            if c != None:
                Log.logEvent('UDP_INPUT ', meta={'value': c})


                if c[0] in '123456789A':
                    if Config.get('UDPRELAY') == 'TRUE':
                        action = Config.buttonLookup(c)
                        print action, "fucntion pressed"
                        if action != None:
                            self.slicer.processAction(action, now, type='MAN')

                elif c == 'R':
                    print "Restart request..."
                    Log.logEvent('RESTART', meta={'type':'MANUAL'})

                elif c == 'C':
                    Log.logEvent('REQ_CONFIG', meta={'type':'MANUAL'})
                    Config.readConfig()
                    self.pbInit()
                    self.setSlicerConfig(now)

        except Exception:
                Log.logError(GetException())



    def slicerPoll(self, now):
        try:
            self.slicer.poll(now)

        except Exception:
            Log.logError(GetException())


    def poll(self, now):
        self.pbPoll(now)
        self.udpPoll(now)
        self.slicerPoll(now)



def main():
    try:
        Log.init()

        Log.logEvent('SYSTEM START ' + Config.get('version'))
        Config.readConfig()
        pub = Pub()

    except Exception:
        msg = GetException()
        Log.logCritical(msg)
        print msg
        exit(86)

    Log.logEvent('RUNNING', meta={})

    while True:
        try:

            now = time.time()
            pub.poll(now)

        except Exception, msg:
            Log.logError(msg)

        time.sleep(.010)


if __name__ == "__main__":
    main()
