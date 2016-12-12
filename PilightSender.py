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
        
    def processUpdate(self, u):
        device = u['devices'][0]
        parts = device.split('_')
        if parts[0] == 'hue':
            self.parseUpdate(parts, u)
        
    def parseUpdate(self, parts, u):
        device = u['devices'][0]
        parts = device.split('_')
        
        deviceType = parts[1]
        groupName = parts[2]
        deviceName = parts[3]
        action = None
        if len(parts) > 4:
            action = parts[4]
            
        elif action is not None and action == 'bri':
            self.updateDimmer(device, u['values']['dimlevel'])
    
    def updateDimmer(self, device, dimlevel):
        if dimlevel == 0:
            self.pilight.devices[device]['state'] = 'off'
            message = {
                "action":"control",
                "code":{
                    "device":str(device),
                    "state":"off"
                }
            }
            self.pilight.sendMessage(message)
    
    def getConfig(self):
        message = {
            "action": "request config"
        }
        self.pilight.sendMessage(message)
    
