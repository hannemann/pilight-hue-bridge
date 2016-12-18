#!/usr/bin/env python

import os
import sys
import getopt
import time
import signal
import json
from threading import Lock
from Pilight import Pilight
from HueSender import HueSender
from devices.Devices import Devices
import logging

logFormat = '%(asctime)s %(name)s\t%(levelname)s:\t'
logFormat += '%(message)s, (%(module)s, %(lineno)d)'

logging.basicConfig(level=logging.ERROR, format=logFormat)
logger = logging.getLogger('daemon')


class PilightHueBridge(object):
    
    terminate = False
    modules = ['Pilight', 'HueSender']
    devicesInitialized = False
    
    def __init__(self, debugmode=False):
        self.logging = {"mode": "d", "d-level": logging.INFO}
        self.init_logging(debugmode)
        self.pilight = Pilight(self, 5)
        self.hue = HueSender(self)
        self.devices = Devices(self)
        self.lock = Lock()
        logger.info('Daemon initialized')
        
    def init_logging(self, debugmode):
        
        if debugmode is not False:
            if '-' in debugmode:
                mode, levels = debugmode.split('-')
            else:
                mode = debugmode
                levels = 'info'
            
            if ':' in levels:
                levels = levels.split(':')
            else:
                levels = [levels]
            
            level = logging.INFO
            for i, m in enumerate(mode):
                if i < len(levels):
                    level = levels[i].upper()
                    if hasattr(logging, level):
                        level = getattr(logging, level)
                self.logging[m + '-level'] = level
                
            self.logging['mode'] = str(mode)

        logger.setLevel(self.logging['d-level'])
        
    def update_devices(self, module):
        
        if self.devicesInitialized is False:
            
            if 'Pilight' in self.modules and isinstance(module, Pilight):
                self.modules.remove('Pilight')
            elif 'HueSender' in self.modules and isinstance(module, HueSender):
                self.modules.remove('HueSender')
                
            if len(self.modules) == 0:
                self.devices.init_devices()
                self.devicesInitialized = True
        else:
            self.lock.acquire()
            self.devices.update_devices(module)
            self.lock.release()
        
    def proxy_update(self, update):
        self.lock.acquire()
        self.devices.update(update)
        self.lock.release()
        
    @staticmethod
    def dump_json(obj):
        print(
            json.dumps(
                obj,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
            )
        )

    def run(self):
        logger.info('Daemon PID: %s' % os.getpid())
        self.pilight.start()
        self.hue.start()
        while True:
            if self.terminate:
                logger.info('Terminated')
                break
            
            time.sleep(2)    
             
    def shutdown(self):
        logger.info('Catched SIGTERM')
        self.pilight.shutdown()
        self.hue.shutdown()
        self.terminate = True   


def usage():
    """ print help message """
    print '\n\tUsage:\n'
    print '\t\t-h\tHelp'
    print '\t\t-d\tDebugmode: modes and levels seperated by -, levels seperated by :'
    print '\t\t\tmodes: d=main program, a=hue api, p=pilight, h=hue'
    print '\t\t\tlevels: debug, info, warning, error, critical'
    print '\t\t\te.g.:\t-d dpa-debug:info to set debug on main program'
    print '\t\t\t\tinfo on pilight and info on hue api (because explicit level on a is omitted)'
    
if __name__ == "__main__":
    debug = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit(0)
        if opt == '-d':
            debug = arg
    
    bridge = PilightHueBridge(debug)
    signal.signal(signal.SIGTERM, bridge.shutdown)
    bridge.run()
