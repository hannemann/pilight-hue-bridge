#!/usr/bin/env python

import os, sys, getopt
import time
import signal
import json
from Pilight import Pilight
from HueSender import HueSender
from devices.Devices import Devices

class PilightHueBridge(object):
    
    terminate = False
    modules = ['Pilight', 'HueSender']
    devicesInitialized = False
    
    def __init__(self, debugMode = False):
        self.debugMode = debugMode
        self.pilight = Pilight(self, 5)
        self.hue = HueSender(self)
        self.devices = Devices(self)
        print('Daemon initialized')
        
    def updateDevices(self, module):
        
        if self.devicesInitialized is False:
            
            if isinstance(module, Pilight):
                self.modules.remove('Pilight')
            elif isinstance(module, HueSender):
                self.modules.remove('HueSender')
                
            if len(self.modules) == 0:
                self.devices.initDevices()
                self.devicesInitialized = True
        else:
            self.devices.updateDevices(module)
        
        
    def proxyUpdate(self, update):
        self.hue.processUpdate(update)
        self.pilight.sender.processUpdate(update)
        self.devices.update(update)

    def emit(self, message):
        print(message)

    def debug(self, message):
        if self.debugMode is True:
            self.emit(message)
        
    def dumpJson(self, obj):
        self.debug(
            json.dumps(
                obj,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
            )
        )  

    def run(self):
        self.emit('Daemon PID: %s' % os.getpid())
        self.pilight.start()
        self.hue.start()
        while True:
            if self.terminate:
                self.emit('Terminated')
                break
            
            time.sleep(2)    
             
    def shutdown(self, a, b):
        self.emit('Catched SIGTERM')
        self.pilight.shutdown()
        self.hue.shutdown()
        self.terminate = True   

def usage():
    print '\n\tUsage:\n'
    print '\t\t-h\tHelp'
    print '\t\t-d\tDebugmode'
    
if __name__ == "__main__":
    debug = False
    try:
        opts, args = getopt.getopt(sys.argv[1:],"dh")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit(0)
        if opt == '-d':
            debug = True
            
    bridge = PilightHueBridge(debug)
    signal.signal(signal.SIGTERM, bridge.shutdown)
    bridge.run()