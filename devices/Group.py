
class Group(object):

    def __init__(self, daemon, group):
        self.daemon = daemon
        self.name = group.name
        self.lights = group.lights
        self.hueGroup = group
        self.scenes = {}
        self.lightIds = frozenset(light.light_id for light in self.lights)
        
    def hasLights(self, lights):
        return len(self.lights) == len(self.lightIds.intersection(lights))
    
    def addScene(self, name, scene):
        self.scenes[name] = scene;
        
    def hasScene(self, name):
        return name in self.scenes
    
    def getScene(self, name):
        if self.hasScene(name):
            return self.scenes[name]
        
        return None