from Switchable import Switchable
from pilight.Dimmer import Dimmer as PilightDimmer
import time
import logging

logger = logging.getLogger('daemon')


class Dimmable(Switchable):
    
    def __init__(self, daemon, hue_values, hue_id):
        """ initialize """
        Switchable.__init__(self, daemon, hue_values, hue_id)
        self.pilight_device_class = PilightDimmer
        self.bri = self.get_initial_brightness(hue_values)
        self.action = 'bri'
        self.dimlevel_callbacks = []
        
    def init_pilight_device(self):
        """ initzialize pilight device """
        Switchable.init_pilight_device(self)

        if self.pilightDevice is not None:
            if self.dimlevel != self.bri or self.pilightDevice.state != self.state:
                self._state = self.pilightDevice.state
    
    @property
    def dimlevel(self):
        """ retrieve dimlevel """
        return self.pilightDevice.dimlevel
    
    @dimlevel.setter
    def dimlevel(self, dimlevel):
        """ dim hue device """
        logger.debug('Dimmimg ' + self.type + ' ' + self.name + ' to dimlevel ' + str(dimlevel))
        self.update_hue_device(dimlevel)
        self.update_pilight_device(dimlevel)
        Switchable.state.fset(self, 'on' if dimlevel > 0 else 'off')
            
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
            result = self.send_to_bridge(param)
            success = result[0][0].keys()[0]
            logger.debug(
                'DIMMER: {1} {2} apply dimlevel of {0}: {3}'.format(
                    dimlevel, self.type, self.name, success
                )
            )
            if 'success' == success:
                self.bri = dimlevel
        else:
            logger.debug('Hue: {} {} dimlevel {} already applied'.format(self.type, self.name, str(dimlevel)))

    def update_pilight_device(self, dimlevel):
        """ update pilight device to reflect hue state """
        action = False
        if self.dimlevel != dimlevel:
            if self.pilightDevice is not None:
                self.pilightDevice.dimlevel = dimlevel
            action = True
        else:
            logger.debug('pilight: {} {} dimlevel {} already applied'.format(self.type, self.name, str(dimlevel)))

        self.dimlevel_callback(action)
        
    def set_transition(self, config):
        """ apply transition """
        self._state = 'on'
        from_bri = int(config['fromBri'])
        to_bri = int(config['toBri'])
        tt = int(config['transitiontime'])
        param = {
            "on": True,
            "bri": from_bri
        }
        result = self.send_to_bridge(param)
        logger.debug(
            'TRANSITION: apply start values to {0} {1}: {2}'.format(
                self.type, self.name, result[0][0].keys()[0]
            )
        )
        
        time.sleep(.5)
        
        param = {
            "bri": to_bri,
            "transitiontime": tt,
            "on": to_bri > 0
        }
        result = self.send_to_bridge(param)
        logger.debug(
            'TRANSITION: apply end values to {0} {1}: {2}'.format(
                self.type, self.name, result[0][0].keys()[0]
            )
        )
                
    def can_sync(self):
        """ determine if sync is applicable """
        return self.hueState != self._state or self.bri != self.dimlevel

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
        param['on'] = True if self.dimlevel > 0 else False
        if param['on']:
            param['bri'] = self.dimlevel if self.dimlevel > 0 else 1
        return param

    def register_dimlevel_callback(self, func):
        self.dimlevel_callbacks.append(func)

    def dimlevel_callback(self, action):
        for func in self.dimlevel_callbacks:
            func(DimlevelEvent(action, self))

    def get_initial_brightness(self, hue_values):
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
