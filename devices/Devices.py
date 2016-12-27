from Hue import Hue
from DeviceParser import DeviceParser
import threading
import time
import logging

logger = logging.getLogger('daemon')


class Devices(threading.Thread):

    performanceLogging = False
    
    groups = {}
    scenes = {}
    lights = {}
    transitions = {}
    pilightDevices = {
            'groups': {},
            'lights': {},
            'transitions': {}
        }
        
    def __init__(self, daemon):
        """ initialize """
        threading.Thread.__init__(self, name='devices')
        self.daemon = daemon
        self.parser = DeviceParser(self)
        self.lock = threading.Lock()
        logger.info('Devices container initialized')

    def run(self):
        while True:
            time.sleep(0.1)
        
    def init_devices(self):
        """ initialize devices """
        self.log_performance('GET ============ Start init devices ================')
        self.parser.execute()
        self.log_performance('GET ============ Stop init devices ================')
        self.log_performance('PUT ============ Start sync with pilight ==========')
        self.sync_with_pilight()
        self.log_performance('PUT ============ Stop sync with pilight ==========')
        
    def sync_with_pilight(self):
        """ sync hue devices with pilight devices """
        groups = self.pilightDevices['groups']
        for name in groups:
            if name in self.groups:
                self.groups[name].sync_with_pilight()

    def user_update(self, updates):
        """ process device updates """
        configs = self.get_update_config(updates)
        if len(configs) > 0:
            logger.debug('USER_UPDATE: got {} updates'.format(len(configs)))
            if not self.lock.acquire(False):
                logger.debug('USER-UPDATE: update in progress... blocked user input')
            else:
                try:
                    for config in configs:
                        logger.debug('USER-UPDATE: update in progress... blocking further input')
                        """
                        logger.debug(config)
                        logger.debug(config['state'])
                        logger.debug(config['dimlevel'])
                        """
                        if 'scene' == config['type']:
                            """ process scene """
                            self.process_scene(config)

                        if 'group' == config['type']:
                            """ process group """
                            self.process_group(config)

                        if 'light' == config['type']:
                            """ process light """
                            self.process_light(config)
                finally:
                    logger.debug('USER-UPDATE: update ready... releasing lock')
                    self.lock.release()
    
    def recurring_update(self, module=None):
        """ process config updates """
        if isinstance(module, Hue):

            if not self.lock.acquire(False):
                logger.debug('RECURRING-UPDATE: update in progress... blocked update from bridge')
            else:
                try:
                    lights = self.daemon.hue.bridge.get_light()
                    messages = []
                    for hue_values in lights.values():
                        for group in self.groups.values():
                            if group.has_light(hue_values['name']):
                                light = group.get_light(hue_values['name'])
                                hue_state = hue_values['state']
                                on_state = 'on' if hue_state['on'] else 'off'
                                if hue_state['on'] and hue_state['bri'] != light.dimlevel:
                                    light.pilight.update_dimlevel(hue_state['bri'])
                                    light.hue.update_dimlevel(hue_state['bri'])
                                    message = light.pilight.get_message()
                                    messages.append(message)
                                if on_state != light.state:
                                    light.pilight.update_state(on_state)
                                    light.hue.update_state(on_state)
                                    message = light.pilight.get_switch_message()
                                    messages.append(message)

                    if len(messages) > 0:
                        self.daemon.pilight.send_message(messages)
                        for group in self.groups.values():
                            group.check_active_scene()
                finally:
                    self.lock.release()
        return

    def get_update_config(self, updates):
        """ parse update """
        result = []
        for u in updates:
            device = u['devices'][0]
            if 'hue_' == device[:4]:
                config = self.parser.parse_device_name(device)
                if 'origin' in u:
                    config['origin'] = u['origin']

                state = None
                dimlevel = None
                if 'values' in u:
                    values = u['values']

                    if 'state' in values:
                        state = u['values']['state']

                    if 'dimlevel' in values:
                        dimlevel = u['values']['dimlevel']

                config['state'] = state
                config['dimlevel'] = dimlevel
                result.append(config)
        return result
            
    def process_scene(self, config):
        """ process scene """
        if 'toggle' == config['action'] and 'on' == config['state']:
            if self.groups[config['group']].has_active_scene(config['name']) is False:
                logger.info('SCENE: Activate scene ' + config['name'])
                group = self.groups[config['group']]
                scene = group.get_scene(config['name'])
                scene.pilight.lock_send = config
                group.activate_scene(scene.name)
                scene.pilight.lock_send = False
            
    def process_group(self, config):
        """ process group """
        group = self.groups[config['group']]
        if 'dim' == config['action'] and group.can_modify(config):
            logger.debug('GROUP: Modifying {}'.format(config['group']))
            group.pilight.lock_send = config
            if config['dimlevel'] is not None:

                logger.info('Deviceaction: Dim group ' + config['group'] + ' to ' + str(config['dimlevel']))
                group.dimlevel = config['dimlevel']

            elif config['state'] is not None:

                if self.groups[config['group']].state != config['state']:
                    logger.info('Deviceaction: Switch group ' + config['group'] + ' ' + config['state'])
                    self.groups[config['group']].state = config['state']
            group.pilight.lock_send = False
            
    def process_light(self, config):
        """ process light """

        if 'dim' == config['action']:
            group = self.groups[config['group']]
            light = group.lights[config['name']]

            if light.can_modify(config):
                logger.debug('LIGHT: Modifying ' + light.name + ' in group ' + group.name)
                light.pilight.lock_send = config
                if config['dimlevel'] is not None:
                    logger.info('Dim light ' + group.name + ' ' + config['name'] + ' to ' + str(config['dimlevel']))
                    light.dimlevel = config['dimlevel']

                elif config['state'] is not None:
                    logger.info(' Switch light ' + group.name + ' ' + config['name'] + ' ' + config['state'])
                    light.state = config['state']
                light.pilight.lock_send = False

        if 'toggle' == config['action'] and config['state'] is not None:
            group = self.groups[config['group']]
            light = group.lights[config['name']]
            light.pilight.lock_send = config
            logger.info('Switch light ' + group.name + ' ' + config['name'] + ' ' + config['state'])
            light.state = config['state']
            light.pilight.lock_send = False
        
        if 'transition' == config['action']:
            transition = self.transitions[config['pilight_device']]
            if 'on' == config['state']:
                logger.info('Set transition on light ' + config['name'])
                transition.start()
                
            else:
                logger.info('End transition on light ' + config['name'])
                transition.cancel()
    
    def log_performance(self, message):
        if self.performanceLogging is True:
            logger.debug(message)
