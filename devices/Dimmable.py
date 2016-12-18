from Switchable import Switchable
from pilight.Dimmer import Dimmer as PilightDimmer
from threading import Timer
import math
import time
import logging

logger = logging.getLogger('daemon')


class Dimmable(Switchable):
    
    def __init__(self, daemon, hue_values, hue_id):
        """ initialize """
        Switchable.__init__(self, daemon, hue_values, hue_id)
        self.action = 'dim'
        self.transition_timer = None
        self.transition = None
        self.dimlevel_callbacks = []

    def get_pilight_class(self):
        """ retrieve new pilight device class """
        return PilightDimmer

    @property
    def state(self):
        """ get state """
        return Switchable.state.fget(self)

    @state.setter
    def state(self, state):
        """ set state """
        Switchable.state.fset(self, state)

    @property
    def dimlevel(self):
        """ retrieve dimlevel """
        return self.pilight.dimlevel
    
    @dimlevel.setter
    def dimlevel(self, dimlevel):
        """ dim hue device """
        logger.debug('Dimmimg ' + self.type + ' ' + self.name + ' to dimlevel ' + str(dimlevel))
        self.hue.dimlevel = dimlevel
        self.update_pilight_device(dimlevel)
        Switchable.state.fset(self, 'on' if dimlevel > 0 else 'off')

    def update_pilight_device(self, dimlevel):
        """ update pilight device to reflect hue state """
        action = False
        if self.dimlevel != dimlevel:
            if self.pilight is not None:
                self.pilight.dimlevel = dimlevel
            action = True
        else:
            logger.debug('pilight: {} {} dimlevel {} already applied'.format(self.type, self.name, str(dimlevel)))

        self.dimlevel_callback(action)
        return self
        
    def set_transition(self, config):
        """ apply transition """

        # self.transition = Transition(config, self.pilight, self.hue)
        # self.transition.start()

        if self.transition_timer is not None:
            self.transition_timer.cancel()
        self.state = 'on'
        fr = int(config['fr'])
        to = int(config['to'])
        tt = int(config['transitiontime'])
        self.hue.set_transition(fr, to, tt)
        self.transition_timer = Timer(tt / 10, self.cancel_transition, [config])
        self.transition_timer.start()

    def cancel_transition(self, config):
        """ cancel transition """
        if self.transition_timer is not None:
            self.transition_timer.cancel()
            self.transition_timer = None

        tmp = self.pilight.name
        self.pilight.name = config['pilight_device']
        self.pilight.state = 'off'
        self.pilight.name = tmp
                
    def can_sync(self):
        """ determine if sync is applicable """
        return self.hue.state != self.state or self.hue.dimlevel != self.dimlevel

    def can_modify(self, config):
        """
        determine if dimmable can be modified
        :param config dict
        :return boolean
        """
        return self.state != config['state'] or self.dimlevel != config['dimlevel']

    def get_sync_param(self):
        """ retrieve sync param """
        param = Switchable.get_sync_param(self)
        if param['on']:
            param['bri'] = self.dimlevel if self.dimlevel > 0 else 1
        return param

    def register_dimlevel_callback(self, func):
        self.dimlevel_callbacks.append(func)

    def dimlevel_callback(self, action):
        for func in self.dimlevel_callbacks:
            func(DimlevelEvent(action, self))


class Transition(object):

    def __init__(self, config, pilight, hue):
        self.pilight = pilight
        self.hue = hue
        self.fr = int(config['fr'])
        self.to = int(config['to'])
        self.tt = int(config['transitiontime'])
        self.width = math.fabs(self.to - self.fr)
        self.transition_device = config['pilight_device']
        self.direction = 'brighter' if self.fr < self.to else 'darker'
        self.next_update = None
        self.current = 0
        self.group = self.get_group(config['group'])
        self.step_width = self.init_step_width()
        self.is_canceled = False
        self.update_timer = None

    def start(self):
        self.deactivate_scene()
        self.hue.set_transition(self.fr, self.to, self.tt)
        if self.pilight is not None:
            self.set_dimlevel(self.fr)
            self.next_update = time.time()
            Timer(2, self.update).start()

    def update(self):
        if self.is_canceled:
            return
        self.current += self.step_width
        if self.current < self.width:
            self.update_pilight()
            self.next_update += 2
            self.update_timer = Timer(self.next_update - time.time(), self.update)
            self.update_timer.start()
        else:
            self.end()

    def update_pilight(self):
        if 'brighter' == self.direction:
            self.set_dimlevel(self.pilight.dimlevel + self.step_width)
        else:
            self.set_dimlevel(self.pilight.dimlevel - self.step_width)

    def end(self):
        self.set_dimlevel(self.to)
        tmp = self.pilight.name
        self.pilight.name = self.transition_device
        self.pilight.state = 'off'
        self.pilight.name = tmp

    def cancel(self):
        if self.update_timer is not None:
            self.update_timer.cancel()
        self.is_canceled = True

    def set_dimlevel(self, dimlevel):
        if self.group is not None:
            self.group.lock_light_callbacks()
        self.pilight.dimlevel = dimlevel
        if self.group is not None:
            self.group.release_light_callbacks()

    def init_step_width(self):
        iterations = float(self.tt / 10 / 2)
        width = float(self.width)
        return int(round(math.fabs(width / iterations)))

    def get_group(self, name):
        if name in self.pilight.daemon.devices.groups:
            return self.pilight.daemon.devices.groups[name]
        return None

    def deactivate_scene(self):
        if self.group is not None:
            if self.group.has_active_scene() and str(self.hue.id) in self.group.activeScene.hue.lightStates:
                self.group.deactivate_active_scene()


class DimlevelEvent(object):

    def __init__(self, action, origin):
        self.action = action
        self.origin = origin
