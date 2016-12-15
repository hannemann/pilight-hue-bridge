
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
    def state(self, state):
        """ set state """
        if state in ['on', 'off']:
            self._state = state
            message = {
                "action":"control",
                "code":{
                    "device":self.pilightName,
                    "state":self._state
                }
            }
            self.daemon.pilight.send_message(message)
            if 'on' == self._state:
                success = self.daemon.hue.bridge.activate_scene(self.groupId, self.sceneId)[0]
                logger.debug('{2}: switch scene {0} {1}'.format(self.name, state, 'Success' if success else 'Error'))
    
    def update(self):
        """ update """
        logger.info('update scene ' + self.name)
        
    def isActive(self, group, lights):
        """ determine if scene is currently active within group """
        
        toMatch = len(self.lightStates)
        #logger.debug('IsActive: ================= Scene {} ==============='.format(self.name))
        for lightId in self.lightStates:
            realState = lights[lightId]['state']
            sceneState = self.lightStates[lightId]

            #logger.debug('IsActive: ================= {} ================='.format(lights[lightId]['name']))
            #logger.debug('IsActive: real {}'.format(realState))
            #logger.debug('IsActive: scene {}'.format(sceneState))

            if realState['on'] == sceneState['on']:
                if 'bri' in sceneState:
                    if realState['bri'] == sceneState['bri']:
                        if 'xy' in sceneState:
                            if self.xyMatch(sceneState['xy'], realState['xy']):
                                toMatch -= 1
                        else:
                            toMatch -= 1
                else:
                    toMatch -= 1
                #logger.debug('IsActive : ================= {} ================='.format(lights[lightId]['name']))

        #logger.debug('IsActive result: {}'.format(toMatch == 0))
        return toMatch == 0
    
    def xyMatch(self, scene, real):
        """ xy can drift """
        ranges=[
            [real[0] - 0.005, real[0] + 0.005],
            [real[1] - 0.005, real[1] + 0.005]
        ]
        return scene[0] > ranges[0][0] and scene[0] < ranges[0][1] \
            and scene[1] > ranges[1][0] and scene[1] < ranges[1][1]
    
    def logPerformance(self, message):
        if self.perfomanceLogging is True:
            logger.debug(message)
        
        
        
        
        
        
        
        
        