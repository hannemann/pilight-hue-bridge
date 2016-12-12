

class Scene(object):
    
    def __init__(self, daemon, name, pilightScene, hueScene):
        self.daemon = daemon
        self.hue = daemon.hue
        self.pilight = daemon.pilight
        self.bridge = self.hue.bridge
        
        self.hueName = hueScene.name
        self.sceneId = hueScene.scene_id
        self.pilightName = pilightScene['pilightName']
        self.groupName = pilightScene['group']
        self.groupId = self.bridge.get_group_id_by_name(self.groupName)        
        self.pilightDevice = self.pilight.devices[self.pilightName]
        self._state = self.pilightDevice['state']
        
        username = self.hue.bridge.username
        
        self.hueSettings = self.hue.bridge.request('GET', '/api/' + username + '/scenes/' + self.sceneId)
        self.lightStates = self.hueSettings['lightstates']
    
    @property
    def name(self):
        return self.hueName
    
    @property
    def state(self):
        return self._state
    
    @state.setter
    def state(self, value):
        if value in ['on', 'off']:
            if self._state != value:
                self._state = value
                message = {
                    "action":"control",
                    "code":{
                        "device":self.pilightName,
                        "state":self._state
                    }
                }
                self.daemon.pilight.sendMessage(message)
                if 'on' == self._state:
                    self.bridge.activate_scene(self.groupId, self.sceneId)
    
    def isActive(self, lights):
        
        if self.hueName == 'Gemuetlich':
            toMatch = len(self.lightStates)
            self.daemon.debug(toMatch)
            for lightId in self.lightStates:
                hueState = lights[lightId]['state']
                selfState = self.lightStates[lightId]
                
                self.daemon.debug(lights[lightId]['name'])
                self.daemon.debug(hueState)
                self.daemon.debug(selfState)
                
                if hueState['on'] == selfState['on'] and hueState['bri'] == selfState['bri']:
                    if 'xy' in selfState:
                        if selfState['xy'][0] == hueState['xy'][0] and selfState['xy'][1] == hueState['xy'][1]:
                            toMatch -= 1
                    else:
                        toMatch -= 1
                        
            self.daemon.debug(toMatch)
            return toMatch == 0
        return False
                            
        
        
        
        
        
        