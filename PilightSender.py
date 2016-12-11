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
        if len(parts) >= 4 and parts[0] == 'hue' and parts[1] == 'scene' and u['values']['state'] == 'on':
            self.updateSceneSwitches(device)
        elif parts[1] == 'bri':
            self.updateDimmer(device, u['values']['dimlevel'])
    
    def updateSceneSwitches(self, device):
        group = device.split('_')[2]
        message = []
        for l in self.pilight.devices:
            if l != device:
                parts = l.split('_')
                if len(parts) >= 4 and parts[0] == 'hue' and parts[1] == 'scene' and parts[2] == group:
                    message.append({
                        "action":"control",
                        "code":{
                            "device":str(l),
                            "state":"off"
                        }
                    })
                    self.pilight.devices[l]['state'] = 'off'
        self.pilight.sendMessage(message)
    
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
    
