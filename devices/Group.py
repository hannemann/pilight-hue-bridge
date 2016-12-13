import time
from Switchable import Switchable
from Dimmable import Dimmable

class Group(Dimmable):

    def __init__(self, daemon, hue):
        """ initialize """
        Dimmable.__init__(self, daemon, hue)
        self.lights = hue.lights
        self.groupId = hue.group_id
        self._state = 'on' if hue.on else 'off'
        
        hueValues = self.hue._get()
        self.bri = hueValues['action']['bri']
        
        self.pilightDeviceName = 'hue_group_' + self.name + '_all_bri'
        self.initPilightDevice()
        if self.pilightDevice is not None:
            self.sync()
        
        self.scenes = {}
        self.activeScene = None
        self.lightIds = frozenset(light.light_id for light in self.lights)
        
        #self.daemon.debug(self.pilightDevice)
        
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
    
    def activateScene(self, name):
        """ activate scene
        """
        scene = self.getScene(name)
        if scene is not None:
            self._state = 'on'
            for scene in self.scenes:
                if scene == name:
                    self.scenes[scene].state = 'on'
                    self.activeScene = name
                else:
                    self.scenes[scene].state = 'off'
                    
        
        
        
        
        
    