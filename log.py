import json
from utils import GetException
import os
import logging



class Log:
    @staticmethod
    def formatMsg(name, meta):
        try:
            msg = name
            for item in meta:
                msg += '    {0}={1}'.format(item, meta[item])

            meta['event'] = name
            msg += '?' + json.dumps(meta)

        except Exception:
            print GetException()

        return msg

    @staticmethod
    def logEvent(name, meta={}):
        msg = Log.formatMsg(name,meta)
        logging.info(msg)


    @staticmethod
    def logError(name, meta={}):
        msg = Log.formatMsg(name,meta)
        logging.error(msg)


    @staticmethod
    def logCritical(name, meta={}):
        msg = Log.formatMsg(name,meta)
        logging.critical(msg)


    @staticmethod
    def init():
        cwd = os.path.dirname(os.path.realpath(__file__))
        logging.basicConfig(filename=os.path.join(cwd, 'pub.log'), level=logging.NOTSET, format='%(created).2f %(levelname)s:%(message)s')





