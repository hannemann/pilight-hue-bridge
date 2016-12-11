#!/usr/bin/env python

import os, sys
import time
import signal
import json
from Pilight import Pilight
from HueSender import HueSender

class PilightHueBridge(object):
    
    terminate = False
    
    def __init__(self, debugMode = False):
        self.debugMode = debugMode
        self.pilight = Pilight(self, 5)
        self.hue = HueSender(self)
        print('Daemon initialized')
        
    def proxyUpdate(self, update):
        self.hue.processUpdate(update)
        self.pilight.sender.processUpdate(update)

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

if __name__ == "__main__":
    
    bridge = PilightHueBridge(False)
    signal.signal(signal.SIGTERM, bridge.shutdown)
    bridge.run()