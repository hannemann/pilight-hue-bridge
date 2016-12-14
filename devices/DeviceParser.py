from Scene import Scene
from Group import Group
from Light import Light
import logging

logger = logging.getLogger('daemon')

class DeviceParser(object):
    
    perfomanceLogging = False
    
    def __init__(self, container):
        """ initialize """
        self.daemon = container.daemon
        self.container = container
        
    def execute(self):
        """ parse configurations """
        self.logPerformance('GET ========== Start parsing devices ================')
        self.logPerformance('GET ======== init pilights')
        self.initPilightDevices()        
        self.logPerformance('GET ======== init pilights end')
        self.logPerformance('GET ======== init groups')
        self.initGroups()
        self.logPerformance('GET ======== init groups end')

        self.logPerformance('GET ======== init lights')
        for light in self.daemon.hue.lights:
            self.logPerformance('GET ====== init light')
            hueValues = light._get()
            if self.canAddLight(hueValues['name']):
                self.initLight(self.container.pilightDevices['lights'][hueValues['name']], light, hueValues)
            self.logPerformance('GET ====== init light end')
        self.logPerformance('GET ======== init lights end')
        
        self.logPerformance('GET ======== parse scenes')
        for hueScene in self.daemon.hue.scenes:
            
            self.logPerformance('GET ====== init scene - iterate devices container scene')
            for groupName in self.container.groups:
                self.logPerformance('GET ==== init scene - iterate devices container groups')
                if self.canAddSceneToGroup(groupName, hueScene):
                    self.initScene(
                        groupName,
                        self.container.pilightDevices['groups'][groupName]['scenes'][hueScene.name],
                        hueScene
                    )
                    break
                self.logPerformance('GET ==== init scene - iterate devices container groups end')
            self.logPerformance('GET ====== init scene - iterate devices container scene end')
        self.logPerformance('GET ======== parse scenes end')
                
        self.logPerformance('GET ========== Stop parsing devices ================')
    
    def initPilightDevices(self):
        """ initialize pilight devices """
        for device in self.daemon.pilight.devices:
            if device[:4] == 'hue_':
                pilightDevice = self.getPilightDevice(device)
                group = pilightDevice['group']
                name = pilightDevice['name']
                if 'scene' == pilightDevice['type']:
                    self.container.pilightDevices['groups'][group]['scenes'][name] = pilightDevice
                if 'light' == pilightDevice['type']:                    
                    self.container.pilightDevices['lights'][name] = pilightDevice
    
    def initGroups(self):
        """ initialize groups """
        for group in self.daemon.hue.groups:
            hueValues = group._get()
            self.container.groups[group.name] = Group(self.daemon, group, hueValues)

    def initLight(self, pilight, light, hueValues):
        """ initialize light """
        light = Light(self.daemon, pilight, light, hueValues)
        self.container.groups[pilight['group']].addLight(
            pilight['name'], light
        )
                
    def initScene(self, group, pilightScene, hueScene):
        """ initialize scene """
        name = group + '_' + pilightScene['name']
        self.container.groups[group].addScene(
            pilightScene['name'],
            Scene(self.daemon, name, pilightScene, hueScene, group)
        )            
            
    def getPilightDevice(self, device):
        """ retrieve piligt device """
        pilightConfig = device.split('_')
        type = pilightConfig[1]
        group = pilightConfig[2]
        name = pilightConfig[3]
        if group not in self.container.pilightDevices['groups']:
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
        self.container.pilightDevices['groups'][group] = {
            "scenes":{}
        }
    
    def canAddLight(self, hueLight):
        """ can add light? """
        return hueLight in self.container.pilightDevices['lights']
    
    def canAddSceneToGroup(self, groupName, hueScene):
        """ can add scene to group? """
        self.logPerformance('GET === test if device is handled by pilight')
        return self.container.groups[groupName].hasLights(hueScene.lights) \
               and self.hasPilightScene(groupName, hueScene.name)
        
    def hasPilightScene(self, groupName, sceneName):
        """ has pilight scene? """
        return sceneName in self.container.pilightDevices['groups'][groupName]['scenes']
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
    
    
    
    
    
    