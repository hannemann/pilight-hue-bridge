from threading import Timer
import logging

logger = logging.getLogger('daemon')


class Transition(object):
    def __init__(self, config, pilight, hue):
        self.pilight = pilight
        self.hue = hue
        self.fr = int(config['fr'])
        self.to = int(config['to'])
        self.tt = int(config['transitiontime'])
        self.group = self.get_group(config['group'])
        self.end_timer = None

    def start(self):
        self.pilight.state = 'on'
        self.deactivate_scene()
        self.hue.set_transition(self.fr, self.to, self.tt)
        self.end_timer = Timer(self.tt / 10 + 10, self.end)
        self.end_timer.start()

    def end(self):
        self.end_timer = None
        self.hue.end_transition()
        self.pilight.state = 'off'

    def cancel(self):
        if self.end_timer is not None:
            self.pilight.state = 'off'
            self.end_timer.cancel()
            self.end_timer = None
            self.hue.cancel_transition()

    def get_group(self, name):
        if name in self.pilight.daemon.devices.groups:
            return self.pilight.daemon.devices.groups[name]
        return None

    def deactivate_scene(self):
        if self.group is not None:
            if self.group.has_active_scene() and str(self.hue.id) in self.group.activeScene.hue.lightStates:
                self.group.deactivate_active_scene()
