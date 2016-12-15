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
        self.logPerformance('GET init light')
        Dimmable.__init__(self, daemon, hue, hueValues)
        self.groupName = pilight['group']
        self.lightName = self.name
        self.id = hue.light_id
        
        self.initPilightDevice()
        self.logPerformance('GET init light end')
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
        
        
        
        
        