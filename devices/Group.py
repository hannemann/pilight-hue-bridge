import time

class Group(object):

    def __init__(self, daemon, group):
        self.daemon = daemon
        self.hue = daemon.hue
        self.name = group.name
        self.lights = group.lights
        self.hueGroup = group
        self.groupId = group.group_id
        self._state = 'on' if group.on else 'off'
        
        self.scenes = {}
        self.lightIds = frozenset(light.light_id for light in self.lights)
        
    def hasLights(self, lights):
        return len(self.lights) == len(self.lightIds.intersection(lights))
    
    def addScene(self, name, scene):
        self.scenes[name] = scene;
        
    def hasScene(self, name):
        return name in self.scenes
    
    def getScene(self, name):
        if self.hasScene(name):
            return self.scenes[name]
        
        return None
    
    @property
    def state(self):
        return self._state
    
    @state.setter
    def state(self, value):
        if value in ['on', 'off'] and self.state != value:
            self._state = value
            self.hue.bridge.set_group(self.groupId, 'on', value == 'on')
    
    def activateScene(self, name):
        scene = self.getScene(name)
        if scene is not None:
            activate = scene.name
            for scene in self.scenes:
                if scene == activate:
                    self.scenes[scene].state = 'on'
                else:
                    self.scenes[scene].state = 'off'
                    
                    
    def dim(self, device, dimlevel):
        
        if dimlevel == 0:
            message = {
                "action":"control",
                "code":{
                    "device":device,
                    "state":"off"
                }
            }
            self.daemon.pilight.sendMessage(message)        
        
        param = {
            "bri": dimlevel if dimlevel > 0 else 1
        }
        
        state = 'on' if dimlevel > 0 else 'off'
        if state != self.state:
            param['on'] = state == 'on'
            
        self._state = state
        self.hue.bridge.set_group(self.groupId, param)
        
        
        
        
        
    