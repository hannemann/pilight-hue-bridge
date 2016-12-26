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
        self._lock_send = False

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

    @property
    def lock_send(self):
        return self._lock_send

    @lock_send.setter
    def lock_send(self, config):
        if config is False:
            self._lock_send = False
        elif 'origin' in config and 'pilight' == config['origin']:
            self._lock_send = True

    def update_pilight(self):
        """ send updates to pilight """
        if self._lock_send is False:
            message = self.get_message()
            self.pilight.send_message(message)

    def get_message(self):
        """ retrieve pilight message """
        return {
            "action": "control",
            "code": {
                "device": self.name,
                "state": self.state
            }
        }
