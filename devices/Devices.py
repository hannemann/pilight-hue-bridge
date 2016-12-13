from HueSender import HueSender
from Pilight import Pilight
from Scene import Scene
from Group import Group
from Light import Light

class Devices():
    
    devices = {}
    
    def __init__(self, daemon):
        
        self.groups = {}
        self.scenes = {}
        self.lights = {}
        
        self.pilightDevices = {
            'groups':{},
            'lights':{}
        }
        
        self.daemon = daemon
        self.daemon.debug('Devices container initialized')
        
    def initDevices(self):
        
        self.initPilight()        
        self.initGroups()
        
        for hueScene in self.daemon.hue.scenes:
            
            for group in self.groups:
                if self.canAddSceneToGroup(group, hueScene):
                    self.initScene(
                        group,
                        self.pilightDevices['groups'][group]['scenes'][hueScene.name],
                        hueScene
                    )
                    break

        for light in self.daemon.hue.lights:
            if self.canAddLight(light.name):
                self.initLight(self.pilightDevices['lights'][light.name], light)
            
        #self.daemon.debug(self.lights)

    def initLight(self, pilight, hue):
        light = Light(self.daemon, pilight, hue)
        self.lights[hue.name] = light
    
    def initPilight(self):
        for device in self.daemon.pilight.devices:
            if device[:4] == 'hue_':
                pilightDevice = self.getPilightDevice(device)
                group = pilightDevice['group']
                name = pilightDevice['hueName']
                if 'scene' == pilightDevice['type']:
                    self.pilightDevices['groups'][group]['scenes'][name] = pilightDevice
                if 'light' == pilightDevice['type']:
                    self.pilightDevices['lights'][name] = pilightDevice
                    
        #self.daemon.debug(self.pilightDevices)
    
    def initGroups(self):
        for group in self.daemon.hue.groups:
            self.groups[group.name] = Group(self.daemon, group)
                
    def initScene(self, group, pilightScene, hueScene):
        name = group + '_' + pilightScene['hueName']
        self.groups[group].addScene(
            pilightScene['hueName'],
            Scene(self.daemon, name, pilightScene, hueScene)
        )

    def update(self, u):
        
        device = u['devices'][0]
        if 'hue_' == device[:4]:
            config = self.parseDeviceName(device)
            
            values = None
            state = None
            dimlevel = None
            if 'values' in u:
                values = u['values']
                
                if 'state' in values:
                    state = u['values']['state']
                    
                if 'dimlevel' in values:
                    dimlevel = u['values']['dimlevel']
            
            """
            self.daemon.debug(config)
            self.daemon.debug(state)
            self.daemon.debug(dimlevel)
            """
            if 'scene' == config['type'] and 'toggle' == config['action'] and 'on' == state:
                
                self.daemon.debug('Deviceaction: Activate scene ' + config['name'])
                self.groups[config['group']].activateScene(config['name'])
                
            if 'group' == config['type'] and 'bri' == config['action'] and dimlevel is not None:
                
                self.daemon.debug('Deviceaction: Dim group ' + config['group'] + ' to ' + str(dimlevel))
                self.groups[config['group']].dim(device, dimlevel)
                
            if 'group' == config['type'] and 'off' == state:
                
                self.daemon.debug('Deviceaction: Switch group ' + config['group'] + ' off')
                self.groups[config['group']].state = 'off'
                
            if 'light' == config['type'] and 'bri' == config['action']:
                
                if dimlevel is not None:
                    self.daemon.debug('Deviceaction: Dim light ' + config['name'] + ' to ' + str(dimlevel))
                    self.lights[config['name']].dim(dimlevel)
                    
                if config['transitiontime'] is not None and 'on' == state:
                    self.daemon.debug('Deviceaction: Set transtition on light ' + config['name'])
                    self.lights[config['name']].setTransition(config)
                    
                if 'off' == state:
                    self.daemon.debug('Deviceaction: Switch light ' + config['name'] + ' off')
                    self.lights[config['name']].state = 'off'
    
    def updateDevices(self, module = None):
    
        if isinstance(module, HueSender):
            self.daemon.debug('TODO: parse hue updates')
            
            
    def getPilightDevice(self, device):
        pilightConfig = device.split('_')
        type = pilightConfig[1]
        group = pilightConfig[2]
        name = pilightConfig[3]
        if group not in self.pilightDevices['groups']:
            self.addPilightGroup(group)
        return {
            "type": type,
            "hueName": name,
            "pilightName": device,
            "group": group
        }
        
    def parseDeviceName(self, device):
        maxLen = 8
        config = device.split('_')
        config = config + [None] * (maxLen - len(config))
        hue, type, group, name, action, fromBri, toBri, tr = config
        return {
            "type": type,
            "group": group,
            "name": name,
            "action": action,
            "fromBri": fromBri,
            "toBri": toBri,
            "transitiontime": tr
        }
    
    def addPilightGroup(self, group):
        self.pilightDevices['groups'][group] = {
            "scenes":{}
        }
    
    def canAddLight(self, hueLight):
        return hueLight in self.pilightDevices['lights']
    
    def canAddSceneToGroup(self, groupName, hueScene):
        return self.groups[groupName].hasLights(hueScene.lights) and self.hasPilightScene(groupName, hueScene.name)
        
    def hasPilightScene(self, groupName, sceneName):
        return sceneName in self.pilightDevices['groups'][groupName]['scenes']