    
import logging

logger = logging.getLogger('daemon')


class Switchable(object):
    
    def __init__(self, daemon, hue, hue_values):
        """ initialize """
        self.daemon = daemon
        self.hue = hue
        self.hueValues = hue_values
        self.pilightDevice = None
        self.pilightDeviceName = ''
        on = False
        if 'action' in self.hueValues and 'on' in self.hueValues['action']:
            on = self.hueValues['action']['on']
        elif 'state' in self.hueValues and 'on' in self.hueValues['state']:
            on = self.hueValues['state']['on']
            
        self._state = 'on' if on else 'off'
        self.hueState = self._state
        self.name = self.hueValues['name']
        self.id = None
        self.type = ''
        self.groupName = ''
        self.lightName = ''
        
    def init_pilight_device(self):
        """ initialize pilight device """
        
        self.pilightDeviceName = '_'.join([
            'hue',
            self.type,
            self.groupName,
            self.lightName,
            'bri'
        ])
        
        if self.pilightDeviceName in self.daemon.pilight.devices:
            self.pilightDevice = self.daemon.pilight.devices[self.pilightDeviceName]
            
    @property
    def state(self):
        """ get state """
        return self._state
    
    @state.setter
    def state(self, state):
        """ set state """
        if state in ['on', 'off']:
            logger.debug('Switching ' + self.type + ' ' + self.name + ' ' + state)
            
            if self._state != state:
                logger.debug('Switching hue ' + self.type + ' ' + self.name + ' ' + state)
                param = {
                    "on": state == 'on'
                }
                result = self.send_to_bridge(param)[0][0]
                logger.debug(
                    'SWITCH: {0} {1} {2}: {3}'.format(
                        self.type, self.name, state, result.keys()[0]
                    )
                )
                if 'success' == result.keys()[0]:
                    self._state = state
            else:
                logger.debug('Hue ' + self.type + ' ' + self.name + ' is already ' + state)
                
            if self.pilightDevice is not None and 'off' == self._state:
                self.switch_pilight_device_off()
        
    def switch_pilight_device_off(self):
        """ switch off pilight device """
        message = {
            "action": "control",
            "code": {
                "device": self.pilightDeviceName,
                "state": "off"
            }
        }
        self.daemon.pilight.send_message(message)
    
    def sync(self):
        """ synchronize state and dimlevel """
        if self.pilightDevice is not None:
            param = self.get_sync_param()
            if self.can_sync():
                result = self.send_to_bridge(param)[0][0]
                logger.debug(
                    'SYNC: {0} {1}: {2}'.format(self.type, self.name, result.keys()[0])
                )
                
    def can_sync(self):
        """ determine if sync is applicable """
        return self.hueState != self._state
        
    def get_sync_param(self):
        """ retrieve sync param """
        return {
            "on": self.state == 'on'
        }

    def send_to_bridge(self, param):
        """ send param to setter according to type
        :return: dict
        """
        return getattr(self.hue.bridge, 'set_' + self.type)(self.id, param)
