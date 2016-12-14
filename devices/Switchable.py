
import logging

logger = logging.getLogger('daemon')

class Switchable(object):
    
    def __init__(self, daemon, hue):
        """ initialize """
        self.daemon = daemon
        self.hue = hue
        self.name = hue.name
        
        hueValues = self.hue._get()
        if 'action' in hueValues and 'bri' in hueValues['action']:
            self.bri = hueValues['action']['bri']
        elif 'state' in hueValues and 'bri' in hueValues['state']:
            self.bri = hueValues['state']['bri']
        else:
            self.bri = None
        
        self.pilightDevice = None
        self.pilightDeviceName = ''
        
        """ flag if we don't want to set hue
            because its already switched off
            e.g. by dim action
        """
        self.lockHue = False
        
        self._state = 'on' if hue.on else 'off' 
        
    def initPilightDevice(self, skipSync = False):
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
        
        if skipSync is not False:
            self.sync()
            
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
        if self.pilightDevice is not None:
            self.hue._set(self.getSyncParam())
        
    def getSyncParam(self):
        """ retrieve sync param """
        return {
            "on": self.state == 'on'
        }






