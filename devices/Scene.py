
import logging

logger = logging.getLogger('daemon')

class Scene(object):
    
    perfomanceLogging = False
    
    def __init__(self, daemon, name, pilightScene, hue, group):
        """ initialize """
        self.logPerformance('GET == init scene')
        self.daemon = daemon
        self.pilight = daemon.pilight
        
        self.name = hue.name
        self.sceneId = hue.scene_id
        self.pilightName = pilightScene['pilightName']
        self.groupName = pilightScene['group']
        self.groupId = self.daemon.devices.groups[self.groupName].hue.group_id
        self.pilightDevice = self.pilight.devices[self.pilightName]
        self._state = self.pilightDevice['state']
        
        username = self.daemon.hue.bridge.username
        self.hueSettings = self.daemon.hue.bridge.request(
            'GET', '/api/' + username + '/scenes/' + self.sceneId
        )
        self.lightStates = self.hueSettings['lightstates']
        self.logPerformance('GET == init scene end')
    
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
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
        
        
        
        
        
        
        
        
        