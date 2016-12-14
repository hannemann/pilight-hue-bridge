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

class PilightSender():
    
    daemon = None
    pilight = None

    def __init__(self, pilight):
        self.pilight = pilight
        self.daemon = pilight.daemon
        logger.info('pilight sender initialized')
    
    def getConfig(self):
        message = {
            "action": "request config"
        }
        self.pilight.sendMessage(message)
    
