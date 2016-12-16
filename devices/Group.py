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
    
    def has_active_scene(self, name=False):
        """ determine if group has active scene """
        return True if name and self.activeScene.name == name else self.activeScene is not None
    
    def add_light(self, name, light):
        """ add light """
        self.lights[name] = light
        if light.pilightDevice is not None:
            light.register_dimlevel_callback(self.light_dimmmed)
            light.register_state_callback(self.light_switched)
        
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
            self.set_average_dependent_dimlevels(dimlevel)\
                .update_pilight_device(dimlevel)
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
            
    def sync_active_scene(self):
        """ synchronize active scene """
        if self.lock_sync_scene is True:
            return

        logger.debug('CHECK SCENE: fetch lights from bridge')
        lights = self.daemon.hue.bridge.get_light()

        if self.has_active_scene() and self.activeScene.is_active(lights):
            logger.debug('CHECK SCENE: current active scene remains active')
            return           
            
        self.activeScene = None
        for scene in self.scenes.values():
            if scene.is_active(lights):
                logger.debug('CHECK SCENE: activating scene {}'.format(scene.name))
                self.activate_scene(scene.name)
                break
            else:
                if scene.state == 'on':
                    logger.debug('CHECK SCENE: switching scene {} off'.format(scene.name))
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

    def sync_with_pilight(self):
        """ synchronize hue devices with pilight devices """
        for scene in self.scenes.values():
            if scene.state == 'on':
                self.activeScene = scene
                break

        if self.has_active_scene():
            self.activeScene.state = 'on'
            self.lock_set_average = True
            self.sync_pilight_lights_with_scene()
            self.lock_set_average = False

        for light in self.lights.values():
            light.sync()

        self.set_light_average()

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

    def light_dimmmed(self, e):
        """ callback if dimlevel has changed """
        if e.action and self.has_light(e.origin.name):
            if self.lock_set_average is False:
                self.set_light_average()
            if self.lock_sync_scene is False:
                self.sync_active_scene()

    def light_switched(self, e):
        """ callback if state has changed """
        if e.action and self.has_light(e.origin.name):
            if self.lock_sync_scene is False:
                self.sync_active_scene()

    def set_light_average(self):
        """ get average and update pilight device """
        self.lock_set_average = True
        if self.pilightDevice is not None:
            avg = int(self.get_average_dimlevel())
            if self.pilightDevice.dimlevel != avg:
                self._dimlevel = None
                self.update_pilight_device(avg)
        self.lock_set_average = False

    def get_average_dimlevel(self):
        """
         retrieve average dimlevel
        :return: float
        """
        lights = self.lights.values()
        dimlevels = [l.dimlevel for l in lights if l.dimlevel is not None]
        a = math.fsum(dimlevels) / len(lights)
        return round(a)

    def set_average_dependent_dimlevels(self, dimlevel):
        """
        compute dimlevels for lights in group if
        mimics behaviour of app
        """
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

        return self

    def log_performance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
