from Switchable import Switchable
from pilight.Dimmer import Dimmer as PilightDimmer
from threading import Timer
import logging

logger = logging.getLogger('daemon')


class Dimmable(Switchable):
    
    def __init__(self, daemon, hue_values, hue_id):
        """ initialize """
        Switchable.__init__(self, daemon, hue_values, hue_id)
        self.bri = self.get_initial_brightness(hue_values)
        self.action = 'bri'
        self.transition_timer = None
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

    @staticmethod
    def get_initial_brightness(hue_values):
        """ retrieve initial brightness """
        bri = None
        if 'action' in hue_values and 'bri' in hue_values['action']:
            bri = hue_values['action']['bri']
        elif 'state' in hue_values and 'bri' in hue_values['state']:
            bri = hue_values['state']['bri']

        return bri


class DimlevelEvent(object):

    def __init__(self, action, origin):
        self.action = action
        self.origin = origin
