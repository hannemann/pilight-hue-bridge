import logging
from Light import Light

logger = logging.getLogger('daemon')


class Scene(Light):

    def __init__(self, daemon, hue_values, hue_id):
        """ initialize """
        Light.__init__(self, daemon, hue_values, hue_id)
        self.group_id = None
        self._state = None
        self.lightStates = self.get_light_states()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if 'on' == state:
            result = self.daemon.hue.bridge.activate_scene(self.group_id, self.id)[0]
            logger.debug('SCENE: {}'.format(result.keys()[0]))
        self._state = state

    def get_light_states(self):
        username = self.daemon.hue.bridge.username
        hue_settings = self.daemon.hue.bridge.request(
            'GET', '/api/' + username + '/scenes/' + self.id
        )
        return hue_settings['lightstates']
