#!/usr/bin/env python

import os
import sys
import getopt
import time
import signal
import json
from config import config
from config import ConfigParser
from Pilight import Pilight
from Pilight import PilightException
from Hue import Hue
from Hue import HueException
from devices.Devices import Devices
import threading
import logging

logFormat = '%(asctime)s %(name)s\t%(levelname)s:\t'
logFormat += '%(message)s, (%(module)s, %(lineno)d)'

logging.basicConfig(level=logging.ERROR, format=logFormat)
logger = logging.getLogger('daemon')


class PilightHueBridge(object):
    
    terminate = False
    modules = ['Pilight', 'HueSender']
    devicesInitialized = False
    
    def __init__(self, debug_mode=False):
        self.logging = {"mode": "d", "d-level": logging.INFO}
        self.config = config
        self.init_logging(debug_mode)
        try:
            self.pilight = Pilight(self, 5)
            self.hue = Hue(self)
        except (HueException, PilightException) as exc:
            logger.critical(exc.message)
            logger.critical('could not initialize')
            sys.exit(1)
        self.devices = Devices(self)
        logger.info('Daemon initialized')
        
    def init_logging(self, debug_mode):

        if debug_mode is False:
            try:
                debug_mode = self.config.get('general', 'debug')
            except ConfigParser.NoSectionError:
                debug_mode = False
            except ConfigParser.NoOptionError:
                debug_mode = False

        if debug_mode is not False:
            if ':' in debug_mode:
                mode, levels = debug_mode.split(':')
            else:
                mode = debug_mode
                levels = 'info'
            
            if ',' in levels:
                levels = levels.split(',')
            else:
                levels = [levels]
            
            level = logging.INFO
            for i, m in enumerate(mode):
                if i < len(levels):
                    level = levels[i].upper()
                    if hasattr(logging, level):
                        level = getattr(logging, level)
                self.logging[m + '-level'] = level
                
            self.logging['mode'] = str(mode)

        logger.setLevel(self.logging['d-level'])
        
    def update_devices(self, module):
        
        if self.devicesInitialized is False:
            if 'Pilight' in self.modules and isinstance(module, Pilight):
                self.modules.remove('Pilight')
            elif 'HueSender' in self.modules and isinstance(module, Hue):
                self.modules.remove('HueSender')

            if len(self.modules) == 0:
                self.devices.init_devices()
                self.devicesInitialized = True
        else:
            self.devices.recurring_update(module)
        
    def user_update(self, update):
        threading.Timer(0.01, self.devices.user_update, [update]).start()
        
    @staticmethod
    def dump_json(obj):
        print(
            json.dumps(
                obj,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
            )
        )

    def run(self):
        logger.info('Daemon PID: %s' % os.getpid())
        self.pilight.start()
        self.hue.start()
        while True:
            if self.terminate:
                logger.info('Terminated')
                break
            
            time.sleep(2)    
             
    def shutdown(self):
        logger.info('Catched SIGTERM')
        self.pilight.shutdown()
        self.hue.shutdown()
        self.terminate = True   


def usage(with_config=False):
    """ print help message """
    print '\n\tBridge pilight with hue\n'
    print '\n\tUsage:\n'
    print '\t\t-h\tHelp'
    print '\t\t-c\tHelp with pilight configuration examples'
    print '\t\t-d\tDebug mode: modes and levels separated by colon, levels separated by comma'
    print '\t\t\tmodes: d=main program, a=hue api, p=pilight module, h=hue module'
    print '\t\t\tlevels: debug, info, warning, error, critical'
    print '\t\t\te.g.:\t-d dpa:debug,info to set debug on main program, info on pilight'
    print '\t\t\t\tand info on hue api (because explicit level on a is omitted)'
    print '\t\t\tDebug mode can also be set via configuration file'
    print '\n\tRestart program if pilight has been restarted.'
    if with_config:
        print '\tFor convenience add a program device to your pilight configuration:'
        print '\n'
        print '\tDevice:'
        print '\t"bridge_to_hue": {'
        print '\t\t"protocol": [ "program" ],'
        print '\t\t\t"id": [{'
        print '\t\t\t\t"name": "hue-bridge"'
        print '\t\t\t}],'
        print '\t\t"program": "python",'
        print '\t\t"arguments": "/home/pi/PilightHueBridge/PilightHueBridge.py",'
        print '\t\t"stop-command": "systemctl stop pilight-hue-bridge.service",'
        print '\t\t"start-command": "systemctl start pilight-hue-bridge.service",'
        print '\t\t"state": "stopped",'
        print '\t\t"pid": 0,'
        print '\t\t"poll-interval": 5'
        print '\t}'
        print '\n'
        print '\tGui:'
        print '\t"bridge_to_hue": {'
        print '\t\t"name": "HUE Bridge",'
        print '\t\t"group": ["Name"]'
        print '\t}'
        print '\n'
        print '\tDevices configuration:\n'
        print '\tpilight devices must respect a naming convention'
        print '\tevery device starts with \'hue_\' and is split into parts by underscores'
        print '\tsecond part:\ttype of hue device: light, scene, group'
        print '\tthird part:\tname of the hue group of the device/scene'
        print '\tfourth part:\tname of the device itself, \'all\' for groups'
        print '\tfifth part:\taction: dim, toggle, transition'
        print '\tsixth part:\ttransition only: start dimlevel'
        print '\tseventh part:\ttransition only: end dimlevel (if zero, hue light is turned of afterwards)'
        print '\teighth part:\ttransition only: duration in seconds/10 (4 = 400ms, 18000 = 30 * 60 * 10 = 30 minutes)'
        print '\n\tHue light:'
        print '\t"hue_light_Huegroupname_Huedevicename_dim": {'
        print '\t\t"protocol": ["generic_dimmer"],'
        print '\t\t"id": [{'
        print '\t\t\t"id": 38'
        print '\t\t}],'
        print '\t\t"state": "off",'
        print '\t\t"dimlevel": 148,'
        print '\t\t"dimlevel-minimum": 0,'
        print '\t\t"dimlevel-maximum": 254'
        print '\t}'
        print '\n\tHue group:'
        print '\t"hue_group_Huegroupname_all_dim": {'
        print '\t\t"protocol": ["generic_dimmer"],'
        print '\t\t"id": [{'
        print '\t\t\t"id": 24'
        print '\t\t}],'
        print '\t\t"state": "on",'
        print '\t\t"dimlevel": 145,'
        print '\t\t"dimlevel-minimum": 0,'
        print '\t\t"dimlevel-maximum": 254'
        print '\t}'
        print '\n\tHue scene:'
        print '\t"hue_scene_Huegroupname_Huescenename_toggle": {'
        print '\t\t"protocol": ["generic_switch"],'
        print '\t\t"id": [{'
        print '\t\t\t"id": 25'
        print '\t\t}],'
        print '\t\t"state": "off"'
        print '\t}'
        print '\n\tHue transition: (dims from 1 to 254 in 30 minutes)'
        print '\t"hue_light_Huegroupname_Huedevicename_transition_1_254_18000": {'
        print '\t\t"protocol": ["generic_switch"],'
        print '\t\t"id": [{'
        print '\t\t\t"id": 27'
        print '\t\t}],'
        print '\t\t"state": "off"'
        print '\t}'
    print '\n'

if __name__ == "__main__":
    debug = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:hc", ["help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        if opt == '-c':
            usage(True)
            sys.exit(0)
        if opt == '-d':
            debug = arg
    
    bridge = PilightHueBridge(debug)
    signal.signal(signal.SIGTERM, bridge.shutdown)
    bridge.run()
