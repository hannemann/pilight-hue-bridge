import logging
from Switchable import Switchable

logger = logging.getLogger('daemon')


class Scene(Switchable):
    
    performanceLogging = False
    
    def __init__(self, daemon, hue_values, hue_id, group_name):
        """ initialize """
        Switchable.__init__(self, daemon, hue_values, hue_id)
        self.log_performance('GET == init scene')
        self.type = 'scene'
        self.groupName = group_name
        self.lightName = self.name
        self.groupId = self.daemon.devices.groups[self.groupName].id
        self.lightStates = self.get_light_states()
        self.init_pilight_device()
        self.log_performance('GET == init scene end')

    def switch_hue(self, state):
        """ switch hue device """
        if 'on' == state:
            result = self.daemon.hue.bridge.activate_scene(self.groupId, self.id)[0]
            logger.debug('SCENE: {}'.format(result.keys()[0]))

        return True

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

    def get_light_states(self):
        username = self.daemon.hue.bridge.username
        hue_settings = self.daemon.hue.bridge.request(
            'GET', '/api/' + username + '/scenes/' + self.id
        )
        return hue_settings['lightstates']

    def log_performance(self, message):
        if self.performanceLogging is True:
            logger.debug(message)
