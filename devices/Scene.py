
import logging

logger = logging.getLogger('daemon')

class Scene(object):
    
    def __init__(self, daemon, name, pilightScene, hue):
        """ initialize """
        self.daemon = daemon
        self.pilight = daemon.pilight
        
        self.name = hue.name
        self.sceneId = hue.scene_id
        self.pilightName = pilightScene['pilightName']
        self.groupName = pilightScene['group']
        self.groupId = self.daemon.hue.bridge.get_group_id_by_name(self.groupName)        
        self.pilightDevice = self.pilight.devices[self.pilightName]
        self._state = self.pilightDevice['state']
        
        username = self.daemon.hue.bridge.username
        self.hueSettings = self.daemon.hue.bridge.request(
            'GET', '/api/' + username + '/scenes/' + self.sceneId
        )
        self.lightStates = self.hueSettings['lightstates']
    
    @property
    def state(self):
        """ get state """
        return self._state
    
    @state.setter
    def state(self, value):
        """ set state """
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
                self.daemon.hue.bridge.activate_scene(self.groupId, self.sceneId)
    
    def update(self):
        """ update """
        logger.info('update scene ' + self.name)
        
        
        
        
        
        
        
        
        