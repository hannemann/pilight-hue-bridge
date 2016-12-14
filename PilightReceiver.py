#!/usr/bin/env python

import socket
import httplib
import StringIO
import struct
import re
import json
import time
import logging

logger = logging.getLogger('daemon')

class PilightReceiver():

    def __init__(self, pilight):
        self.pilight = pilight
        self.daemon = pilight.daemon
        logger.info('pilight receiver initialized')
            
    def parseConfig(self, c):
        config = c['config'];
        
        self.pilight.config = config
        if 'devices' in config:
            self.pilight.devices = config['devices']
        if 'rules' in config:
            self.pilight.rules = self.pilight.config['rules']
        if 'gui' in config:
            self.pilight.gui = self.pilight.config['gui']
        logger.info('loaded config from pilight')
