from Scene import Scene
from Group import Group
from Light import Light

class DeviceParser(object):
    
    def __init__(self, daemon):
        """ initialize """
        self.daemon = daemon
        
        self.pilightDevices = {
            'groups':{},
            'lights':{}
        }
        
    def execute(self):
        """ parse configurations """
        self.initPilightDevices()        
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
    
    def initPilightDevices(self):
        """ initialize pilight devices """
        for device in self.daemon.pilight.devices:
            if device[:4] == 'hue_':
                pilightDevice = self.getPilightDevice(device)
                group = pilightDevice['group']
                name = pilightDevice['name']
                if 'scene' == pilightDevice['type']:
                    self.pilightDevices['groups'][group]['scenes'][name] = pilightDevice
                if 'light' == pilightDevice['type']:                    
                    self.pilightDevices['lights'][name] = pilightDevice
                    
        #self.daemon.debug(self.pilightDevices)
    
    def initGroups(self):
        """ initialize groups """
        for group in self.daemon.hue.groups:
            self.daemon.devices.groups[group.name] = Group(self.daemon, group)

    def initLight(self, pilight, light):
        """ initialize light """
        light = Light(self.daemon, pilight, light)
        self.daemon.devices.lights[light.name] = light
                
    def initScene(self, group, pilightScene, hueScene):
        """ initialize scene """
        name = group + '_' + pilightScene['name']
        self.daemon.devices.groups[group].addScene(
            pilightScene['name'],
            Scene(self.daemon, name, pilightScene, hueScene)
        )            
            
    def getPilightDevice(self, device):
        """ retrieve piligt device """
        pilightConfig = device.split('_')
        type = pilightConfig[1]
        group = pilightConfig[2]
        name = pilightConfig[3]
        if group not in self.pilightDevices['groups']:
            self.addPilightGroup(group)
            
        pilightConfig = self.daemon.pilight.devices[device]
        state = None
        dimlevel = None
        if 'state' in pilightConfig:
            state = pilightConfig['state']
        if 'dimlevel' in pilightConfig:
            dimlevel = pilightConfig['dimlevel']
        return {
            "type": type,
            "name": name,
            "pilightName": device,
            "group": group,
            "state": state,
            "dimlevel": dimlevel
        }
        
    def parseDeviceName(self, device):
        """ parse device name """
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
        """ add pilight group """
        self.pilightDevices['groups'][group] = {
            "scenes":{}
        }
    
    def canAddLight(self, hueLight):
        """ can add light? """
        return hueLight in self.pilightDevices['lights']
    
    def canAddSceneToGroup(self, groupName, hueScene):
        """ can add scene to group? """
        return self.daemon.devices.groups[groupName].hasLights(hueScene.lights) and self.hasPilightScene(groupName, hueScene.name)
        
    def hasPilightScene(self, groupName, sceneName):
        """ has pilight scene? """
        return sceneName in self.pilightDevices['groups'][groupName]['scenes']
    
    
    
    
    
    