__author__ = 'User'

class EconRes:
    def __init__(self, name):
        self.name = name
        self.state = 'Closed'

    def setState(self, state='Open'):
        self.state = state

class resMan(EconRes):
    pass

