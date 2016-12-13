import time
from Switchable import Switchable
from Dimmable import Dimmable

class Group(Dimmable):
    
    scenes = {}
    activeScene = None
    lightName = 'all'
    type = 'group'

    def __init__(self, daemon, hue):
        """ initialize """
        Dimmable.__init__(self, daemon, hue)
        self.groupId = hue.group_id
        self.groupName = self.name
        self.initPilightDevice()
        #self.daemon.debug(self.pilightDevice)
        
    def hasLights(self, lights):
        """ has lights """
        set = frozenset(light.light_id for light in self.hue.lights)
        return len(self.hue.lights) == len(set.intersection(lights))
    
    def addScene(self, name, scene):
        """ add scene """
        self.scenes[name] = scene;
        
    def hasScene(self, name):
        """ has scene """
        return name in self.scenes
    
    def getScene(self, name):
        """ retrieve scene """
        if self.hasScene(name):
            return self.scenes[name]
        
        return None
    
    def activateScene(self, name):
        """ activate scene """
        scene = self.getScene(name)
        if scene is not None:
            self._state = 'on'
            for scene in self.scenes:
                if scene == name:
                    self.scenes[scene].state = 'on'
                    self.activeScene = name
                else:
                    self.scenes[scene].state = 'off'
                    
        
        
        
        
        
    