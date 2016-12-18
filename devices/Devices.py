from HueSender import HueSender
from DeviceParser import DeviceParser
import logging

logger = logging.getLogger('daemon')


class Devices(object):
    
    performanceLogging = False
    
    groups = {}
    scenes = {}
    lights = {}
    pilightDevices = {
            'groups': {},
            'lights': {},
            'transitions': {}
        }
        
    def __init__(self, daemon):
        """ initialize """        
        self.daemon = daemon
        self.parser = DeviceParser(self)
        logger.info('Devices container initialized')
        
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

    def user_update(self, u):
        """ process device updates """
        config = self.get_update_config(u)
        if config is not False:
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
    
    def recurring_update(self, module=None):
        """ process config updates """
        # return
        if isinstance(module, HueSender):            
            lights = self.daemon.hue.bridge.get_light()
            groups = self.daemon.hue.bridge.get_group()
            for group in self.groups.values():
                group.check_active_scene()
                logger.debug('Group {0} has active scene: {1}'.format(group.name, group.has_active_scene()))
                if group.has_active_scene() is False:
                    hue_group = groups[str(group.id)]
                    logger.debug('Group {0} hue state: {1}'.format(group.name, hue_group['action']['on']))
                    group.sync_with_hue(lights)
            
    def get_update_config(self, u):
        """ parse update """
        device = u['devices'][0]
        if 'hue_' == device[:4]:
            config = self.parser.parse_device_name(device)

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
            return config
        return False
            
    def process_scene(self, config):
        """ process scene """
        if 'toggle' == config['action'] and 'on' == config['state']:
            if self.groups[config['group']].has_active_scene(config['name']) is False:
                logger.info('SCENE: Activate scene ' + config['name'])
                self.groups[config['group']].activate_scene(config['name'])
            
    def process_group(self, config):
        """ process group """
        group = self.groups[config['group']]
        if 'dim' == config['action'] and group.can_modify(config):
            logger.debug('GROUP: Modifying {}'.format(config['group']))
            if config['dimlevel'] is not None:

                logger.info('Deviceaction: Dim group ' + config['group'] + ' to ' + str(config['dimlevel']))
                group.dimlevel = config['dimlevel']

            elif config['state'] is not None:

                if self.groups[config['group']].state != config['state']:
                    logger.info('Deviceaction: Switch group ' + config['group'] + ' ' + config['state'])
                    self.groups[config['group']].state = config['state']
            
    def process_light(self, config):
        """ process light """
        group = self.groups[config['group']]
        light = group.lights[config['name']]
        
        if 'dim' == config['action'] and light.can_modify(config):
            logger.debug('LIGHT: Modifying ' + light.name + ' in group ' + group.name)
            if config['dimlevel'] is not None:
                logger.info('Dim light ' + group.name + ' ' + config['name'] + ' to ' + str(config['dimlevel']))
                light.dimlevel = config['dimlevel']
                
            elif config['state'] is not None:
                logger.info(' Switch light ' + group.name + ' ' + config['name'] + ' ' + config['state'])
                light.state = config['state']
        
        if 'transition' == config['action']:
            if 'on' == config['state']:
                logger.info('Set transtition on light ' + group.name + ' ' + config['name'])
                light.set_transition(config)
                
            elif 'off' == config['state'] is not None:
                logger.info('End transition on light ' + group.name + ' ' + config['name'])
                light.cancel_transition(config)
        
        if 'toggle' == config['action'] and config['state'] is not None:
            logger.info('Switch light ' + group.name + ' ' + config['name'] + ' ' + config['state'])
            light.state = config['state']
    
    def log_performance(self, message):
        if self.performanceLogging is True:
            logger.debug(message)
