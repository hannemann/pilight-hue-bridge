from Dimmable import Dimmable
import logging

logger = logging.getLogger('daemon')


class Light(Dimmable):
    
    perfomanceLogging = False
    
    def __init__(self, daemon, pilight, hue, hue_values):
        """ initialize """
        self.log_performance('GET init light')
        Dimmable.__init__(self, daemon, hue, hue_values)
        self.groupName = pilight['group']
        self.lightName = self.name
        self.type = 'light'
        self.id = hue.light_id
        
        self.init_pilight_device()
        self.log_performance('GET init light end')
    
    def log_performance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
