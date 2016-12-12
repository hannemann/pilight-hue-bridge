import time

class Group(object):

    def __init__(self, daemon, group):
        self.lock = False
        self.daemon = daemon
        self.hue = daemon.hue
        self.name = group.name
        self.lights = group.lights
        self.hueGroup = group
        self.groupId = group.group_id
        
        self._state = 'on' if group.on else 'off'
        
        hueValues = self.hue.bridge.get_group(self.groupId)
        self.bri = hueValues['action']['bri']
        self.dimmerDeviceName = 'hue_group_' + self.name + '_all_bri'
        self.dimmer = None
        self.dimlevel = None
        if self.dimmerDeviceName in self.daemon.pilight.devices:
            self.dimmer = self.daemon.pilight.devices[self.dimmerDeviceName]
            self.dimlevel = self.dimmer['dimlevel']
            if self.dimlevel != self.bri or self.dimmer['state'] != self.state:
                self.state = self.dimmer['state']
                self.sync()
                
        self.scenes = {}
        self.activeScene = None
        self.lightIds = frozenset(light.light_id for light in self.lights)
        
    def hasLights(self, lights):
        """ has lights
        """
        return len(self.lights) == len(self.lightIds.intersection(lights))
    
    def addScene(self, name, scene):
        """ add scene
        """
        self.scenes[name] = scene;
        
    def hasScene(self, name):
        """ has scene
        """
        return name in self.scenes
    
    def getScene(self, name):
        """ retrieve scene
        """
        if self.hasScene(name):
            return self.scenes[name]
        return None
    
    @property
    def state(self):
        """ get state
        """
        return self._state
    
    @state.setter
    def state(self, value):
        """ set state
        """
        if self.lock:
            return
        self.lock
        
        if value in ['on', 'off'] and self.state != value:
            self._state = value
            self.hue.bridge.set_group(self.groupId, 'on', value == 'on')
            if 'off' == self._state:
                self._switchPilightDimmerOff() 
        
        self.lock = False           
                
    def sync(self):
        """ synchronize state and dimlevel
        """
        if self.lock:
            return
        self.lock
        
        param = {
            "bri": self.dimlevel if self.dimlevel > 0 else 1,
            "on": self.state == 'on'
        }
        self.hue.bridge.set_group(self.groupId, param)
        
        self.lock = False
        
    def applyHueUpdates(self):
        """ apply updates from hue bridge
        """
        if self.lock:
            return
        self.lock

        if self.dimmer is None:
            return
        
        hueValues = self.hue.bridge.get_group(self.groupId)
        on = 'on' if hueValues['action']['on'] else 'off'
        bri = hueValues['action']['bri']
        
        if on != self.state or bri != self.dimlevel:
            message = {
                "action":"control",
                "code":{
                    "device":self.dimmerDeviceName,
                    "state":on,
                    "values":{
                        "dimlevel":bri
                    }
                }
            }
            self.daemon.pilight.sendMessage(message)
            self.state = on
            self.bri = bri
            self.dimlevel = bri
        
        self.lock = False
    
    def activateScene(self, name):
        """ activate scene
        """
        scene = self.getScene(name)
        if scene is not None:
            activate = scene.name
            for scene in self.scenes:
                if scene == activate:
                    self.scenes[scene].state = 'on'
                    self.activeScene = scene.name
                else:
                    self.scenes[scene].state = 'off'
                    
                    
    def dim(self, dimlevel):
        """ dim hue device
        """
        if self.lock:
            return
        self.lock
        
        if dimlevel == 0:
            self._switchPilightDimmerOff()       
        
        param = {
            "bri": dimlevel if dimlevel > 0 else 1
        }
        
        state = 'on' if dimlevel > 0 else 'off'
        if state != self.state:
            param['on'] = state == 'on'
            
        self.hue.bridge.set_group(self.groupId, param)
        
        self.state = state
        if self.dimmer is not None:
            self.dimmer['dimlevel'] = dimlevel
        self.bri = dimlevel
        
        self.lock = False
    
    def _switchPilightDimmerOff(self):
        """ switch off pilight device
        """
        message = {
            "action":"control",
            "code":{
                "device":self.dimmerDeviceName,
                "state":"off"
            }
        }
        self.daemon.pilight.sendMessage(message)
        
        
        
        
        
    