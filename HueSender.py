#!/usr/bin/python

from phue import Bridge
import logging
from phue import logger as hueLogger

import threading, time
import logging

logger = logging.getLogger('hue')
logger.setLevel(logging.INFO)

class HueSender(threading.Thread):
    
    terminate = False
    daemon = None
    lights = None
    scenes = None
    groups = None

    def __init__(self, daemon):
        threading.Thread.__init__(self, name='hue')
        self.daemon = daemon
        if 'h' in self.daemon.logging['mode']:
            logger.setLevel(self.daemon.logging['h-level'])
        logger.info('hue sender initialized')
        
    def run(self):
        logger.info('starting hue sender')
        if 'a' in self.daemon.logging['mode']:
            hueLogger.setLevel(self.daemon.logging['a-level'])
        self.bridge = Bridge('192.168.3.66', "mzdWB1nVn3A3oiKw4UWriuAN73b6trclfOyBGUFa")
        self.next_update = time.time()
        self.update()
        logger.info('hue connected')
        
    def update(self):
        if self.terminate is False:
            logger.info('fetching updates from bridge')
            self.scenes = self.bridge.scenes
            self.lights = self.bridge.lights
            self.groups = self.bridge.groups
            self.daemon.updateDevices(self)
            self.next_update = self.next_update + 5
            self.updateTimer = threading.Timer( self.next_update - time.time(), self.update )
            self.updateTimer.start()
            
    
    def shutdown(self):
        logger.info("Shutting down hue sender")
        if self.updateTimer is not None:
            self.updateTimer.cancel()
        self.terminate = True
        