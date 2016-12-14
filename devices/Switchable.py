    
import logging

logger = logging.getLogger('daemon')

class Switchable(object):
    
    def __init__(self, daemon, hue):
        """ initialize """
        self.daemon = daemon
        self.hue = hue
        self.pilightDevice = None
        self.pilightDeviceName = ''
        
        """ example hueValues
        {u'name': u'Billiardtisch', u'swconfigid': u'60083D2F', u'swversion': u'1.15.0_r18729', u'manufacturername': u'Philips', u'state': {u'on': True, u'reachable': True, u'bri': 33, u'alert': u'select'}, u'uniqueid': u'00:17:88:01:02:6c:d9:40-0b', u'productid': u'Philips-LWB010-1-A19DLv3', u'type': u'Dimmable light', u'modelid': u'LWB010'}
        {u'name': u'Vios-Aura', u'swversion': u'4.6.0.8274', u'manufacturername': u'Philips', u'state': {u'on': True, u'hue': 17204, u'colormode': u'xy', u'effect': u'none', u'alert': u'none', u'xy': [0.4833, 0.4922], u'reachable': True, u'bri': 147, u'sat': 254}, u'uniqueid': u'00:17:88:01:00:1a:13:65-0b', u'type': u'Color light', u'modelid': u'LLC007'}, (Switchable, 16)
        {u'name': u'Sofa-Hinten', u'swversion': u'5.50.1.19085', u'manufacturername': u'Philips', u'state': {u'on': True, u'hue': 21010, u'colormode': u'xy', u'effect': u'none', u'alert': u'select', u'xy': [0.4561, 0.482], u'reachable': True, u'bri': 109, u'ct': 363, u'sat': 252}, u'uniqueid': u'00:17:88:01:00:de:fe:98-0b', u'type': u'Extended color light', u'modelid': u'LCT001'}, (Switchable, 16)
        {u'name': u'Stripes-Wohnzimmer', u'swversion': u'020E.2000004F', u'manufacturername': u'dresden elektronik', u'state': {u'on': True, u'hue': 2730, u'colormode': u'xy', u'effect': u'none', u'alert': u'select', u'xy': [0.6007, 0.3909], u'reachable': True, u'bri': 150, u'ct': 500, u'sat': 254}, u'uniqueid': u'00:21:2e:ff:ff:00:80:da-0a', u'type': u'Extended color light', u'modelid': u'FLS-PP3'}, (Switchable, 16)
        """
                
        if 'action' in self.hueValues and 'on' in self.hueValues['action']:
            on = self.hueValues['action']['on']
        elif 'state' in self.hueValues and 'on' in self.hueValues['state']:
            on = self.hueValues['state']['on']
            
        self._state = 'on' if on else 'off'
        self.hueState = self._state
        self.name = self.hueValues['name']
        
    def initPilightDevice(self, skipSync = False):
        """ initialize pilight device """
        
        self.pilightDeviceName = '_'.join([
            'hue',
            self.type,
            self.groupName,
            self.lightName,
            'bri'
        ])
        
        if self.pilightDeviceName in self.daemon.pilight.devices:
            self.pilightDevice = self.daemon.pilight.devices[self.pilightDeviceName]
            
    @property
    def state(self):
        """ get state """
        return self._state
    
    @state.setter
    def state(self, value):
        """ set state """
        if value in ['on', 'off']:
            logger.debug('Switching ' + self.type + ' ' + self.name + ' ' + value)
            
            if self._state != value:
                logger.debug('Switching hue ' + self.type + ' ' + self.name + ' ' + value)
                self._state = value
                self.hue.on = value == 'on'
            else:
                logger.debug('Hue ' + self.type + ' ' + self.name + ' is already ' + value)
    
    def sync(self):
        """ synchronize state and dimlevel """
        if self.pilightDevice is not None:
            param = self.getSyncParam()
            if self.mustSync():
                self.hue._set(param)
                
    def mustSync(self):
        """ determine if sync is applicable """
        return self.hueState != self._state
        
    def getSyncParam(self):
        """ retrieve sync param """
        return {
            "on": self.state == 'on'
        }






