import logging

logger = logging.getLogger('daemon')


class Switch(object):

    valid_states = ['on', 'off']

    def __init__(self, daemon, name, config):
        """
        initialize
        :arg daemon PilightHueBridge
        :arg name string
        :arg config dict
        """
        self.type = 'switch'
        self.daemon = daemon
        self.pilight = daemon.pilight
        self.config = config
        self.name = name
        self._state = config['state']

    @property
    def state(self):
        """ get state """
        return self._state

    @state.setter
    def state(self, state):
        """ set state """
        if state in self.valid_states and state != self.state:
            logger.debug('Switching pilight {} {} to {}'.format(self.type, self.name, state))
            self._state = state
            self.update_pilight()

    def update_pilight(self):
        """ send updates to pilight """
        self.pilight.send_message(self.get_message())

    def get_message(self):
        """ retrieve pilight message """
        return {
            "action": "control",
            "code": {
                "device": self.name,
                "state": self._state
            }
        }
