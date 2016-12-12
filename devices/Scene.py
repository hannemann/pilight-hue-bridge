

class Scene(object):
    
    def __init__(self, daemon, name, pilightScene, hueScene):
        self.daemon = daemon
        self.hue = daemon.hue
        self.pilight = daemon.pilight
        self.bridge = self.hue.bridge
        
        self.hueName = hueScene.name
        self.pilightName = pilightScene['pilightName']
        self.group = pilightScene['group']
        
        self.pilightDevice = self.pilight.devices[self.pilightName]
        self._state = self.pilightDevice['state']
        
    @property
    def name(self):
        return self.hueName
    
    @property
    def state(self):
        self.daemon.debug('get state')
        return self._state
    
    @state.setter
    def state(self, value):
        self.daemon.debug('set state')
        if value in ['on', 'off']:
            self._state = value
    
    def update(self):
        self.daemon.debug('update scene ' + self.name)