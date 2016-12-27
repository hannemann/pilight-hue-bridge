import os
import sys
if sys.version_info[0] > 2:
    PY3K = True
else:
    PY3K = False

if PY3K:
    import configparser as ConfigParser
else:
    import ConfigParser


class ConfigException(Exception):

    def __init__(self, exc_id, message):
        self.id = exc_id
        self.message = message

config = ConfigParser.ConfigParser()
path = os.path.expanduser("~/.config/pilight-hue-bridge")
user = path if os.path.exists(path) else "/tmp"
etc = "/etc/pilight-hue-bridge"
env = "PILIGHT_HUE_BRIDGE_CONF"
file_name = "config.ini"

count = 0
for loc in os.curdir, os.path.expanduser(user), etc, os.environ.get(env):
    try:
        if loc is not None:
            with open(os.path.join(loc, file_name)) as source:
                config.readfp(source)
    except IOError:
        pass
