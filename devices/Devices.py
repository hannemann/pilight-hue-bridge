from HueSender import HueSender
from Pilight import Pilight
from DeviceParser import DeviceParser
import logging

logger = logging.getLogger('daemon')

class Devices():
    
    perfomanceLogging = False
    
    groups = {}
    scenes = {}
    lights = {}
    pilightDevices = {
            'groups':{},
            'lights':{}
        }
        
    def __init__(self, daemon):
        """ initialize """        
        self.daemon = daemon
        self.parser = DeviceParser(self)
        logger.info('Devices container initialized')
        
    def initDevices(self):
        """ initialize devices """
        self.logPerformance('GET ============ Start init devices ================')
        self.parser.execute()
        self.logPerformance('GET ============ Stop init devices ================')
        self.logPerformance('PUT ============ Start sync with pilight ==========')
        self.syncWithPilight()
        self.logPerformance('PUT ============ Stop sync with pilight ==========')
        
    def syncWithPilight(self):
        """ sync hue devices with pilight devices """
        groups = self.pilightDevices['groups']
        for name in groups:
            if name in self.groups:
                self.groups[name].syncWithPilight()

    def update(self, u):
        """ process device updates """
        config = self.getUpdateConfig(u)
        if config is not False:            
            """
            logger.debug(config)
            logger.debug(config['state'])
            logger.debug(config['dimlevel'])
            """
            if 'scene' == config['type']:
                """ process scene """
                self.processScene(config)
                
            if 'group' == config['type']:
                """ process group """
                self.processGroup(config)
                
            if 'light' == config['type']:
                """ process light """
                self.processLight(config)
    
    def updateDevices(self, module = None):
        """ process config updates """
        if isinstance(module, HueSender):            
            lights = self.daemon.hue.bridge.get_light()
            """ groups example
            {u'1': {u'name': u'Wohnzimmer', u'lights': [u'9', u'1', u'2', u'3', u'4', u'5', u'6'], u'state': {u'any_on': True, u'all_on': True}, u'action': {u'on': True, u'hue': 2730, u'colormode': u'xy', u'effect': u'none', u'alert': u'select', u'xy': [0.6007, 0.3909], u'bri': 150, u'ct': 500, u'sat': 254}, u'type': u'Room', u'class': u'Living room'}, u'2': {u'name': u'Schlafzimmer', u'lights': [u'8'], u'state': {u'any_on': True, u'all_on': True}, u'action': {u'on': True, u'bri': 254, u'alert': u'none'}, u'type': u'Room', u'class': u'Bedroom'}}
            """
            groups = self.daemon.hue.bridge.get_group()
            for group in self.groups.values():
                group.syncActiveScene(lights)
                logger.debug('Group {0} has active scene: {1}'.format(group.name, group.hasActiveScene()))
                if group.hasActiveScene() is False:
                    hueGroup = groups[str(group.id)]
                    logger.debug('Group {0} hue state: {1}'.format(group.name, hueGroup['state']))
                    group.syncLights(lights, hueGroup)
            
    def getUpdateConfig(self, u):
        """ parse update """
        device = u['devices'][0]
        if 'hue_' == device[:4]:
            config = self.parser.parseDeviceName(device)
            
            values = None
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
            
    def processScene(self, config):
        """ process scene """
        if 'toggle' == config['action'] and 'on' == config['state']:
            
            logger.info('Deviceaction: Activate scene ' + config['name'])
            self.groups[config['group']].activateScene(config['name'])
            
    def processGroup(self, config):
        """ process group """
        if 'bri' == config['action'] and config['dimlevel'] is not None:
            
            logger.info('Deviceaction: Dim group ' + config['group'] + ' to ' + str(config['dimlevel']))
            self.groups[config['group']].dimlevel = config['dimlevel']
            
        if 'bri' == config['action'] and config['state'] is not None and config['dimlevel'] is None:
            
            if self.groups[config['group']].state != config['state']:
                logger.info('Deviceaction: Switch group ' + config['group'] + ' ' + config['state'])
                self.groups[config['group']].state = config['state']
            
    def processLight(self, config):
        """ process light """
        group = self.groups[config['group']]
        light = group.lights[config['name']]
        logger.debug('Modifying light ' + light.name + ' in group ' + group.name)        
        
        if 'bri' == config['action']:
            if config['dimlevel'] is not None:
                logger.info('Dim light ' + group.name + ' ' + config['name'] + ' to ' + str(config['dimlevel']))
                light.dimlevel = config['dimlevel']
                
            elif config['state'] is not None:
                logger.info(' Switch light ' + group.name + ' ' + config['name'] + ' ' + config['state'])
                light.state = config['state']
        
        if 'transition' == config['action']:
            if 'on' == config['state']:
                logger.info('Set transtition on light ' + group.name + ' ' + config['name'])
                light.setTransition(config)
                
            elif 'off' == config['state'] is not None:
                logger.info('Switch light ' + group.name + ' ' + config['name'] + ' ' + config['state'])
                light.state = config['state']
        
        if 'toggle' == config['action'] and config['state'] is not None:
            logger.info('Switch light ' + group.name + ' ' + config['name'] + ' ' + config['state'])
            light.state = config['state']
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)




    
    
    
    
    