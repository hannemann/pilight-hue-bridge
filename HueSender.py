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
            self.daemon.debug('run scene')
            self.runScene(parts, u)
        elif parts[1] == 'bri':
            if 'dimlevel' in u['values']:
                self.daemon.debug('Set brightness')
                self.setBrightness(parts, u['values']['dimlevel'])
            else:
                self.daemon.debug('Switch dimmer')
                self.switchDimmer(parts, u['values']['state'])
            
            
    def runScene(self, parts, u):
        groups = [x for x in self.groups if x.name == parts[2]]
        scenes = [x for x in self.scenes if x.name == parts[3]]
        if len(groups) > 0 and len(scenes) > 0:
            self.bridge.activate_scene(groups[0].group_id, scenes[0].scene_id)
    
    def setBrightness(self, parts, dimlevel):
        groups = [x for x in self.groups if x.name == parts[2]]
        lights = [x for x in self.lights if x.name == parts[2]]
        if len(groups) > 0:
            if dimlevel == 0:
                self.switchDimmer(parts, 'off')
            else:
                self.bridge.set_group(groups[0].group_id, 'bri', dimlevel)
                self.switchDimmer(parts, 'on')
        elif len(lights) > 0:
            self.daemon.debug(u)
            self.bridge.set_group(lights[0].light_id, 'bri', u['values']['dimlevel'])
            
    def switchDimmer(self, parts, state):
        groups = [x for x in self.groups if x.name == parts[2]]
        lights = [x for x in self.lights if x.name == parts[2]]

        self.daemon.debug(state)
        
        if len(groups) > 0:
            self.bridge.set_group(groups[0].group_id, 'on', state == 'on')
        elif len(lights) > 0:
            light = lights[0]
            if state == 'off':
                light.on = False
            elif len(parts) == 6:
                
                fromBri = int(parts[3])
                bri = int(parts[4])
                transition = int(parts[5]) 
                
                self.daemon.debug(fromBri)
                self.daemon.debug(bri)
                self.daemon.debug(transition)
                self.daemon.debug(light.light_id)
                
                f = {
                    "on": True,
                    "bri": fromBri
                }
                self.daemon.debug(f)
                
                result = self.bridge.set_light(light.light_id, f)
                self.daemon.debug(result)
                
                time.sleep(.5)
                
                f = {
                    "bri": bri,
                    "transitiontime": transition,
                    "on": bri > 0
                }
                self.daemon.debug(f)
                self.bridge.set_light(light.light_id, f)
            
    
    def shutdown(self):
        self.daemon.emit("Shutting down hue sender")
        if self.updateTimer is not None:
            self.updateTimer.cancel()
        self.terminate = True
        