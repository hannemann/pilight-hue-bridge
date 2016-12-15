import logging

logger = logging.getLogger('daemon')


class PilightReceiver(object):

    def __init__(self, pilight):
        self.pilight = pilight
        self.daemon = pilight.daemon
        logger.info('pilight receiver initialized')
            
    def parse_config(self, c):
        config = c['config']
        
        self.pilight.config = config
        if 'devices' in config:
            self.pilight.devices = self.normalize_devices(config['devices'])
        if 'rules' in config:
            self.pilight.rules = self.pilight.config['rules']
        if 'gui' in config:
            self.pilight.gui = self.pilight.config['gui']
        logger.info('loaded config from pilight')

    def normalize_devices(self, devices):
        for name in devices:
            if 'hue_' == name[:4]:
                device = devices[name]
                if 'dimlevel' in device:
                    dimlevel = float(device['dimlevel']) / 100 * 254
                    device['dimlevel'] = int(round(dimlevel))

        return devices

    def normalize_update(self, update):
        if 'dimlevel' in update['values']:
            dimlevel = float(update['values']['dimlevel']) / 100 * 254
            update['values']['dimlevel'] = int(round(dimlevel))


        return update

