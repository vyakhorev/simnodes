# ======================== Nodes ===================
import simpy
import random
import abc

# Abstract Node base class
class Node(metaclass=abc.ABCMeta):
    """
        Abstract Node class, defining node interface
    """
    @abc.abstractproperty
    def PortList(self):
        """ str list of ports """
        pass

    @abc.abstractclassmethod
    def MakeStores(self):
        """ make Store from PortList """
        pass

    @abc.abstractclassmethod
    def printPort(self):
        """ return concrete Port store """
        pass

    @abc.abstractclassmethod
    def PuttoPort(self, **kwargs):
        """ put values into concrete Port store """
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Node:
            attrs = set(dir(C))
            if set(cls.__abstractmethods__) <= attrs:
                return True
        return NotImplemented


class Client(Node):

    def __init__(self, env, name='Noname'):
        self._PortList = []
        self.env = env
        self.name = name
        # Catching instances
        self.Port_instances = {}
        # setting neighbours
        self.neighbors = []

    def addNbors(self, lst, comeback=False):
        """ adding multiple neighbours to this node, moreover adding backward connection """
        if isinstance(lst, Node):
            self.neighbors.append(lst)
            if comeback == False:
                lst.addNbors(self, comeback=True)
        elif type(lst) == list:
            for el in lst:
                self.addNbors(el)
        else:
            print('Cant add neigbours')

    def getNbors(self):
        return self.neighbors

    def addPort(self, slist):
        """ add port to Client, while checking a bad input type """
        if type(slist) is str:
            self._PortList.append(slist)

        elif type(slist) is list:
            self._PortList += slist

        else:
            print('Port name has wrong type')
        print(self._PortList)

    def PortList(self):
        return 'port list : {0}'.format(self._PortList)

    def MakeStores(self):
        for prt in self._PortList:
            self.a_port = Port(self.env, prt)
            self.Port_instances[prt] = self.a_port

        print('Ports made : {0}'.format(self.a_port))

    def PuttoPort(self, elem):
        self.a_port.AddtoOutput(elem)

    def getInstance(self, portid):
        if portid in self.Port_instances:
            # print('Yeah, {0} got {1}'.format(self, portid))
            return self.Port_instances[portid]
        else:
            print('there isnt such instance')
            return None

    def printInstances(self):
        print('\n*********************'*3)
        print(self.Port_instances)

    def printPort(self):
        print(self._PortList)

    def GenInput(self, portid):
        """ test port listener"""
        inst = self.getInstance(portid)
        if inst is not None:
            while True:
                yield self.env.timeout(8)
                print('listening {0} nodes {1} port'.format(inst.name, portid))
                Comand = yield inst.getInput()
                # print('COMAND : {0}'.format(Comand))
                if Comand == 'Alert!':
                    yield self.env.process(inst.AddtoOutput('Im catch ALERT, all to the boats!!!'))

                # print(Bifurcator.printInstances())
                # print(Ecvilibrium.printInstances())


    def GenOutput(self, portid):
        """ test output generator """
        counter = -1
        inst = self.getInstance(portid)

        if inst == None:
            print('there isnt such key!!')

        if portid in self._PortList:

            while True:
                counter += 1
                print('put {0} Order!!'.format(counter))
                yield self.env.timeout(random.randint(1, 3))
                if portid == 'info':
                    if counter % 4 == 0:
                        yield self.env.process(inst.AddtoOutput('Alert!'))
                    else:
                        yield self.env.process(inst.AddtoOutput('{0}#{1}'.format(portid.upper(), counter)))
                else:
                    yield self.env.process(inst.AddtoOutput('{0}#{1}'.format(portid.upper(), counter)))

    def __repr__(self):
        a_str = '{0} Node \n with ports {1} \n'.format(self.name, self._PortList)
        return a_str


class Port:
    """
        Port defining input and output FIFO queues
    """
    # todo make queue generator
    def __init__(self, env, name):
        self.env = env

        self.name = name
        self.Outqueue = simpy.Store(self.env)
        self.Inqueue = simpy.Store(self.env)

    # Input
    def AddtoInput(self, elem):
        yield self.Inqueue.put(elem)

    def getInput(self):
        return self.Inqueue.get()

    # Out
    def AddtoOutput(self, elem):

        yield self.Outqueue.put(elem)
        # print(self)

    def getOutput(self):
        return self.Outqueue.get()

    def __repr__(self):
        return 'current time : {2}\n INPUT {0} \n OUTPUT {1} \n'.format(self.Inqueue.items, self.Outqueue.items,
                                                                        str(self.env.now)+' tick')


class Hub:
    """
        Class which connect neighbour nodes and solve their intersections
    """
    def __init__(self):
        pass

    def synch_stores(self, a_node, b_node):
        for a_portid, a_klass in a_node.Port_instances.items():
            for b_portid, b_klass in b_node.Port_instances.items():
                if a_portid == b_portid:
                    print('{0} and {1} have same {2} port !'.format(a_node.name, b_node.name, a_portid))
                    a_klass.Inqueue = b_klass.Outqueue
                    b_klass.Inqueue = a_klass.Outqueue


if __name__ == '__main__':

    env = simpy.Environment()

    # make Client
    Bifurcator = Client(env, name='Bifurcator')
    # setup ports
    Bifurcator.addPort(['uow', 'res', 'info'])
    # Set data to apropriate port
    # Bifurcator.setData('uow', UoW)

    print(Bifurcator.PortList())

    Bifurcator.MakeStores()

    env.process(Bifurcator.GenOutput('res'))
    env.process(Bifurcator.GenOutput('uow'))
    env.process(Bifurcator.GenOutput('info'))

    # # addding port during run
    # Bifurcator.addPort('lol')
    # Bifurcator.MakeStores()
    # env.process(Bifurcator.GenOutput('lol'))

    # Lets make another Agent
    Ecvilibrium = Client(env, name='Ecvilibrium')
    Ecvilibrium.addPort(['uow', 'res', 'spam', 'info'])
    Ecvilibrium.MakeStores()

    # Manage neighbours
    alpha = Client(env, name='alpha')
    beta = Client(env, name='beta')

    Ecvilibrium.addNbors([Bifurcator, alpha, beta])
    print('***Neighbours***')
    print(Ecvilibrium.neighbors)
    print('________________')
    print(Bifurcator.neighbors)
    print('________________')
    print(alpha.neighbors)
    print('________________')

    # Checking Hub
    # todo make access only from neighbours
    a_hub = Hub()
    a_hub.synch_stores(Bifurcator, Ecvilibrium)

    # Set fake generation
    env.process(Ecvilibrium.GenOutput('uow'))
    env.process(Ecvilibrium.GenOutput('res'))
    env.process(Ecvilibrium.GenOutput('spam'))

    # Set fake listener
    env.process(Ecvilibrium.GenInput('info'))

    env.run(until=55)

    # Print results
    Bifurcator.printInstances()
    Ecvilibrium.printInstances()
    print('****************')
    print(Bifurcator)
    print(Ecvilibrium)
