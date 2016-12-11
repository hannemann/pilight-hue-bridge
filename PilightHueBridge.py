#!/usr/bin/env python

import os, sys
import time
import signal
from PilightReceiver import PilightReceiver
from HueSender import HueSender

class PilightHueBridge(object):
    
    terminate = False
    
    def __init__(self, debugMode = False):
        self.debugMode = debugMode
        self.pilightReceiver = PilightReceiver(self, 5)
        self.hue = HueSender(self)
        print('Initialized')
        
    def proxyUpdate(self, update):
        self.hue.processUpdate(update)
        self.pilightReceiver.processUpdate(update)

    def emit(self, message):
        print(message)

    def debug(self, message):
        if self.debugMode is True:
            self.emit(message)

    def run(self):
        self.emit('Daemon PID: %s' % os.getpid())
        self.pilightReceiver.start()
        self.hue.start()
        while True:
            if self.terminate:
                self.emit('Terminated')
                break
            
            time.sleep(2)    
             
    def shutdown(self, a, b):
        self.emit('Catched SIGTERM')
        self.pilightReceiver.shutdown()
        self.hue.shutdown()
        self.terminate = True   

if __name__ == "__main__":
    
    bridge = PilightHueBridge(True)
    signal.signal(signal.SIGTERM, bridge.shutdown)
    bridge.run()