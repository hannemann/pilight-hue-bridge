from Light import Light


class Group(Light):

    def __init__(self, daemon, hue_values, hue_id):
        """ initialize """
        Light.__init__(self, daemon, hue_values, hue_id)
        self.type = 'group'