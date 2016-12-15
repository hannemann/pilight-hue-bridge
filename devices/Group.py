import time
from Dimmable import Dimmable
import logging

logger = logging.getLogger('daemon')


class Group(Dimmable):
    
    perfomanceLogging = False
    
    lightName = 'all'

    def __init__(self, daemon, hue, hue_values):
        """ initialize """
        self.log_performance('GET init group')
        Dimmable.__init__(self, daemon, hue, hue_values)
        self.scenes = {}
        self.lights = {}
        self.activeScene = None
        self.groupId = hue.group_id
        self.id = self.groupId
        self.groupName = self.name
        self.type = 'group'
        self.init_pilight_device()
        self.log_performance('GET init group end')
        
    def has_lights(self, lights):
        """ has lights """
        lights_set = frozenset(light.hue.light_id for light in self.lights.values())
        return len(self.lights) == len(lights_set.intersection(lights))
    
    def add_scene(self, name, scene):
        """ add scene """
        self.scenes[name] = scene
        
    def has_scene(self, name):
        """ has scene """
        return name in self.scenes
    
    def get_scene(self, name):
        """ retrieve scene """
        if self.has_scene(name):
            return self.scenes[name]
        
        return None
    
    def has_active_scene(self):
        """ determine if group has active scene """
        
        return self.activeScene is not None
    
    def add_light(self, name, light):
        """ add light """
        self.lights[name] = light
        
    def has_light(self, name):
        """ has light """
        return name in self.lights
    
    def get_light(self, name):
        """ retrieve light """
        if self.has_light(name):
            return self.lights[name]
        
        return None
    
    def activate_scene(self, name):
        """ activate scene """
        scene = self.get_scene(name)
        if scene is not None:
            self._state = 'on'
            scene.state = 'on'
            self.activeScene = scene
            for scene in self.scenes:
                if scene != name:
                    self.scenes[scene].state = 'off'
                    time.sleep(.2)
                    
            self.sync_pilight_lights_with_scene()
            
    def sync_active_scene(self, lights):
        """ synchronize active scene """
        if self.has_active_scene() and self.activeScene.isActive(self, lights):
            logger.debug('current active scene remains active')
            return           
            
        self.activeScene = None
        for scene in self.scenes.values():
            if scene.isActive(self, lights):
                logger.debug('activating scene {}'.format(scene.name))
                self.activate_scene(scene.name)
                break
            else:
                logger.debug('switching scene {} off'.format(scene.name))
                scene.state = 'off'
                
    def sync_lights(self, lights, group):
        """ synchronize pilight lights with hue lights """
        for lightId in lights:
            light = lights[lightId]
            name = light['name']
            if self.has_light(name):
                update_light = self.lights[name]
                state = 'on' if light['state']['on'] is True else 'off'
                dimlevel = light['state']['bri']
                logger.debug('{}: {} -> {}, {}'.format(lightId, update_light.name, state, dimlevel))
                if 'on' == state:
                    update_light.dimlevel = dimlevel
                else:
                    update_light.state = state

    @Dimmable.dimlevel.setter
    def dimlevel(self, dimlevel):
        """ dim hue device """
        Dimmable.dimlevel.fset(self, dimlevel)
        self.sync_lights_with_group()
            
    def sync_lights_with_group(self):
        """ synchronize lights with group device """
        for light in self.lights.values():
            light.bri = self.dimlevel
            light._state = 'on' if self.dimlevel > 0 else 'off'
            light.update_pilight_device(self.dimlevel)
            
    def sync_pilight_lights_with_scene(self):
        """ synchronize pilight devices with light states """
        states = self.activeScene.lightStates
        
        for light in self.lights.values():
            logger.debug('Light {} {}: Updating pilightDevice'.format(self.name, light.name))
            time.sleep(0.1)
            state = states[str(light.hue.light_id)]
            dimlevel = state['bri'] if state['on'] is True else 0
            light._state = 'on' if state['on'] is True else 'off'
            light.bri = dimlevel
            logger.debug(
                'Set light {} {}: bri={}, state={}'.format(self.name, light.name, str(light.bri), light._state)
            )
            light.update_pilight_device(dimlevel)

    def sync_with_pilight(self):
        """ synchronize hue devices with pilight devices """
        for scene in self.scenes.values():
            if scene.state == 'on':
                self.activeScene = scene
                break
                
        if self.has_active_scene():
            self.activeScene.state = 'on'
        elif self.pilightDevice is not None:
            self.sync()
            self.sync_lights_with_group()
        else:
            for light in self.lights.values():
                light.sync()
    
    def log_performance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
