import logging
import time

logger = logging.getLogger('daemon')


class Light(object):

    def __init__(self, daemon, hue_values, hue_id):
        """ initialize """
        self.daemon = daemon
        self.type = 'light'
        self.id = hue_id
        self.name = hue_values['name']
        self._state = self.get_initial_state(hue_values)
        self._dimlevel = self.get_initial_dimlevel(hue_values)
        self._transition_time = None
        self._transition_in_progress = False

    @property
    def state(self):
        """ get state """
        return self._state

    @state.setter
    def state(self, state):
        """ set state """
        if self._transition_in_progress is False:
            logger.debug('Switching hue ' + self.type + ' ' + self.name + ' ' + state)
            param = {
                "on": state == 'on'
            }
            result = self.send_to_bridge(param)[0][0]
            logger.debug(
                'SWITCH: {0} {1} {2}: {3}'.format(
                    self.type, self.name, state, result.keys()[0]
                )
            )
            if 'success' == result.keys()[0]:
                self._state = state

    @property
    def dimlevel(self):
        """ get dimlevel """
        return self._dimlevel

    @dimlevel.setter
    def dimlevel(self, dimlevel):
        """ update hue device """
        if self.dimlevel != dimlevel and self._transition_in_progress is False:
            logger.debug('DIMMER: Dimming hue {} {} to dimlevel {}'.format(self.type, self.name, dimlevel))
            param = {
                "bri": dimlevel if dimlevel > 0 else 1
            }
            state = 'on' if dimlevel > 0 else 'off'
            param['on'] = state == 'on'
            if self._transition_time is not None:
                logger.debug(
                    'TRANSITION: apply transition time {2} to {0} {1}'.format(
                        self.type, self.name, self._transition_time
                    )
                )
                param['transitiontime'] = self._transition_time
                self._transition_time = None
            result = self.send_to_bridge(param)
            success = result[0][0].keys()[0]
            logger.debug(
                '{1} {2} apply dimlevel of {0}: {3}'.format(
                    dimlevel, self.type, self.name, success
                )
            )
            if 'success' == success:
                self._dimlevel = dimlevel
        else:
            logger.debug('Hue: {} {} dimlevel {} already applied'.format(self.type, self.name, str(dimlevel)))

    def set_transition(self, fr, to, tt):
        """ set transition """
        self.dimlevel = fr
        time.sleep(.5)
        self._transition_time = tt
        self.dimlevel = to
        self._transition_in_progress = True

    def cancel_transition(self):
        self.reset_transition()
        self.state = 'on'

    def end_transition(self):
        self.reset_transition()

    def reset_transition(self):
        self._transition_time = None
        self._transition_in_progress = False

    def send_to_bridge(self, param):
        """ send param to setter according to type
        :return: dict
        """
        return getattr(self.daemon.hue.bridge, 'set_' + self.type)(self.id, param)

    @staticmethod
    def get_initial_state(hue_values):
        """ retrieve inital state """
        on = False
        if 'action' in hue_values and 'on' in hue_values['action']:
            on = hue_values['action']['on']
        elif 'state' in hue_values and 'on' in hue_values['state']:
            on = hue_values['state']['on']

        return 'on' if on else 'off'

    @staticmethod
    def get_initial_dimlevel(hue_values):
        """ retrieve initial brightness """
        dimlevel = None
        if 'action' in hue_values and 'bri' in hue_values['action']:
            dimlevel = hue_values['action']['bri']
        elif 'state' in hue_values and 'bri' in hue_values['state']:
            dimlevel = hue_values['state']['bri']

        return dimlevel
