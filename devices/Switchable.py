
class Switchable(object):
    
    def __init__(self, daemon, hue):
        """ initialize """
        self.daemon = daemon
        self.hue = hue
        self.name = hue.name
        
        self.pilightDevice = None
        self.pilightDeviceName = ''
        
        self._state = None
        
        """ flag if we don't want to set hue
            because its already switched off
            e.g. by dim action
        """
        self.lockHue = False
        
    def initPilightDevice(self):
        """ initialize pilight device """
        if self.pilightDeviceName in self.daemon.pilight.devices:
            self.pilightDevice = self.daemon.pilight.devices[self.pilightDeviceName]
            
    @property
    def state(self):
        """ get state
        """
        return self._state
    
    @state.setter
    def state(self, value):
        """ set state
        """
        if value in ['on', 'off']:
            self._state = value
            
            if self.lockHue is False:
                self.hue.on = value == 'on'
            else:
                self.lockHue = False
    
    def sync(self):
        """ synchronize state and dimlevel
        """
        self.hue._set(self.getSyncParam())
        
    def getSyncParam(self):
        """ retrieve sync param """
        return {
            "on": self.state == 'on'
        }






