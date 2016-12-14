from Switchable import Switchable
import logging

logger = logging.getLogger('daemon')

class Dimmable(Switchable):
    
    def __init__(self, daemon, hue):
        """ initialize """
        Switchable.__init__(self, daemon, hue)
        
        if 'action' in self.hueValues and 'bri' in self.hueValues['action']:
            self.bri = self.hueValues['action']['bri']
        elif 'state' in self.hueValues and 'bri' in self.hueValues['state']:
            self.bri = self.hueValues['state']['bri']
        else:
            self.bri = None
            
        self._dimlevel = None
        
        """ flag if we don't want to set hue
            because its already dimmed
            e.g. by scene action
        """
        self.lockBri = False
        
    def initPilightDevice(self):
        """ initzialize pilight device """
        Switchable.initPilightDevice(self, skipSync = True)
        
        if self.pilightDevice is not None:
            if 'dimlevel' in self.pilightDevice:
                self._dimlevel = self.pilightDevice['dimlevel']
            if self.dimlevel != self.bri or self.pilightDevice['state'] != self.state:
                self._state = self.pilightDevice['state']
    
    @Switchable.state.setter
    def state(self, value):
        """ set state """
        Switchable.state.fset(self, value)
        
        if value in ['on', 'off']:
            if self.pilightDevice is not None and 'off' == self._state:
                self._switchPilightDeviceOff()
        
    def _switchPilightDeviceOff(self):
        """ switch off pilight device """
        message = {
            "action":"control",
            "code":{
                "device":self.pilightDeviceName,
                "state":"off"
            }
        }
        self.daemon.pilight.sendMessage(message)
    
    @property
    def dimlevel(self):
        """ retrieve dimlevel """
        return self._dimlevel
    
    @dimlevel.setter
    def dimlevel(self, dimlevel):
        """ dim hue device """
        
        logger.debug('Dimmimg ' + self.type + ' ' + self.name + ' to dimlevel ' + str(dimlevel))
        param = {
            "bri": dimlevel if dimlevel > 0 else 1
        }
        
        state = 'on' if dimlevel > 0 else 'off'
        if state != self.state:
            param['on'] = state == 'on'
            
        if self.bri != dimlevel:
            logger.debug('Dimmimg hue {} {} to dimlevel {}'.format(self.type, self.name, dimlevel))
            self.hue._set(param)
            self.bri = dimlevel
        else:
            logger.debug('Hue ' + self.type + ' ' + self.name + ' ' + str(dimlevel) + ' already applied')
            
        self.state = state
        if self.pilightDevice is not None:
            self.pilightDevice['dimlevel'] = dimlevel
            
        self._dimlevel = dimlevel
                
    def mustSync(self):
        """ determine if sync is applicable """
        return self.hueState != self._state or self.bri != self.dimlevel

    def getSyncParam(self):
        """ retrieve sync param """
        param = Switchable.getSyncParam(self)
        param['bri'] = self.dimlevel if self.dimlevel > 0 else 1
        return param
        
        
        
        
        