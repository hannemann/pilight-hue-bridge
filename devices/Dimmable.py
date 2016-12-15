from Switchable import Switchable
import time
import logging

logger = logging.getLogger('daemon')


class Dimmable(Switchable):
    
    def __init__(self, daemon, hue, hue_values):
        """ initialize """
        Switchable.__init__(self, daemon, hue, hue_values)
        
        if 'action' in self.hueValues and 'bri' in self.hueValues['action']:
            self.bri = self.hueValues['action']['bri']
        elif 'state' in self.hueValues and 'bri' in self.hueValues['state']:
            self.bri = self.hueValues['state']['bri']
        else:
            self.bri = None
            
        self._dimlevel = None
        
    def init_pilight_device(self):
        """ initzialize pilight device """
        Switchable.init_pilight_device(self)
        
        if self.pilightDevice is not None:
            if 'dimlevel' in self.pilightDevice:
                self._dimlevel = self.pilightDevice['dimlevel']
            if self.dimlevel != self.bri or self.pilightDevice['state'] != self.state:
                self._state = self.pilightDevice['state']
    
    @Switchable.state.setter
    def state(self, state):
        """ set state """
        Switchable.state.fset(self, state)
    
    @property
    def dimlevel(self):
        """ retrieve dimlevel """
        return self._dimlevel
    
    @dimlevel.setter
    def dimlevel(self, dimlevel):
        """ dim hue device """
        logger.debug('Dimmimg ' + self.type + ' ' + self.name + ' to dimlevel ' + str(dimlevel))
        self.update_hue_device(dimlevel)
        self.update_pilight_device(dimlevel)
        self.state = 'on' if dimlevel > 0 else 'off'
            
    def update_hue_device(self, dimlevel):
        """ update hue device """
        if self.bri != dimlevel:
            logger.debug('Dimmimg hue {} {} to dimlevel {}'.format(self.type, self.name, dimlevel))
            param = {
                "bri": dimlevel if dimlevel > 0 else 1
            }
            state = 'on' if dimlevel > 0 else 'off'
            if state != self.state:
                param['on'] = state == 'on'
            success = self.hue._set(param)
            logger.debug(
                '{3}: apply dimlevel {0} to {1} {2}'.format(
                    dimlevel, self.type, self.name, 'Success' if success else 'Error'
                )
            )
            if success:
                self.bri = dimlevel
        else:
            logger.debug('Hue ' + self.type + ' ' + self.name + ' ' + str(dimlevel) + ' already applied')

    def update_pilight_device(self, dimlevel):
        """ update pilight device to reflect hue state """
        if self._dimlevel != dimlevel:
            logger.debug('Dimmimg pilight {} {} to dimlevel {}'.format(self.type, self.name, dimlevel))
            message = {
                "action": "control",
                "code": {
                    "device": self.pilightDeviceName,
                    "values": {
                        "dimlevel": dimlevel
                    }
                }
            }
            self.daemon.pilight.send_message(message)
            self.pilightDevice['dimlevel'] = dimlevel
            self._dimlevel = dimlevel
        else:
            logger.debug('pilight ' + self.type + ' ' + self.name + ' ' + str(dimlevel) + ' already applied')
        
    def set_transition(self, config):
        """ apply transition """
        self._state = 'on'
        from_bri = int(config['fromBri'])
        to_bri = int(config['toBri'])
        tt = int(config['transitiontime'])
        message = {
            "on": True,
            "bri": from_bri
        }
        success = self.hue._set(message)
        logger.debug(
            '{2} apply transition start values to {0} {1}'.format(
                self.type, self.name, 'Success' if success else 'Error'
            )
        )
        
        time.sleep(.5)
        
        message = {
            "bri": to_bri,
            "transitiontime": tt,
            "on": to_bri > 0
        }
        success = self.hue._set(message)
        logger.debug(
            '{2} applied transition end values to {0} {1}'.format(
                self.type, self.name, 'Success' if success else 'Error'
            )
        )
                
    def can_sync(self):
        """ determine if sync is applicable """
        return self.hueState != self._state or self.bri != self.dimlevel

    def get_sync_param(self):
        """ retrieve sync param """
        param = Switchable.get_sync_param(self)
        param['bri'] = self.dimlevel if self.dimlevel > 0 else 1
        return param
