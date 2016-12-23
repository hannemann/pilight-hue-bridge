import logging
from Switch import Switch

logger = logging.getLogger('daemon')


class Dimmer(Switch):

    def __init__(self, daemon, name, config):
        """
        initialize
        :arg daemon PilightHueBridge
        :arg name string
        :arg config dict
        """
        Switch.__init__(self, daemon, name, config)
        self._dimlevel = config['dimlevel']
        self.type = 'dimmer'
        self.mode = 'dim'

    @property
    def state(self):
        """ get state """
        return Switch.state.fget(self)

    @state.setter
    def state(self, state):
        """ set state """
        self.mode = 'switch'
        Switch.state.fset(self, state)
        self.mode = 'dim'

    @property
    def dimlevel(self):
        """ get dimlevel """
        return self._dimlevel

    @dimlevel.setter
    def dimlevel(self, dimlevel):
        """ set dimlevel """
        if isinstance(dimlevel, int) and self._dimlevel != dimlevel:
            logger.debug('Dimmimg pilight {} {} to dimlevel {}'.format(self.type, self.name, dimlevel))
            self._dimlevel = dimlevel
            self.update_pilight()
            self.state = 'on' if self.dimlevel > 0 else 'off'

    def reset_dimlevel(self):
        """ to force update """
        self._dimlevel = None

    def update_dimlevel(self, dimlevel):
        if isinstance(dimlevel, int) and self._dimlevel != dimlevel:
            self._dimlevel = dimlevel

    def update_state(self, state):
        if state in self.valid_states and state != self.state:
            self._state = state

    def get_message(self):
        """ retrieve pilight message """
        message = Switch.get_message(self)
        if 'dim' == self.mode:
            message['code']['values'] = {
                "dimlevel": self.dimlevel
            }
            message['code'].pop('state')
        return message

    def get_switch_message(self):
        """ retrieve pilight message """
        message = Switch.get_message(self)
        return message
