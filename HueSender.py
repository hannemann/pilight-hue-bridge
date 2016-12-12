#!/usr/bin/python

from phue import Bridge
import threading, time

class HueSender(threading.Thread):
    
    terminate = False
    daemon = None
    lights = None
    scenes = None
    groups = None

    def __init__(self, daemon):
        threading.Thread.__init__(self)
        self.daemon = daemon
        self.daemon.emit('hue sender initialized')
        
    def run(self):
        self.daemon.emit('starting hue sender')
        self.bridge = Bridge('192.168.3.66', "mzdWB1nVn3A3oiKw4UWriuAN73b6trclfOyBGUFa")
        self.next_update = time.time()
        self.update()
        self.daemon.emit('hue connected')
        
    def update(self):
        if self.terminate is False:
            self.daemon.debug('fetching updates from bridge')
            self.scenes = self.bridge.scenes
            self.lights = self.bridge.get_light()
            self.groups = self.bridge.groups
            self.daemon.updateDevices(self)
            self.next_update = self.next_update + 5
            self.updateTimer = threading.Timer( self.next_update - time.time(), self.update )
            self.updateTimer.start()
            
    
    def shutdown(self):
        self.daemon.emit("Shutting down hue sender")
        if self.updateTimer is not None:
            self.updateTimer.cancel()
        self.terminate = True
        