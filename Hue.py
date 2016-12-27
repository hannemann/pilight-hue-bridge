from config import ConfigParser
from phue import Bridge
from phue import logger as hue_logger

import threading
import time
import logging
import socket

logger = logging.getLogger('hue')
logger.setLevel(logging.INFO)


class Hue(threading.Thread):
    
    terminate = False
    daemon = None
    lights = None
    scenes = None
    groups = None

    def __init__(self, daemon):
        threading.Thread.__init__(self, name='hue')
        self.daemon = daemon
        self.bridge = None
        self.next_update = None
        self.updateTimer = None
        self.address = None
        self.user = None
        self.auto_update = False
        self.bridge = None
        self.read_config()
        self.init_bridge()

        if 'h' in self.daemon.logging['mode']:
            logger.setLevel(self.daemon.logging['h-level'])

        if self.bridge is not None:
            logger.info('hue sender initialized')

    def read_config(self):
        try:
            self.address = self.daemon.config.get('hue', 'address')
            self.user = self.daemon.config.get('hue', 'user')
            self.auto_update = self.daemon.config.get('hue', 'auto_update') in [1, 'on', 'true']
        except ConfigParser.NoSectionError:
            raise HueException(0, 'No section "Hue" found in configuration')
        except ConfigParser.NoOptionError:
            if self.address is None:
                raise HueException(0, 'No option "address" found in configuration')
            elif self.user is None:
                raise HueException(0, 'No option "user" found in configuration')
            elif self.auto_update is False:
                pass

    def init_bridge(self):
        self.bridge = Bridge(self.address, self.user)
        # test connection
        try:
            result = self.bridge.get_api()
            if isinstance(result, list) and 'error' in result[0]:
                raise HueException(
                    0,
                    'Error connecting to hue bridge: {}'.format(result[0]['error']['description'])
                )
        except ValueError as exc:
            raise HueException(
                0,
                'Error connecting to hue bridge: {} (address {} correct?)'.format(exc.message, self.address)
            )
        except socket.error as exc:
            raise HueException(
                exc.errno,
                'Error connecting to hue bridge: {}'.format(exc.strerror)
            )
        
    def run(self):
        logger.info('starting hue sender')
        if 'a' in self.daemon.logging['mode']:
            hue_logger.setLevel(self.daemon.logging['a-level'])
        self.next_update = time.time()
        self.update()
        logger.info('hue connected')
        
    def update(self):
        if self.terminate is False:
            logger.debug('fetching updates from bridge')
            self.scenes = self.bridge.scenes
            self.lights = self.bridge.lights
            self.groups = self.bridge.groups
            self.daemon.update_devices(self)
            if self.auto_update:
                self.next_update += 5
                self.updateTimer = threading.Timer(self.next_update - time.time(), self.update)
                self.updateTimer.start()

    def shutdown(self):
        logger.info("Shutting down hue sender")
        if self.updateTimer is not None:
            self.updateTimer.cancel()
        self.terminate = True


class HueException(Exception):

    def __init__(self, exc_id, message):
        self.id = exc_id
        self.message = message
