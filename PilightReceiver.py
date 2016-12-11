#!/usr/bin/env python
#
#	Copyright (C) 2013 CurlyMo
#
#	This file is part of pilight.
#
#   pilight is free software: you can redistribute it and/or modify it under the
#	terms of the GNU General Public License as published by the Free Software
#	Foundation, either version 3 of the License, or (at your option) any later
#	version.
#
#   pilight is distributed in the hope that it will be useful, but WITHOUT ANY
#	WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#	A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with pilight. If not, see	<http://www.gnu.org/licenses/>
#
import socket
import httplib
import StringIO
import struct
import re
import threading
import json
import time

class PilightReceiver(threading.Thread):
    
    daemon = None
    terminate = False
    retries = 1
    service = "urn:schemas-upnp-org:service:pilight:1"
    config = None
    devices = None

    def __init__(self, daemon, retries=1):
        threading.Thread.__init__(self)
        self.daemon = daemon
        self.retries = retries
    
    def discover(self, service, timeout=2, retries=1):
        group = ("239.255.255.250", 1900)
        message = "\r\n".join([
            'M-SEARCH * HTTP/1.1',
            'HOST: {0}:{1}'.format(*group),
            'MAN: "ssdp:discover"',
            'ST: {st}','MX: 3','',''])

        responses = {}
        i = 0;
        for _ in range(retries):
            i += 1
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 0, 10000));
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto(message.format(st=service), group)
            while True:
                if self.terminate is True:
                    break;
                try:
                    responses[i] = sock.recv(1024);
                    break;
                except socket.timeout:
                    break;
                except:
                    print "no pilight ssdp connections found"
                    break;
            time.sleep(.2)
        return responses.values()

    def run(self):
        self.daemon.emit('starting pilight receiver')
        self.message = '{"action": "request config"}'
        self.responses = self.discover(self.service, retries=self.retries)
        if self.terminate is False and len(self.responses) > 0:
            self.daemon.emit('pilight connected')
            locationsrc = re.search('Location:([0-9.]+):(.*)', str(self.responses[0]), re.IGNORECASE)
            if locationsrc:
                location = locationsrc.group(1)
                port = locationsrc.group(2)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket.setdefaulttimeout(0)
            s.connect((location, int(port)))
            s.send('{"action":"identify","options":{"receiver":1,"config":1}}\n')
            text = "";
            while True:
                line = s.recv(1024)
                text += line;
                if "\n\n" in line[-2:]:
                    text = text[:-2];
                    break;
                if self.terminate is True:
                    break
            if text == '{"status":"success"}':
                text = "";	
                while True:
                    if self.terminate is True:
                        break
                    if self.message is not None:
                        self.daemon.debug(self.message)
                        s.send(self.message + '\n')
                        self.message = None
                        while True:
                            line = s.recv(1024)
                            text += line;
                            if "\n\n" in line[-2:]:
                                if self.config is None:
                                    try:
                                        self.parseConfig(json.loads(text))
                                    except ValueError:
                                        self.daemon.emit('could not load config')
                                        pass
                                text = ""
                                break;
                    line = s.recv(1024)
                    text += line;
                    if "\n\n" in line[-2:]:
                        text = text[:-2];
                        for f in iter(text.splitlines()):
                            #self.daemon.emit(f)
                            try:
                                j = json.loads(f)
                                if j['origin'] is not None and j['origin'] == "update":
                                    self.daemon.proxyUpdate(j)
                            except KeyError:
                                pass
                            except ValueError:
                                pass
                        text = "";
            s.close()
            
    def parseConfig(self, c):
        self.config = c['config']        
        self.devices = self.config['devices']
        self.rules = self.config['rules']
        self.gui = self.config['gui']
            
        
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
        for l in self.devices:
            if l != device:
                parts = l.split('_')
                if len(parts) >= 4 and parts[0] == 'hue' and parts[1] == 'scene' and parts[2] == group:
                    message.append('{"action":"control","code":{"device":"'+l+'","state":"off"}}')
                    self.devices[l]['state'] = 'off'
        self.message = '\n'.join(message)          
    
    def updateDimmer(self, device, dimlevel):
        if dimlevel == 0:
            self.devices[device]['state'] = 'off'
            self.message = '{"action":"control","code":{"device":"'+device+'","state":"off"}}'
        
    def shutdown(self):
        self.daemon.emit('shutting down pilight receiver')
        self.terminate = True
