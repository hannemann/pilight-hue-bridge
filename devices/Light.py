from Switchable import Switchable
from Dimmable import Dimmable
import time

class Light(Dimmable):
    
    def __init__(self, daemon, pilight, hue):
        """ initialize """
        Dimmable.__init__(self, daemon, hue)
        self.daemon = daemon
        #self.pilightDevice = pilight
        self._state = 'on' if hue.on else 'off'
        
        self.daemon.debug(self.name)
        
    def setTransition(self, config):

        self._state = 'on'
        fromBri = int(config['fromBri'])
        toBri = int(config['toBri'])
        tt = int(config['transitiontime'])
        message = {
            "on": True,
            "bri": fromBri
        }
        self.hue._set(message)
        
        time.sleep(.5)
        
        message = {
            "bri": toBri,
            "transitiontime": tt,
            "on": toBri > 0
        }
        self.hue._set(message)
        
        
        
        
        
        