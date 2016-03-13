import simpy
from random import randint
from collections import deque


# testing custom type
class dynint(int):
    def __new__(cls, val):
        return int.__new__(cls, val + randint(-3, 3))


class Descriptor:
    """
        Base descriptor, which handle types
    """
    def __init__(self, name, **opts):
        self._name = name
        for key, value in opts.items():
            setattr(self, key, value)

    def __set__(self, instance, value):
        instance.__dict__[self._name] = value

class Typed(Descriptor):
    """
        Checking type
    """
    _expected_type = type(None)
    _simulatable = False

    def __set__(self, instance, value):
        if not isinstance(value, self._expected_type):
            print('value : {}'.format(value))
            raise TypeError('Expected ' + str(self._expected_type))
        super().__set__(instance, value)


class Dynamic(Typed):
    _expected_type = dynint


class Integer(Typed):
    _expected_type = int


class Float(Typed):
    _expected_type = float


class String(Typed):
    _expected_type = str


class List(Typed):
    _expected_type = list

# TODO delete this
class Store(Typed):
    _expected_type = simpy.Store


class IntList(List):
    def __set__(self, instance, values):
        for val in values:
            if not isinstance(val, int):
                raise TypeError('Expected int list')
        super().__set__(instance, values)


class StrList(List):
    def __set__(self, instance, values):
        for val in values:
            if not isinstance(val, str):
                raise TypeError('Expected str list')
        super().__set__(instance, values)


# -------------------------------------
# TODO: metatypes.mtResource()
class mtQueue():
    _simulatable = True

    def __init__(self,parent, *args):
        """
            deque how-to:
            https://docs.python.org/2/library/collections.html#collections.deque
            FIFO - append(), pop()
            LIFO - appendleft(), popleft()
        """
        self.parent = parent
        self.proxylist = deque()
        for el in args:
            self.proxylist.append(el)

    def add(self, val):
        self.proxylist.append(val)

    def give_sim_analog(self, simpy_env):
        """ Create Simpy.Store obj for self.proxylist"""
        somestore = simpy.Store(simpy_env)
        for el in self.proxylist:
            somestore.put(el)
        somestore.parent = self.parent
        return somestore


class mtFilteredQueue():
    _simulatable = True

    def __init__(self, parent=None, *args):
        self.proxylist = deque()
        self.parent = parent
        for el in args:
            self.proxylist(el)

    def add(self, val):
        self.proxylist.append(val)

    def give_sim_analog(self, simpy_env):
        """ Create Simpy.FilteredStore obj for self.proxylist"""
        somestore = simpy.FilterStore(simpy_env)
        somestore.parent = self.parent
        for el in self.proxylist:
            somestore.put(el)
        return somestore


class mtPile():
    _simulatable = True

    def __init__(self, level=0, simstate=0, simpy_env=None):
        #todo: if simstate - then give_sim_analog(simpy_env)
        # may be there is another way....
        self.proxyLevel = level

    def add(self, val):
        if val > 0:
            self.proxyLevel += val
        else:
            raise ValueError('Value must be positive')

    def give_sim_analog(self, simpy_env):
        """ Create Simpy.Store obj for self.proxylist"""
        somePile = simpy.Container(simpy_env)
        if self.proxyLevel > 0:
            somePile.put(self.proxyLevel)
        return somePile


class mtPileAccount():
    _simulatable = True

    def __init__(self, level=0):
        self.accounts = {}

    def add(self, dim, val):
        if not(dim in self.accounts):
            self.accounts[dim] = mtPile()
        if val > 0:
            self.accounts[dim].add(val)
        else:
            raise ValueError('Value must be positive')

    def give_sim_analog(self, simpy_env):
        """ Create Simpy.Store obj for self.proxylist"""
        # somePile = simpy.Container(simpy_env)
        # if self.proxyLevel > 0:
        #     somePile.put(self.proxyLevel)
        new_accounts = cSimPileAccount(simpy_env)
        for dim, val in self.accounts:
            new_accounts.accounts[dim] = val.give_sim_analog(simpy_env)
        return new_accounts


class cSimPileAccount():
    def __init__(self, simpy_env):
        self.simpy_env = simpy_env
        self.accounts = {}


class nQueue(Typed):
    _expected_type = simpy.Store


class nPile(Typed):
    _expected_type = simpy.Container


