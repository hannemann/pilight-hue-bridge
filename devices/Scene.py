import logging

logger = logging.getLogger('daemon')


class Scene(object):
    
    performanceLogging = False
    
    def __init__(self, daemon, pilight_scene, hue):
        """ initialize """
        self.log_performance('GET == init scene')
        self.daemon = daemon
        self.pilight = daemon.pilight
        
        self.name = hue.name
        self.sceneId = hue.scene_id
        self.pilightName = pilight_scene['pilightName']
        self.groupName = pilight_scene['group']
        self.groupId = self.daemon.devices.groups[self.groupName].hue.group_id
        self.pilightDevice = self.pilight.devices[self.pilightName]
        self._state = self.pilightDevice['state']
        
        username = self.daemon.hue.bridge.username
        self.hueSettings = self.daemon.hue.bridge.request(
            'GET', '/api/' + username + '/scenes/' + self.sceneId
        )
        self.lightStates = self.hueSettings['lightstates']
        self.log_performance('GET == init scene end')
    
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
                "action": "control",
                "code": {
                    "device": self.pilightName,
                    "state": self._state
                }
            }
            logger.debug('SCENE: switch pilight {0} {1}'.format(self.name, state))
            self.daemon.pilight.send_message(message)
            if 'on' == self._state:
                result = self.daemon.hue.bridge.activate_scene(self.groupId, self.sceneId)[0]
                logger.debug('SCENE: {}'.format(result.keys()[0]))
    
    def update(self):
        """ update """
        logger.info('update scene ' + self.name)
        
    def is_active(self, lights):
        """ determine if scene is currently active within group """
        
        to_match = len(self.lightStates)
        # logger.debug('IsActive: !!!!!!!!!!!!!!!!! Scene {} !!!!!!!!!!!!!!!!'.format(self.name))
        for lightId in self.lightStates:
            real_state = lights[lightId]['state']
            scene_state = self.lightStates[lightId]

            # logger.debug('IsActive: ================= {} ================='.format(lights[lightId]['name']))
            # logger.debug('IsActive: real\ton: {} bri: {} xy: {}'.format(
            #     real_state['on'], real_state['bri'], real_state['xy'] if 'xy' in real_state else None)
            # )
            # logger.debug('IsActive: scene\t{}'.format(scene_state))

            decrement = False
            if real_state['on'] == scene_state['on']:
                if 'bri' in scene_state:
                    if real_state['bri'] == scene_state['bri']:
                        if 'xy' in scene_state:
                            if self.xy_match(scene_state['xy'], real_state['xy']):
                                decrement = True
                        else:
                            decrement = True
                else:
                    decrement = True
                to_match -= 1 if decrement is True else 0
                # logger.debug('IsActive: Match: {}'.format(decrement is True))
                # logger.debug('IsActive: ================= {} ================='.format(lights[lightId]['name']))

        # logger.debug('IsActive result: {}'.format(to_match == 0))
        return to_match == 0
    
    @staticmethod
    def xy_match(scene, real):
        """ xy can drift """
        ranges = [
            [real[0] - 0.005, real[0] + 0.005],
            [real[1] - 0.005, real[1] + 0.005]
        ]
        if ranges[0][0] < scene[0] < ranges[0][1]:
            return ranges[1][0] < scene[1] < ranges[1][1]

        return False
    
    def log_performance(self, message):
        if self.performanceLogging is True:
            logger.debug(message)
