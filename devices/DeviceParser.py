from Scene import Scene
from Group import Group
from Light import Light
from Transition import Transition
from devices.pilight.Switch import Switch as PilightSwitch
from devices.hue.Light import Light as HueLight
import logging

logger = logging.getLogger('daemon')


class DeviceParser(object):
    performanceLogging = False

    def __init__(self, container):
        """ initialize """
        self.daemon = container.daemon
        self.container = container

    def execute(self):
        """ parse configurations """
        self.log_performance('GET ========== Start parsing devices ================')
        self.log_performance('GET ======== init pilights')
        self.init_pilight_devices()
        self.log_performance('GET ======== init pilights end')
        self.log_performance('GET ======== init groups')
        self.init_groups()
        self.log_performance('GET ======== init groups end')

        self.log_performance('GET ======== init lights')
        lights = {}
        for light in self.daemon.hue.lights:
            self.log_performance('GET ====== init light')
            hue_values = self.daemon.hue.bridge.get_light(light.light_id)
            lights[light.light_id] = hue_values
            if self.can_add_light(hue_values['name']):
                self.init_light(self.container.pilightDevices['lights'][hue_values['name']], light, hue_values)

        for hue_id in lights:
            name = lights[hue_id]['name']
            if self.can_add_transition(name):
                for pilight_config in self.container.pilightDevices['transitions'][name].values():
                    if name in self.container.lights:
                        hue = self.container.lights[name].hue
                    else:
                        hue = HueLight(self.daemon, lights[hue_id], hue_id)
                    transition = self.parse_device_name(pilight_config['pilight_name'])
                    self.init_transition(transition, pilight_config, hue)

        self.log_performance('GET ======== init lights end')

        self.log_performance('GET ======== parse scenes')
        for hue_scene in self.daemon.hue.scenes:

            self.log_performance('GET ====== init scene - iterate devices container scene')
            for groupName in self.container.groups:
                self.log_performance('GET ==== init scene - iterate devices container groups')
                if self.can_add_scene_to_group(groupName, hue_scene):
                    self.init_scene(
                        groupName,
                        self.container.pilightDevices['groups'][groupName]['scenes'][hue_scene.name],
                        hue_scene.scene_id
                    )
                    break
                self.log_performance('GET ==== init scene - iterate devices container groups end')
            self.log_performance('GET ====== init scene - iterate devices container scene end')
        self.log_performance('GET ======== parse scenes end')

        self.log_performance('GET ========== Stop parsing devices ================')

    def init_pilight_devices(self):
        """ initialize pilight devices """
        for device in self.daemon.pilight.devices:
            if device[:4] == 'hue_':
                pilight_device = self.get_pilight_device(device)
                group = pilight_device['group']
                name = pilight_device['name']
                if 'scene' == pilight_device['type']:
                    self.container.pilightDevices['groups'][group]['scenes'][name] = pilight_device
                if 'light' == pilight_device['type']:
                    if 'dim' == pilight_device['action']:
                        self.container.pilightDevices['lights'][name] = pilight_device
                    elif 'transition' == pilight_device['action']:
                        pilight_name = pilight_device['pilight_name']
                        self.container.pilightDevices['transitions'][name][pilight_name] = pilight_device

    def init_groups(self):
        """ initialize groups """
        for group in self.daemon.hue.groups:
            hue_values = self.daemon.hue.bridge.get_group(group.group_id)
            self.container.groups[group.name] = Group(self.daemon, hue_values, group.group_id)

    def init_light(self, pilight, light, hue_values):
        """ initialize light """
        light = Light(self.daemon, pilight, hue_values, light.light_id)
        self.container.lights[light.name] = light
        self.container.groups[pilight['group']].add_light(
            pilight['name'], light
        )

    def init_transition(self, transition_config, pilight_config, hue):
        self.container.transitions[pilight_config['pilight_name']] = Transition(
            transition_config,
            PilightSwitch(self.daemon, pilight_config['pilight_name'], pilight_config),
            hue
        )

    def init_scene(self, group, pilight_scene, hue_id):
        """ initialize scene """
        hue_values = {
            "name": pilight_scene['name'],
            "state": {
                "on": True if pilight_scene['state'] == 'on' else False
            }
        }
        self.container.groups[group].add_scene(
            pilight_scene['name'],
            Scene(self.daemon, hue_values, hue_id, group)
        )

    def get_pilight_device(self, device):
        """ retrieve piligt device """
        pilight_config = device.split('_')
        light_type = pilight_config[1]
        group = pilight_config[2]
        name = pilight_config[3]
        action = pilight_config[4]
        if group not in self.container.pilightDevices['groups']:
            self.add_pilight_group(group)

        if 'transition' == action and name not in self.container.pilightDevices['transitions']:
            self.container.pilightDevices['transitions'][name] = {}

        pilight_config = self.daemon.pilight.devices[device]
        state = None
        dimlevel = None
        if 'state' in pilight_config:
            state = pilight_config['state']
        if 'dimlevel' in pilight_config:
            dimlevel = pilight_config['dimlevel']
        return {
            "type": light_type,
            "name": name,
            "pilight_name": device,
            "group": group,
            "state": state,
            "dimlevel": dimlevel,
            "action": action
        }

    @staticmethod
    def parse_device_name(device):
        """ parse device name """
        max_len = 8
        config = device.split('_')
        config += [None] * (max_len - len(config))
        hue, config_type, group, name, action, fr, to, tr = config
        return {
            "type": config_type,
            "group": group,
            "name": name,
            "action": action,
            "fr": fr,
            "to": to,
            "transitiontime": tr,
            "pilight_device": device
        }

    def add_pilight_group(self, group):
        """ add pilight group """
        self.container.pilightDevices['groups'][group] = {
            "scenes": {}
        }

    def can_add_light(self, hue_light):
        """ can add light? """
        return hue_light in self.container.pilightDevices['lights']

    def can_add_transition(self, light_name):
        """ can add transition? """
        return light_name in self.container.pilightDevices['transitions']

    def can_add_light_to_group(self, hue_light):
        """ can add light to group? """
        if hue_light in self.container.pilightDevices['lights']:
            return '_bri_' in self.container.pilightDevices['lights']['hue_light']

    def can_add_scene_to_group(self, group_name, hue_scene):
        """ can add scene to group? """
        self.log_performance('GET === test if device is handled by pilight')
        if self.container.groups[group_name].has_lights(hue_scene.lights):
            return self.has_pilight_scene(group_name, hue_scene.name)
        return False

    def has_pilight_scene(self, group_name, scene_name):
        """ has pilight scene? """
        return scene_name in self.container.pilightDevices['groups'][group_name]['scenes']

    def log_performance(self, message):
        if self.performanceLogging is True:
            logger.debug(message)
