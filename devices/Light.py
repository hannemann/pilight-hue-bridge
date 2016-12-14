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
        self.id = hue.light_id
        
        self.initPilightDevice()
        self.logPerformance('GET init light end')
        
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
            self._dimlevel = dimlevel
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
        
        
        
        
        