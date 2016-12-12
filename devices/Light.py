import time

class Light(object):
    
    def __init__(self, daemon, pilight, hue):
        
        self.daemon = daemon
        self.hue = daemon.hue
        self.pilightDevice = pilight
        self.hueDevice = hue
        self._state = 'on' if hue.on else 'off'
        
    @property
    def state(self):
        return self._state
    
    @state.setter
    def state(self, value):
        if value in ['on', 'off'] and value != self.state:
            self._state = value
            self.hueDevice.on = self.state == 'on'
        
    def setTransition(self, config):

        self._state = 'on'
        fromBri = int(config['fromBri'])
        toBri = int(config['toBri'])
        tt = int(config['transitiontime'])
        message = {
            "on": True,
            "bri": fromBri
        }
        self.daemon.debug(message)
        self.hue.bridge.set_light(self.hueDevice.light_id, message)
        
        time.sleep(.5)
        
        message = {
            "bri": toBri,
            "transitiontime": tt,
            "on": toBri > 0
        }
        self.daemon.debug(message)
        self.hue.bridge.set_light(self.hueDevice.light_id, message)
        
        
        
        
        
        