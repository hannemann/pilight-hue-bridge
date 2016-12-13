from HueSender import HueSender
from Pilight import Pilight
from DeviceParser import DeviceParser

class Devices():
    
    devices = {}
    
    def __init__(self, daemon):
        """ initialize """
        self.groups = {}
        self.scenes = {}
        self.lights = {}
        
        self.daemon = daemon
        self.parser = DeviceParser(self.daemon)
        self.daemon.debug('Devices container initialized')
        
    def initDevices(self):
        """ initialize devices """
        self.parser.execute()

    def update(self, u):
        """ process device updates """
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
            
            """
            self.daemon.debug(config)
            self.daemon.debug(config['state'])
            self.daemon.debug(config['dimlevel'])
            """
            if 'scene' == config['type']:
                """ process scene """
                self.processScene(config)
                
            if 'group' == config['type']:
                """ process group """
                self.processGroup(config, device)
                
            if 'light' == config['type'] and 'bri' == config['action']:
                """ process light """
                self.processLight(config)
    
    def updateDevices(self, module = None):
        """ process config updates """
        if isinstance(module, HueSender):
            self.daemon.debug('TODO: parse hue updates')
            
    def processScene(self, config):
        """ process scene """
        if 'toggle' == config['action'] and 'on' == config['state']:
            
            self.daemon.debug('Deviceaction: Activate scene ' + config['name'])
            self.groups[config['group']].activateScene(config['name'])
            
    def processGroup(self, config, device):
        """ process group """
        if 'bri' == config['action'] and config['dimlevel'] is not None:
            
            self.daemon.debug('Deviceaction: Dim group ' + config['group'] + ' to ' + str(config['dimlevel']))
            self.groups[config['group']].dim(device, config['dimlevel'])
            
        if 'bri' == config['action'] and config['state'] is not None and config['dimlevel'] is None:
            
            if self.groups[config['group']].state != config['state']:
                self.daemon.debug('Deviceaction: Switch group ' + config['group'] + ' ' + config['state'])
                self.groups[config['group']].state = config['state']
            
    def processLight(self, config):
        """ process light """
        if config['dimlevel'] is not None:
            self.daemon.debug('Deviceaction: Dim light ' + config['name'] + ' to ' + str(config['dimlevel']))
            self.lights[config['name']].dim(config['dimlevel'])
            
        if config['transitiontime'] is not None and 'on' == config['state']:
            self.daemon.debug('Deviceaction: Set transtition on light ' + config['name'])
            self.lights[config['name']].setTransition(config)
            
        if 'off' == config['state']:
            self.daemon.debug('Deviceaction: Switch light ' + config['name'] + ' off')
            self.lights[config['name']].state = 'off'




    
    
    
    
    