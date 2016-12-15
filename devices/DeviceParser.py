from Scene import Scene
from Group import Group
from Light import Light
import logging

logger = logging.getLogger('daemon')


class DeviceParser(object):
    perfomanceLogging = False

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
        for light in self.daemon.hue.lights:
            self.log_performance('GET ====== init light')
            hue_values = self.daemon.hue.bridge.get_light(light.light_id)
            if self.can_add_light(hue_values['name']):
                self.init_light(self.container.pilightDevices['lights'][hue_values['name']], light, hue_values)
            self.log_performance('GET ====== init light end')
        self.log_performance('GET ======== init lights end')

        self.log_performance('GET ======== parse scenes')
        for hueScene in self.daemon.hue.scenes:

            self.log_performance('GET ====== init scene - iterate devices container scene')
            for groupName in self.container.groups:
                self.log_performance('GET ==== init scene - iterate devices container groups')
                if self.can_add_scene_to_group(groupName, hueScene):
                    self.init_scene(
                        groupName,
                        self.container.pilightDevices['groups'][groupName]['scenes'][hueScene.name],
                        hueScene
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
                    self.container.pilightDevices['lights'][name] = pilight_device

    def init_groups(self):
        """ initialize groups """
        for group in self.daemon.hue.groups:
            hue_values = self.daemon.hue.bridge.get_group(group.group_id)
            self.container.groups[group.name] = Group(self.daemon, group, hue_values)

    def init_light(self, pilight, light, hue_values):
        """ initialize light """
        light = Light(self.daemon, pilight, light, hue_values)
        self.container.groups[pilight['group']].add_light(
            pilight['name'], light
        )

    def init_scene(self, group, pilight_scene, hue_scene):
        """ initialize scene """
        self.container.groups[group].add_scene(
            pilight_scene['name'],
            Scene(self.daemon, pilight_scene, hue_scene)
        )

    def get_pilight_device(self, device):
        """ retrieve piligt device """
        pilight_config = device.split('_')
        light_type = pilight_config[1]
        group = pilight_config[2]
        name = pilight_config[3]
        if group not in self.container.pilightDevices['groups']:
            self.add_pilight_group(group)

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
            "pilightName": device,
            "group": group,
            "state": state,
            "dimlevel": dimlevel
        }

    @staticmethod
    def parse_device_name(device):
        """ parse device name """
        max_len = 8
        config = device.split('_')
        config += [None] * (max_len - len(config))
        hue, config_type, group, name, action, from_bri, to_bri, tr = config
        return {
            "type": config_type,
            "group": group,
            "name": name,
            "action": action,
            "fromBri": from_bri,
            "toBri": to_bri,
            "transitiontime": tr
        }

    def add_pilight_group(self, group):
        """ add pilight group """
        self.container.pilightDevices['groups'][group] = {
            "scenes": {}
        }

    def can_add_light(self, hue_light):
        """ can add light? """
        return hue_light in self.container.pilightDevices['lights']

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
        if self.perfomanceLogging is True:
            logger.debug(message)
