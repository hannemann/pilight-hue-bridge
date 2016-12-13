

class Scene(object):
    
    def __init__(self, daemon, name, pilightScene, hueScene):
        """ initialize """
        self.daemon = daemon
        self.hue = daemon.hue
        self.pilight = daemon.pilight
        self.bridge = self.hue.bridge
        
        self.name = hueScene.name
        self.sceneId = hueScene.scene_id
        self.pilightName = pilightScene['pilightName']
        self.groupName = pilightScene['group']
        self.groupId = self.bridge.get_group_id_by_name(self.groupName)        
        self.pilightDevice = self.pilight.devices[self.pilightName]
        self._state = self.pilightDevice['state']
    
    @property
    def state(self):
        return self._state
    
    @state.setter
    def state(self, value):
        if value in ['on', 'off']:
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
    
    def update(self):
        self.daemon.debug('update scene ' + self.name)
        
        
        
        
        
        
        
        
        