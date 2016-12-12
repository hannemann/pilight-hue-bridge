#!/usr/bin/env python

import socket
import httplib
import StringIO
import struct
import re
import json
import time

class PilightSender():
    
    daemon = None
    pilight = None

    def __init__(self, pilight):
        self.pilight = pilight
        self.daemon = pilight.daemon
        self.daemon.debug('pilight sender initialized')
    
    def getConfig(self):
        message = {
            "action": "request config"
        }
        self.pilight.sendMessage(message)
    
