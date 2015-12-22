from collections import OrderedDict
from itertools import count
import model.nodes.metatypes as metatypes

class OrderedMeta(type):
    """
        Produces classes with ordered attributes
    """
    def __new__(cls, clsname, bases, clsdict):
        # print('clsdict.items : {}'.format(clsdict.items()))
        d = dict(clsdict)
        # print('d before : {}'.format(d))
        order = []
        for name, value in clsdict.items():
            if isinstance(value, metatypes.Typed):
                value._name = name
                order.append(name)
        d['_order'] = order
        # print('d after : {}'.format(d))
        # if 'nodeid' in clsdict.keys():
        #     print('class {} got portid {}'.format(clsname, clsdict[nodeid]))
        superid = count(1)
        d['iden'] = superid

        return type.__new__(cls, clsname, bases, d)

    @classmethod
    def __prepare__(cls, clsname, bases):
        return OrderedDict()

class MetaStruct(metaclass=OrderedMeta):
    # TODO: as xml write to xml branch and read from an xml branch.
    # Every new instance will got its unique identifier
    _instid = count(1)

    def __init__(self):
        # self.nodeid = self._instid.__next__()

        # we can use builtin identifier :
        # self.nodeid = id(self)

        # or count each class instances separately :
        self._nodeid = self.iden.__next__()

    def __eq__(self, other):
        return self.nodeid == other.nodeid

    def __hash__(self):
        return self._nodeid

    @property
    def nodeid(self):
        output = str(self.__class__.__name__) + '_' + str(self._nodeid)
        return output

    def as_csv(self):
        return ','.join(str(getattr(self, name)) for name in self._order)

    def get_id(self):
        return self.nodeid


# if __name__ == '__main__':
#     import simpy
#     env = simpy.Environment()
#     print(dir())
#     RedOctober = nodes.classes.Factory.nFactory('RedOctober', ['cookie', 'muffins', 'candy'], [10, 8, 5])
#     print(vars(RedOctober))
#     print('prods: ', RedOctober.prods)
#
#     print(RedOctober.as_csv())
#
#     # Mag1 = Client('Perekrestok', simpy.Store(env, 15), 'per@mail.ru', dynint(8))
#     # print(vars(Mag1))
#     # print(Mag1.as_csv())