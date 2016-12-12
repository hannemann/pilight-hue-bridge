from HueSender import HueSender
from Pilight import Pilight
from Scene import Scene
from Group import Group

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
                
        self.daemon.debug(self.groups['Wohnzimmer'].getScene('Hell'))
    
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
    
    def update(self, module):
        if isinstance(module, HueSender):
            self.daemon.debug('parse hue updates')
            
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
    
    def addPilightGroup(self, group):
        self.pilightDevices['groups'][group] = {
            "scenes":{}
        }
        
    def canAddSceneToGroup(self, groupName, hueScene):
        return self.groups[groupName].hasLights(hueScene.lights) and self.hasPilightScene(groupName, hueScene.name)
        
    def hasPilightScene(self, groupName, sceneName):
        return sceneName in self.pilightDevices['groups'][groupName]['scenes']