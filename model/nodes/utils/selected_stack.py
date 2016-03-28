"""
This is list like object to hold node selection
"""
from collections import UserList

class NodeStack(UserList):
    """
    Stricktly constrained list like container to hold node selections
    """

    def __add__(self, other):
        raise AttributeError('Cant add value, use append')

    def __iadd__(self, other):
        raise AttributeError('Cant iadd value, use append')

    def insert(self, i, item):
        raise AttributeError('Cant insert value, use append')

    def sort(self, *args, **kwds):
        raise AttributeError('Cant sort container')

    def append(self, item):
        if item in self.data:
            self.data.remove(item)
        super().append(item)

    def __setitem__(self, key, value):
        raise AttributeError('Cant set value, use append')

    def __repr__(self):
        return 'NodeStack object : {}'.format(self.data)


if __name__ == '__main__':
    fff = NodeStack([5, 6, 7])
    print(fff.index(6))