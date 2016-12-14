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
        
    def __init__(self, daemon):
        """ initialize """        
        self.daemon = daemon
        self.parser = DeviceParser(self.daemon)
        logger.info('Devices container initialized')
        
    def initDevices(self):
        """ initialize devices """
        self.logPerformance('GET ============ Start init devices ================')
        self.parser.execute()
        self.logPerformance('GET ============ Stop init devices ================')

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
            logger.debug('TODO: parse hue updates')
            
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
            self.groups[config['group']].dim(config['dimlevel'])
            
        if 'bri' == config['action'] and config['state'] is not None and config['dimlevel'] is None:
            
            if self.groups[config['group']].state != config['state']:
                logger.info('Deviceaction: Switch group ' + config['group'] + ' ' + config['state'])
                self.groups[config['group']].state = config['state']
            
    def processLight(self, config):
        """ process light """
        group = self.groups[config['group']]
        logger.debug('Modifying light ' + config['name'] + ' in group ' + group.name)
        
        if group.lockLightStates is False:
            logger.debug(group.name + ' is not locked')
            light = group.lights[config['name']]
            
            if 'bri' == config['action']:
                if config['dimlevel'] is not None:
                    logger.info('Dim light ' + group.name + ' ' + config['name'] + ' to ' + str(config['dimlevel']))
                    light.dim(config['dimlevel'])
                    
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
        else:
            logger.debug(group.name + ' is locked')
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)




    
    
    
    
    