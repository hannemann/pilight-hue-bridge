
import logging

logger = logging.getLogger('daemon')


class PilightSender(object):
    
    daemon = None
    pilight = None

    def __init__(self, pilight):
        self.pilight = pilight
        self.daemon = pilight.daemon
        logger.info('pilight sender initialized')
    
    def get_config(self):
        message = {
            "action": "request config"
        }
        self.pilight.send_message(message)
