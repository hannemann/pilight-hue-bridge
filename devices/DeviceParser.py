from Scene import Scene
from Group import Group
from Light import Light

class DeviceParser(object):
    
    def __init__(self, daemon):
        self.daemon = daemon
        
        self.pilightDevices = {
            'groups':{},
            'lights':{}
        }
        
    def execute(self):
        
        self.initPilight()        
        self.initGroups()
        
        for hueScene in self.daemon.hue.scenes:
            
            for group in self.daemon.devices.groups:
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
        self.daemon.devices.lights[hue.name] = light
    
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
            self.daemon.devices.groups[group.name] = Group(self.daemon, group)
                
    def initScene(self, group, pilightScene, hueScene):
        name = group + '_' + pilightScene['hueName']
        self.daemon.devices.groups[group].addScene(
            pilightScene['hueName'],
            Scene(self.daemon, name, pilightScene, hueScene)
        )            
            
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
        return self.daemon.devices.groups[groupName].hasLights(hueScene.lights) and self.hasPilightScene(groupName, hueScene.name)
        
    def hasPilightScene(self, groupName, sceneName):
        return sceneName in self.pilightDevices['groups'][groupName]['scenes']
    
    
    
    
    
    