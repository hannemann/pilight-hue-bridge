from Switchable import Switchable

class Dimmable(Switchable):
    
    def __init__(self, daemon, hue):
        """ initialize """
        Switchable.__init__(self, daemon, hue)
        self.dimlevel = None
        
    def initPilightDevice(self):
        """ initzialize pilight device """
        Switchable.initPilightDevice(self, skipSync = True)
        
        if self.pilightDevice is not None:
            if 'dimlevel' in self.pilightDevice:
                self.dimlevel = self.pilightDevice['dimlevel']
            if self.dimlevel != self.bri or self.pilightDevice['state'] != self.state:
                self._state = self.pilightDevice['state']
                
        self.sync()
    
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
                    
    def dim(self, dimlevel):
        """ dim hue device """
        param = {
            "bri": dimlevel if dimlevel > 0 else 1
        }
        
        state = 'on' if dimlevel > 0 else 'off'
        if state != self.state:
            param['on'] = state == 'on'
            
        self.hue._set(param)
            
        self.lockHue = True
        self.state = state
        if self.pilightDevice is not None:
            self.pilightDevice['dimlevel'] = dimlevel
        self.bri = dimlevel

    def getSyncParam(self):
        """ retrieve sync param """
        param = Switchable.getSyncParam(self)
        param['bri'] = self.dimlevel if self.dimlevel > 0 else 1
        return param
        
        
        
        
        