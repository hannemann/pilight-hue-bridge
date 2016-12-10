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

class PilightSend(threading.Thread):
    
    daemon = None
    terminate = False
    retries = 1
    service = "urn:schemas-upnp-org:service:pilight:1"
    message = None

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
        return responses.values()

    def run(self):
        self.daemon.emit('starting pilight receiver')
        self.message = '{"action": "request config"}'
        self.responses = self.discover(self.service, retries=self.retries)
        if self.terminate is False and len(self.responses) > 0:
            locationsrc = re.search('Location:([0-9.]+):(.*)', str(self.responses[0]), re.IGNORECASE)
            if locationsrc:
                location = locationsrc.group(1)
                port = locationsrc.group(2)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket.setdefaulttimeout(0)
            s.connect((location, int(port)))
            while True:
                if self.message is not None:
                    s.send(self.message + '\n')
                    self.message = None
                    text = ''
                    while True:
                        line = s.recv(1024)
                        text += line;
                        if "\n\n" in line[-2:]:
                            self.daemon.emit(text)
                            break;
                if self.terminate is True:
                    break
                sleep(.1)
            s.close()
            
    
            
    def shutdown(self):
        seld.daemon.emit('shutting down pilight receiver')
        self.terminate = True
