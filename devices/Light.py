from Switchable import Switchable
from Dimmable import Dimmable
import time
import logging

logger = logging.getLogger('daemon')

class Light(Dimmable):
    
    perfomanceLogging = False
    
    def __init__(self, daemon, pilight, hue, hue_values):
        """ initialize """
        self.logPerformance('GET init light')
        Dimmable.__init__(self, daemon, hue, hue_values)
        self.groupName = pilight['group']
        self.lightName = self.name
        self.type = 'light'
        self.id = hue.light_id
        
        self.init_pilight_device()
        self.logPerformance('GET init light end')
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
        
        
        
        
        