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
            self.mode = 'switch'
            self.state = 'on' if self.dimlevel > 0 else 'off'
            self.mode = 'dim'

    def reset_dimlevel(self):
        """ to force update """
        self._dimlevel = None

    def get_message(self):
        """ retrieve pilight message """
        message = Switch.get_message(self)
        if 'dim' == self.mode:
            message['code']['values'] = {
                "dimlevel": self.dimlevel
            }
            message['code'].pop('state')
        return message
