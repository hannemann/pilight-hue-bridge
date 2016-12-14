from Switchable import Switchable
from Dimmable import Dimmable
import time
import logging

logger = logging.getLogger('daemon')

class Light(Dimmable):
    
    perfomanceLogging = False
    
    type = 'light'
    
    def __init__(self, daemon, pilight, hue, hueValues):
        """ initialize """
        self.hueValues = hueValues
        self.logPerformance('GET init light')
        Dimmable.__init__(self, daemon, hue)
        self.groupName = pilight['group']
        self.lightName = self.name
        
        self.initPilightDevice()
        self.logPerformance('GET init light end')
        
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
        self.hue._set(message)
        
        time.sleep(.5)
        
        message = {
            "bri": toBri,
            "transitiontime": tt,
            "on": toBri > 0
        }
        self.hue._set(message)
        
    def updatePilightDevice(self, dimlevel):
        """ update pilight device to reflect hue state """
        if self.pilightDevice is not None:
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
            self.dimlevel = dimlevel
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
        
        
        
        
        