#!/usr/bin/env python

import socket
import struct
import threading
import re
import json
import time
from PilightReceiver import PilightReceiver
from PilightSender import PilightSender
import logging

logger = logging.getLogger('pilight')
logger.setLevel(logging.INFO)


class Pilight(threading.Thread):
    
    service = "urn:schemas-upnp-org:service:pilight:1"
    hasServer = False
    terminate = False
    getConfigFlag = True
    restartTimer = None
    heartbeatTimer = None
    autoreconnect = False
    ip = None
    port = None
    sock = None
    alive = False

    def __init__(self, daemon, retries=1):
        threading.Thread.__init__(self, name='pilight')
        self.retries = retries
        self.daemon = daemon
        if 'p' in self.daemon.logging['mode']:
            logger.setLevel(self.daemon.logging['p-level'])
        self.sender = PilightSender(self)
        self.receiver = PilightReceiver(self)
        self.next_heartbeat = time.time()
        if self.discover():
            self.connect()
    
    def discover(self):
        group = ("239.255.255.250", 1900)
        message = "\r\n".join([
            'M-SEARCH * HTTP/1.1',
            'HOST: {0}:{1}'.format(*group),
            'MAN: "ssdp:discover"',
            'ST: {st}', 'MX: 3', '', ''])
        
        self.ip = None
        self.port = None
        self.sock = None
        
        sock = self.get_udp_socket()

        for _ in range(self.retries):
            sock.sendto(message.format(st=self.service), group)
            while True:
                try:
                    response = sock.recv(1024)
                    location = re.search('Location:([0-9.]+):(.*)', str(response), re.IGNORECASE)
                    if location:
                        self.ip = location.group(1)
                        self.port = location.group(2)
                    break
                except socket.timeout:
                    break
                except:
                    logger.info("no pilight ssdp connections found")
                    break
            time.sleep(.2)
        if self.ip is not None and self.port is not None:
            logger.info('pilight discovered')
            return True
        else:
            logger.info('pilight server not found')
            return False

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(0)
        self.sock.connect_ex((self.ip, int(self.port)))
        self.hasServer = True

    def run(self):
        logger.info('starting pilight')
        while True:
            if self.terminate is False and self.hasServer is True:
                
                if self.identify():
                    logger.info('pilight connected')
                    if self.autoreconnect is True and self.heartbeatTimer is None:
                        self.heartbeat()
                    text = ''
                    line = ''
                    while True:
                        if self.terminate is True:
                            break
                        try:
                            line = self.sock.recv(1024)
                            text += line
                        except:
                            pass
                        if "\n\n" in line[-2:]:
                            text = text[:-2]
                            updates = []
                            
                            for f in iter(text.splitlines()):
                                if f == 'BEAT':
                                    self.alive = True
                                try:
                                    logger.debug(f)
                                    j = json.loads(f)
                                    if 'origin' in j and j['origin'] == "update":
                                        updates.append(j)
                                    if 'config' in j and self.getConfigFlag is True:
                                        self.getConfigFlag = False
                                        self.receiver.parse_config(j)
                                        self.daemon.update_devices(self)
                                    if 'status' in j:
                                        logger.debug('Pilight action: ' + j['status'])
                                except KeyError:
                                    pass
                                except ValueError:
                                    pass

                            if len(updates) > 0:
                                self.daemon.user_update(updates)
                                    
                            if self.getConfigFlag is True:
                                self.sender.get_config()
                            
                            text = ""
                        if self.autoreconnect is True and self.alive is False:
                            logger.info('Lost connection to pilight server')
                            self.hasServer = False
                            break
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
                
            if self.autoreconnect is True and self.hasServer is False:
                if self.restartTimer is None:
                    logger.info('Trying to reconnect to pilight in 5 seconds')
                    self.restartTimer = threading.Timer(5, self.restart)
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
        response = self.send_message(message).get_response()
        if response is not False and 'status' in response and response["status"] == "success":
            logger.info('Successfully identified against pilight api')
            return True
        else:
            logger.info('Could not identify against pilight api')
            return False

    def heartbeat(self):
        logger.debug('sending heartbeat to pilight server')
        self.alive = False
        if self.hasServer is True:
            self.send_message('heartbeat')
        self.next_heartbeat += 5
        self.heartbeatTimer = threading.Timer(self.next_heartbeat - time.time(), self.heartbeat)
        self.heartbeatTimer.start()

    def send_message(self, message):
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
    
    def get_response(self):
        text = ''
        line = ''
        while True:
            try:
                line = self.sock.recv(1024)
                text += line
            except:
                pass
            if "\n\n" in line[-2:]:
                text = text[:-2]
                break
            if self.terminate is True:
                break
        try:
            response = json.loads(text)
        except ValueError:
            return False
        
        return response
        
    @staticmethod
    def get_udp_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 0, 10000))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        return sock
        
    def restart(self):
        logger.info('trying to reconnect to pilight server')
        if self.discover():
            self.connect()
            self.restartTimer = None
        else:
            self.restartTimer = threading.Timer(5, self.restart)
            self.restartTimer.start()
    
    def shutdown(self):
        logger.info('shutting down pilight')
        if self.restartTimer is not None:
            self.restartTimer.cancel()
        if self.heartbeatTimer is not None:
            self.heartbeatTimer.cancel()
        self.terminate = True
