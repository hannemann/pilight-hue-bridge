import json
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

    def normalize_message(self, message):
        """ normalize dimlevel """
        if isinstance(message, list):
            for i in message:
                message[i] = self.normalize_dimlevel(message[i])
        else:
            message = self.normalize_dimlevel(message)

        return message

    def normalize_dimlevel(self, message):
        if 'code' in message and 'values' in message['code'] and 'dimlevel' in message['code']['values']:
            dimlevel = float(message['code']['values']['dimlevel']) / 254 * 100
            message['code']['values']['dimlevel'] = int(round(dimlevel))
        return message
