#!/usr/bin/python

from phue import Bridge
import threading, time

class HueSender(threading.Thread):
    
    terminate = False
    daemon = None

    def __init__(self, daemon):
        threading.Thread.__init__(self)
        self.daemon = daemon
        
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
            self.lights = self.bridge.lights
            self.groups = self.bridge.groups
            self.next_update = self.next_update + 5
            self.updateTimer = threading.Timer( self.next_update - time.time(), self.update )
            self.updateTimer.start()
            
            
    def processUpdate(self, u):
        device = u['devices'][0]
        parts = device.split('_')
        if parts[0] == 'hue':
            self.parseUpdate(parts, u)
            
    def parseUpdate(self, parts, u):
        
        if parts[1] == 'scene' and u['values']['state'] == 'on':
            self.runScene(parts, u)
            
    def runScene(self, parts, u):
        groups = [x for x in self.groups if x.name == parts[2]]
        scenes = [x for x in self.scenes if x.name == parts[3]]
        if len(groups) > 0 and len(scenes) > 0:
            self.bridge.activate_scene(groups[0].group_id, scenes[0].scene_id)
    
    def shutdown(self):
        self.daemon.emit("Shutting down hue sender")
        if self.updateTimer is not None:
            self.updateTimer.cancel()
        self.terminate = True
        