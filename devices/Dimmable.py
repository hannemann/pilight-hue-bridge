from Switchable import Switchable
import time
import logging

logger = logging.getLogger('daemon')

class Dimmable(Switchable):
    
    def __init__(self, daemon, hue, hueValues):
        """ initialize """
        Switchable.__init__(self, daemon, hue, hueValues)
        
        if 'action' in self.hueValues and 'bri' in self.hueValues['action']:
            self.bri = self.hueValues['action']['bri']
        elif 'state' in self.hueValues and 'bri' in self.hueValues['state']:
            self.bri = self.hueValues['state']['bri']
        else:
            self.bri = None
            
        self._dimlevel = None
        
    def initPilightDevice(self):
        """ initzialize pilight device """
        Switchable.initPilightDevice(self, skipSync = True)
        
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
        self.updateHueDevice(dimlevel)
        self.updatePilightDevice(dimlevel)
        self.state = 'on' if dimlevel > 0 else 'off'
            
    def updateHueDevice(self, dimlevel):
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
            logger.debug('{3}: apply dimlevel {0} to {1} {2}'.format(dimlevel, self.type, self.name, 'Success' if success else 'Error'))
            if success:
                self.bri = dimlevel
        else:
            logger.debug('Hue ' + self.type + ' ' + self.name + ' ' + str(dimlevel) + ' already applied')
        
        
    def updatePilightDevice(self, dimlevel):
        """ update pilight device to reflect hue state """
        if self._dimlevel != dimlevel:
            logger.debug('Dimmimg pilight {} {} to dimlevel {}'.format(self.type, self.name, dimlevel))
            message = {
                "action":"control",
                "code":{
                    "device":self.pilightDeviceName,
                    "values": {
                        "dimlevel": dimlevel
                    }
                }
            }
            self.daemon.pilight.sendMessage(message)
            self.pilightDevice['dimlevel'] = dimlevel
            self._dimlevel = dimlevel
        else:
            logger.debug('pilight ' + self.type + ' ' + self.name + ' ' + str(dimlevel) + ' already applied')
        
    def setTransition(self, config):
        """ apply transition """
        self._state = 'on'
        fromBri = int(config['fromBri'])
        toBri = int(config['toBri'])
        tt = int(config['transitiontime'])
        message = {
            "on": True,
            "bri": fromBri
        }
        success = self.hue._set(message)
        logger.debug('{2} apply transition start values to {0} {1}'.format(self.type, self.name, 'Success' if success else 'Error'))
        
        time.sleep(.5)
        
        message = {
            "bri": toBri,
            "transitiontime": tt,
            "on": toBri > 0
        }
        success = self.hue._set(message)
        logger.debug('{2} applied transition end values to {0} {1}'.format(self.type, self.name, 'Success' if success else 'Error'))
                
    def canSync(self):
        """ determine if sync is applicable """
        return self.hueState != self._state or self.bri != self.dimlevel

    def getSyncParam(self):
        """ retrieve sync param """
        param = Switchable.getSyncParam(self)
        param['bri'] = self.dimlevel if self.dimlevel > 0 else 1
        return param
        
        
        
        
        