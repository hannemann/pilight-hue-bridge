import time
from Switchable import Switchable
from Dimmable import Dimmable
import logging

logger = logging.getLogger('daemon')

class Group(Dimmable):
    
    perfomanceLogging = False
    
    lightName = 'all'
    type = 'group'

    def __init__(self, daemon, hue, hueValues):
        self.hueValues = hueValues
        """ initialize """
        self.logPerformance('GET init group')
        Dimmable.__init__(self, daemon, hue)
        self.scenes = {}
        self.lights = {}
        self.activeScene = None
        self.groupId = hue.group_id
        self.id = self.groupId
        self.groupName = self.name
        self.initPilightDevice()
        self.logPerformance('GET init group end')
        
    def hasLights(self, lights):
        """ has lights """
        set = frozenset(light.hue.light_id for light in self.lights.values())
        return len(self.lights) == len(set.intersection(lights))
    
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
    
    def hasActiveScene(self):
        """ determine if group has active scene """
        
        return self.activeScene is not None
    
    def addLight(self, name, light):
        """ add light """
        self.lights[name] = light
        
    def hasLight(self, name):
        """ has light """
        return name in self.lights
    
    def getLight(self, name):
        """ retrieve light """
        if self.hasLight(name):
            return self.lights[name]
        
        return None
    
    def activateScene(self, name):
        """ activate scene """
        scene = self.getScene(name)
        if scene is not None:
            self._state = 'on'
            scene.state = 'on'
            self.activeScene = scene
            for scene in self.scenes:
                if scene != name:
                    self.scenes[scene].state = 'off'
                    time.sleep(.2)
                    
            self.syncPilightLightsWithScene()
            
    def syncActiveScene(self, lights):
        """ synchronize active scene """
        if self.hasActiveScene() and self.activeScene.isActive(self, lights):
            #logger.debug('current active scene remains active')
            return           
            
        self.activeScene = None
        for scene in self.scenes.values():
            if scene.isActive(self, lights):
                #logger.debug('activating scene {}'.format(scene.name))
                self.activateScene(scene.name)
                break;
            else:
                #logger.debug('switching scene {} off'.format(scene.name))
                scene.state = 'off'
                
    @Dimmable.dimlevel.setter
    def dimlevel(self, dimlevel):
        """ dim hue device """
        Dimmable.dimlevel.fset(self, dimlevel)
        self.deactivateActiveScene()
        self.syncLightsWithGroup()
            
    def syncLightsWithGroup(self):
        """ synchronize lights with group device """
        for light in self.lights.values():
            light.bri = self.dimlevel
            light._state = 'on' if self.dimlevel > 0 else 'off'
            light.updatePilightDevice(self.dimlevel)
            
    def syncPilightLightsWithScene(self):
        """ synchronize pilight devices with light states """
        """ lightStates example
        {u'1': {u'on': True, u'xy': [0.4871, 0.4892], u'bri': 147}, u'3': {u'on': True, u'xy': [0.6202, 0.3617], u'bri': 253}, u'2': {u'on': True, u'xy': [0.6202, 0.3617], u'bri': 253}, u'5': {u'on': True, u'bri': 1}, u'4': {u'on': True, u'xy': [0.4561, 0.482], u'bri': 109}, u'6': {u'on': True, u'xy': [0.6007, 0.3909], u'bri': 150}, u'9': {u'on': True, u'bri': 33}}
        """
        states = self.activeScene.lightStates
        
        for light in self.lights.values():
            logger.debug('Light {} {}: Updating pilightDevice'.format(self.name, light.name))
            time.sleep(0.1)
            state = states[str(light.hue.light_id)]
            dimlevel = state['bri'] if state['on'] is True else 0
            light._state = 'on' if state['on'] is True else 'off'
            light.bri = dimlevel
            logger.debug('Set light {} {}: bri={}, state={}'.format(self.name, light.name, str(light.bri), light._state))
            light.updatePilightDevice(dimlevel)

    def syncWithPilight(self):
        """ synchronize hue devices with pilight devices """
        for scene in self.scenes.values():
            if scene.state == 'on':
                self.activeScene = scene
                break;
                
        if self.hasActiveScene():
            self.activeScene.state = 'on'
        elif self.pilightDevice is not None:
            self.sync()
            self.syncLightsWithGroup()
        else:
            for light in self.lights.values():
                light.sync()
            
    def syncScene(self):
        """ apply scene """
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
        
        
        
        
        
    