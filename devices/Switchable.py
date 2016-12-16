import logging
from pilight.Switch import Switch as PilightSwitch
from hue.Light import Light as HueLight

logger = logging.getLogger('daemon')


class Switchable(object):
    
    def __init__(self, daemon, hue_values, hue_id):
        """ initialize """
        self.daemon = daemon
        self.pilight = None
        self.pilight_name = ''
        self.name = hue_values['name']
        self.id = hue_id
        self.type = ''
        self.groupName = ''
        self.lightName = ''
        self.action = 'toggle'
        self._state = None

        self.hue = self.init_hue_device(hue_values, hue_id)

        self.state_callbacks = []
        
    def get_pilight_name(self):
        """ initialize pilight device """
        
        return '_'.join([
            'hue',
            self.type,
            self.groupName,
            self.lightName,
            self.action
        ])

    def get_pilight_class(self):
        """ retrieve new pilight device class """
        return PilightSwitch

    def init_pilight_device(self):
        """ initialize pilight device """
        self.pilight_name = self.get_pilight_name()
        if self.pilight_name in self.daemon.pilight.devices:
            pilight = self.daemon.pilight.devices[self.pilight_name]
            self.pilight = self.get_pilight_class()(self.daemon, self.pilight_name, pilight)

    def init_hue_device(self, hue_values, hue_id):
        """ initialize hue device """
        return HueLight(self.daemon, hue_values, hue_id)
            
    @property
    def state(self):
        """ get state """
        return self.pilight.state
    
    @state.setter
    def state(self, state):
        """ set state """
        if state in ['on', 'off']:
            logger.debug('Switching ' + self.type + ' ' + self.name + ' ' + state)
            action = False
            if self._state != state:
                action = True
                self.switch_hue(state)
                if self.hue.state == state:
                    self._state = state
            else:
                logger.debug('Hue ' + self.type + ' ' + self.name + ' is already ' + state)

            self.pilight.state = self._state
            self.state_callback(action)

    def switch_hue(self, state):
        """ send message to bridge """
        self.hue.state = state

    def sync(self):
        """ synchronize state and dimlevel """
        if self.pilight is not None:
            param = self.get_sync_param()
            if self.can_sync():
                result = self.hue.send_to_bridge(param)[0][0]
                logger.debug(
                    'SYNC: {0} {1}: {2}'.format(self.type, self.name, result.keys()[0])
                )
                
    def can_sync(self):
        """ determine if sync is applicable """
        return self.hue.state != self.state
        
    def get_sync_param(self):
        """ retrieve sync param """
        return {
            "on": self.state == 'on'
        }

    def send_to_bridge(self, param):
        """ send param to setter according to type
        :return: dict
        """
        return getattr(self.daemon.hue.bridge, 'set_' + self.type)(self.id, param)

    def register_state_callback(self, func):
        """ register callback function """
        self.state_callbacks.append(func)

    def state_callback(self, action):
        """ call state callbacks """
        for func in self.state_callbacks:
            func(StateEvent(action, self))


class StateEvent(object):

    def __init__(self, action, origin):
        self.action = action
        self.origin = origin
