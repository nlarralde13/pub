from log import Log
from log import GetException
from utils import isRunningInPyCharm
import time
import urllib2
import json
import threading
import Queue
from time import strftime, gmtime
#from replace import replaceContent



class slicerThread (threading.Thread):
    def __init__(self, name, inq, outq, url):
        threading.Thread.__init__(self)
        self.name = name
        self.inq = inq
        self.outq = outq
        self.url = url

    def ping(self):
        try:
            response = urllib2.urlopen(self.url)
            status =  json.loads(response.read())
        except Exception, msg:
            status = {}

        self.outq.put(status)


    def run(self):
        print "Starting " + self.name

        while True:
            time.sleep(1)
            if not self.inq.empty():
                item = self.inq.get()

                #Process command from main thread
                if item == 'P':
                    self.ping()



class Slicer():

    def __init__(self):
        self.podStartTS = None
        self.cnonce = 100
        self.setPingTime(interval='disabled')

        self.cmds = {
                'START':  'POST/pod_start',
                'END':    'POST/pod_end',
                'TIME' :  'GET/server_time',
                'BLACKOUT' : 'POST/blackout',
                'CONTENT_START' : 'POST/content_start',
                'BOUNDARY' : 'GET/boundary'

        }


    def run(self):
        try:
        # This starts the slicer sub-threads
            url = self.formatURL(self.cmds['TIME'])
            self.thread_inq = Queue.Queue(25)
            self.thread_outq = Queue.Queue(25)
            self.slicerThread =  slicerThread("slicerThread", self.thread_inq, self.thread_outq, url)
            self.slicerThread.daemon = True
            self.slicerThread.start()
        except Exception, msg:
            Log.logError(GetException())


    def setPingTime(self, now=0, interval=0, timeout=3600):
        self.pingTimeout = timeout

        if str(interval).upper() == 'DISABLED':
            self.pingInterval = -1

        else:
            if interval > 0:
                self.pingInterval = interval

            if now > 0 and self.pingInterval > 0:
                self.pingTime = now + self.pingInterval


    def setConfig(self, now, ipAddr, port, authReqd, key, minPodTime, maxPodTime, encDelay, boundaryType):
        self.ipAddr = ipAddr
        self.port = port
        self.authReqd = authReqd
        self.key = key
        self.minPodTime = int(minPodTime)
        self.maxPodTime = int(maxPodTime)
        self.encDelay = int(encDelay)
        self.boundaryType = boundaryType
        Log.logEvent('SLICER CONFIG {0} {1} {2}'.format(ipAddr, minPodTime, maxPodTime), meta={})
        self.lastGoodPingTS = now

    def podActive(self):
        return (self.podStartTS != None)

    def formatURL(self, url):
            return  self.ipAddr + '/' + url.split('/')[1]

    def sendGet(self, url):
        try:
            response = urllib2.urlopen(self.formatURL(url))
            return json.loads(response.read())
        except Exception, msg:
            raise Exception(str(msg))


    def sendPost(self, url, meta):
        try:
            uri = self.formatURL(url)
            print url
            req = urllib2.Request(uri)
            req.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(req, json.dumps(meta))
            return json.loads(response.read())
        except Exception, msg:
            raise Exception(str(msg))


    def sendCmd(self, url, meta ={}, logit=False ):
        try:
            if url.upper().find('POST') >= 0:
                response = self.sendPost(url, meta)
            elif url.upper().find('GET') >= 0:
                response = self.sendGet(url)

            if logit:
                Log.logEvent('SILICER_CMD', meta={'type':url, 'response': response} )

        except Exception,  msg:
            response = {}
            if logit:
                Log.logError('SLICER_CMD', meta={'type':url, 'errror': str(msg)} )

        return response


    def setIPAddr(self, ipAddr):
        self.ipAddr = ipAddr


    def timeStr(self, now):
        return time.strftime('%H:%M:%S;00', time.localtime(now))


    def startPod(self, now, type='IO', delay=0):

        if isRunningInPyCharm:
            print now, delay, self.timeStr(now), self.timeStr(now+delay)
        body = {"start_timecode": self.timeStr(now + delay)  }
        response = self.sendCmd(self.cmds['START'], meta=body, logit=True)

        #Don't start timer if we got a null response
        if len(response):
            self.podStartTS = now

    '''def slicerState():
        #body = json.dumps({"start_timecode":"11:22:33:44"})
        request = urllib2.urlopen('http://localhost:65009/state')
        response = json.loads(request.read())
        return response['state']'''

    def endPod(self, now, type='IO', delay=0):
        print now, self.timeStr(now), self.timeStr(now+delay)
        body = {"start_timecode": self.timeStr(now + delay) }
        response = self.sendCmd(self.cmds['END'], meta=body, logit=True)
        self.podStartTS = None

    def boundary(self, now, type='IO', delay=0):
        body = {"type": self.boundaryType }
        response = self.sendCmd(self.cmds['BOUNDARY'], meta=body, logit=True)

    def blackout(self, now, type='IO', delay=0):
        body = {"start_timecode": self.timeStr(now + delay) }
        response = self.sendCmd(self.cmds['BLACKOUT'], meta=body, logit=True)

    def content_replace(self, now, type='IO', delay=0):
        replace = replaceContent()
        replace.replace()
        Log.logEvent('CONTENT_REPLACE', meta={'type':'Sent replace content'})

    def content_start(self, now, type='IO', delay=0):
        timeNow = strftime("%A %Y-%m-%d %H:%M:%S")
        slicerState = urllib2.urlopen('http://localhost:65009/state')
        slicerStateResponse = json.loads(slicerState.read())
        newState = slicerStateResponse['state']
        print newState
        if newState != 0:
            #print state()
            body = {"start_timecode": self.timeStr(now + delay) + ":00","title":timeNow}
            response = self.sendCmd(self.cmds['CONTENT_START'], meta=body, logit=True)
        else:
            body = {"start_timecode": self.timeStr(now + delay) }
            response = self.sendCmd(self.cmds['BLACKOUT'], meta=body, logit=True)

    def startStopPod(self, now, type='IO', delay=0):
        if self.podStartTS == None:
            self.startPod(now, type, delay=delay)

        else: #This is a potential end button press
            if (self.podStartTS + self.minPodTime) <= now:
                self.endPod(now, type, delay=delay)
            else:
                print "Not stopping pod, minimum pod time not reached"
                Log.logEvent('STOP_IGNORE', meta={'type':'Min time not reached'})


    def abort(self, now, type='IO', delay=0):
        if self.podActive():
            self.endPod(now, type=type, delay=delay)
        else:
            Log.logEvent('ABORT_IGNORE', meta={'type':type, 'error':'NOT ACTIVE'})


    def pingPoll(self, now):

        try:
            if now > self.pingTime:
                #Send ping now
                self.setPingTime(now=now)
                self.thread_inq.put('P')

            #Do we have a response to process
            if not self.thread_outq.empty():
                response = self.thread_outq.get()

                try:
                    if response['time']:
                        self.lastGoodPingTS = now
                        pass
                except Exception:
                    print now, 'ping failed'
                    if (now - self.lastGoodPingTS) > self.pingTimeout:
                        self.lastGoodPingTS = now
                        Log.logError('SLICER COMMUNCIATION FAILURE - LAST GOOD PING MORE THAN {0} MINUTES AGO'.format(int(self.pingTimeout+59)/60), meta={})

        except Exception, msg:
            print msg
            return



    def poll(self, now):
        if self.podActive():
            if (self.podStartTS + self.maxPodTime) <= now:
                print 'Maximum POD time exceeded'
                self.endPod(now, type="TIMEOUT")

        self.pingPoll(now)


    def processAction(self, action, now, type='IO'):

        action = action.upper()

        if action == 'NONE':
            print 'Action = None, ignored'

        elif action == 'BLACKOUT':
            self.blackout(now, type=type, delay=self.encDelay)

        elif action == 'CONTENT_REPLACE':
            self.content_replace(now, type=type, delay=self.encDelay)

        elif action == 'BOUNDARY':
            self.boundary(now, type=type, delay=self.encDelay)

        elif action == 'POD_START':
            self.startPod(now, type=type, delay=self.encDelay)

        elif action == 'POD_END':
            self.endPod(now, type=type, delay=self.encDelay)

        elif action == 'POD_STARTEND':
            self.startStopPod(now, type=type, delay=self.encDelay)

        elif action == 'POD_ABORT':
            self.abort(now, type=type, delay=self.encDelay)

        elif action == 'CONTENT_START':
            self.content_start(now, type=type, delay=self.encDelay)

        else:
            print 'Action not found', action
            Log.logError('ACTION NOT FOUND "{0}"'.format(action), meta={})
