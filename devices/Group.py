import time
from Dimmable import Dimmable
import logging
import math

logger = logging.getLogger('daemon')


class Group(Dimmable):
    
    perfomanceLogging = False

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
        self.lightName = 'all'
        self.type = 'group'
        self.init_pilight_device()
        self.lock_set_average = False
        self.lock_sync_scene = False
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

    @Dimmable.dimlevel.setter
    def dimlevel(self, dimlevel):
        """ dim group """
        if dimlevel != self.dimlevel:
            if dimlevel > self._dimlevel:
                logger.debug('GROUP: calc factor: f = (254 - {}) / (254 - {})'.format(dimlevel, self._dimlevel))
                f = float((254 - dimlevel)) / float((254 - self._dimlevel))
            else:
                logger.debug('GROUP: calc factor: f = {} / {}'.format(dimlevel, self._dimlevel))
                f = float(dimlevel) / float(self._dimlevel)

            logger.debug('GROUP: factor {}'.format(f))

            self.lock_set_average = True
            for light in self.lights.values():
                if dimlevel > self._dimlevel:
                    dlvl = 254 - (254 - float(light.dimlevel)) * f
                else:
                    dlvl = max(1, float(light.dimlevel)) * f
                light.dimlevel = int(round(dlvl))
            self.lock_set_average = False

            self.update_pilight_device(dimlevel)
        else:
            logger.debug('pilight: {} {} dimlevel {} already applied'.format(self.type, self.name, str(dimlevel)))

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

            self.lock_set_average = True
            self.sync_pilight_lights_with_scene()
            self.lock_set_average = False
            self.set_light_average()
            
    def sync_active_scene(self, lights):
        """ synchronize active scene """
        if self.lock_sync_scene is True:
            return

        if self.has_active_scene() and self.activeScene.is_active(lights):
            logger.debug('current active scene remains active')
            return           
            
        self.activeScene = None
        for scene in self.scenes.values():
            if scene.is_active(lights):
                logger.debug('activating scene {}'.format(scene.name))
                self.activate_scene(scene.name)
                break
            else:
                if scene.state == 'on':
                    logger.debug('switching scene {} off'.format(scene.name))
                    scene.state = 'off'
                
    def sync_with_hue(self, lights, group):
        """ synchronize pilight lights with hue lights """

        for lightId in lights:
            light = lights[lightId]
            name = light['name']
            if self.has_light(name):
                update_light = self.lights[name]
                state = 'on' if light['state']['on'] is True else 'off'
                dimlevel = light['state']['bri']
                # logger.debug('{}: {} -> {}, {}'.format(lightId, update_light.name, state, dimlevel))
                if 'on' == state:
                    update_light.dimlevel = dimlevel
                else:
                    update_light.state = state

        if self.pilightDevice is not None:
            self.dimlevel = int(self.get_average_dimlevel())
            
    def sync_pilight_lights_with_scene(self):
        """ synchronize pilight devices with light states """
        states = self.activeScene.lightStates
        
        for light in self.lights.values():
            logger.debug('SYNCSCENE: {} {}: Updating pilightDevice'.format(self.name, light.name))
            time.sleep(0.1)
            state = states[str(light.hue.light_id)]
            dimlevel = state['bri'] if state['on'] is True else 0
            light._state = 'on' if state['on'] is True else 'off'
            light.bri = dimlevel
            logger.debug(
                'Set pilight attributes: bri={}, state={}'.format(self.name, light.name, str(light.bri), light._state)
            )
            light.update_pilight_device(dimlevel)

    def sync_with_pilight(self):
        """ synchronize hue devices with pilight devices """
        for scene in self.scenes.values():
            if scene.state == 'on':
                self.activeScene = scene
                break

        lights = self.lights.values()

        if self.has_active_scene():
            self.activeScene.state = 'on'

        for light in lights:
            light.sync()

        self.set_light_average()

    def set_light_average(self):
        """ get average and update pilight device """
        if self.pilightDevice is not None and self.lock_set_average is False:
            avg = int(self.get_average_dimlevel())
            if self.pilightDevice['dimlevel'] != avg:
                self._dimlevel = None
                self.update_pilight_device(avg)

    def get_average_dimlevel(self):
        """
         retrieve average dimlevel
        :return: float
        """
        lights = self.lights.values()
        dimlevels = [l.dimlevel for l in lights if l.dimlevel is not None] #  and l.state is 'on'
        a = math.fsum(dimlevels) / len(lights)
        return round(a)

    def log_performance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
