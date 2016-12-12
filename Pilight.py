#!/usr/bin/env python

import socket
import httplib
import StringIO
import struct
import threading
import re
import json
import time
from PilightReceiver import PilightReceiver
from PilightSender import PilightSender

class Pilight(threading.Thread):
    
    service = "urn:schemas-upnp-org:service:pilight:1"
    hasServer = False
    terminate = False
    getConfigFlag = True
    restartTimer = None
    heartbeatTimer = None
    autoreconnect = False

    def __init__(self, daemon, retries=1):
        threading.Thread.__init__(self)
        self.retries = retries
        self.daemon = daemon
        self.sender = PilightSender(self)
        self.receiver = PilightReceiver(self)
        self.next_heartbeat = time.time()
        if self.discover():
            self.connect()
    
    def discover(self, timeout=2):
        group = ("239.255.255.250", 1900)
        message = "\r\n".join([
            'M-SEARCH * HTTP/1.1',
            'HOST: {0}:{1}'.format(*group),
            'MAN: "ssdp:discover"',
            'ST: {st}','MX: 3','',''])
        
        self.ip = None
        self.port = None
        self.sock = None
        
        sock = self.getUdpSocket()

        for _ in range(self.retries):
            sock.sendto(message.format(st=self.service), group)
            while True:
                try:
                    response = sock.recv(1024)
                    location = re.search('Location:([0-9.]+):(.*)', str(response), re.IGNORECASE)
                    if location:
                        self.ip = location.group(1)
                        self.port = location.group(2)
                    break;
                except socket.timeout:
                    break;
                except:
                    self.daemon.emit("no pilight ssdp connections found")
                    break;
            time.sleep(.2)
        if self.ip is not None and self.port is not None:
            self.daemon.emit('pilight discovered');
            return True
        else:
            self.daemon.emit('pilight server not found')
            return False

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(0)
        self.sock.connect_ex((self.ip, int(self.port)))
        self.hasServer = True

    def run(self):
        self.daemon.emit('starting pilight')
        while True:
            if self.terminate is False and self.hasServer is True:
                
                if self.identify():
                    self.daemon.emit('pilight connected')
                    if self.autoreconnect is True and self.heartbeatTimer is None:
                        self.heartBeat()
                    text = ''
                    line = ''
                    while True:
                        if self.terminate is True:
                            break
                        try:
                            line = self.sock.recv(1024)
                            text += line;
                        except:
                            pass
                        if "\n\n" in line[-2:]:
                            text = text[:-2];
                            
                            for f in iter(text.splitlines()):
                                if f == 'BEAT':
                                    self.alive = True
                                try:
                                    #self.daemon.emit(f)
                                    j = json.loads(f)
                                    if 'origin' in j and j['origin'] == "update":
                                        self.daemon.proxyUpdate(j)
                                    if 'config' in j and self.getConfigFlag is True:
                                        self.getConfigFlag = False
                                        self.receiver.parseConfig(j)
                                        self.daemon.updateDevices(self)
                                    if 'status' in j:
                                        self.daemon.debug('Pilight action: ' + j['status'])
                                except KeyError:
                                    pass
                                except ValueError:
                                    pass
                                    
                            if self.getConfigFlag is True:
                                self.sender.getConfig()
                            
                            text = "";
                        if self.autoreconnect is True and self.alive is False:
                            self.daemon.emit('Lost connection to pilight server')
                            self.hasServer = False
                            break;
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
                
            if self.autoreconnect is True and self.hasServer is False:
                if self.restartTimer is None:
                    self.daemon.emit('Trying to reconnect to pilight in 5 seconds')
                    self.restartTimer = threading.Timer( 5, self.restart )
                    self.restartTimer.start()
                time.sleep(2)
    
    def identify(self):
        message = {
            "action": "identify",
            "options": {
                "receiver": 1,
                "config": 1
            }
        }
        response = self.sendMessage(message).getResponse()
        if response is not False and 'status' in response and response["status"] == "success":
            self.daemon.emit('Successfully identified against pilight api')
            return True
        else:
            self.daemon.emit('Could not identify against pilight api')
            return False

    def heartBeat(self):
        self.daemon.debug('sending heartbeat to pilight server')
        self.alive = False
        if self.hasServer is True:
            self.sendMessage('heartbeat')
        self.next_heartbeat = self.next_heartbeat + 5
        self.heartbeatTimer = threading.Timer( self.next_heartbeat - time.time(), self.heartBeat )
        self.heartbeatTimer.start()

    def sendMessage(self, message):
        if message == 'heartbeat':
            message = 'HEART'
        elif isinstance(message, list):
            message = '\n'.join(json.dumps(x) for x in message)
        else:
            message = json.dumps(message)
        try:
            self.sock.send(message + '\n')
        except:
            pass
        return self
    
    def getResponse(self):
        text = ''
        line = ''
        while True:
            try:
                line = self.sock.recv(1024)
                text += line;
            except:
                pass
            if "\n\n" in line[-2:]:
                text = text[:-2];
                break;
            if self.terminate is True:
                break
        try:
            response = json.loads(text)
        except ValueError:
            return False
        
        return response
    
        
    def getUdpSocket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 0, 10000));
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        return sock
        
    def restart(self):
        self.daemon.emit('trying to reconnect to pilight server')
        if self.discover():
            self.connect()
            self.restartTimer = None;
        else:
            self.restartTimer = threading.Timer( 5, self.restart )
            self.restartTimer.start()
    
    def shutdown(self):
        self.daemon.emit('shutting down pilight')
        if self.restartTimer is not None:
            self.restartTimer.cancel()
        if self.heartbeatTimer is not None:
            self.heartbeatTimer.cancel()
        self.terminate = True
