import asyncio
import time
from random import randint
from itertools import chain

ALL_ITEMS = []

class BaseNode:
    """
    Base class for nodes subclasses

    """
    def __init__(self, name, inputs, outputs, action=None):
        self.name = name
        self.inputs = inputs
        self.ouputs = outputs
        self._action = action

    def run(self):
        """
        run's generator
        """
        # match input pattern
        # if ok call action
        self._action(self.name, self.inputs, self.ouputs)

    def __repr__(self):
        return 'node {}'.format(self.name)

    def _action(self):
        return NotImplementedError('not in base class')

    def stop(self):
        pass

    def connectInputNode(self, node, rec_lev=0):
        self.inputs.append(node)
        if rec_lev < 1:
            rec_lev += 1
            node.connectOutputNode(self, rec_lev)

    def disconnectInputNode(self, node, rec_lev=0):
        self.inputs.remove(node)
        if rec_lev < 1:
            rec_lev += 1
            node.disconnectOutputNode(self, rec_lev)

    def connectOutputNode(self, node, rec_lev=0):
        self.ouputs.append(node)
        if rec_lev < 1:
            rec_lev += 1
            node.connectInputNode(self, rec_lev)

    def disconnectOutputNode(self, node, rec_lev=0):
        self.ouputs.remove(node)
        if rec_lev < 1:
            rec_lev += 1
            node.disconnectInputNode(self, rec_lev)


class Node(BaseNode):
    def __init__(self, name, inputs, outputs):
        super(Node, self).__init__(name, inputs, outputs)
        self._action = self.printer

    def get_action(self):
        return self.some_synchfunc

    def some_synchfunc(self):
        dt = randint(2, 4)

        def strange_func():
            print("{} what a good day - ({}) ".format(env_time(), self.name))
            return True

        return strange_func, dt

    @asyncio.coroutine
    def printer(self, par=None, chld=None):
        print('{} hello im {} with parents {} and children {}'.format(env_time(), self.name, self.inputs, self.ouputs))
        yield from self.back()
        print('{} im ({}) done'.format(env_time(), self.name))

    @asyncio.coroutine
    def back(self):
        sleeptime = randint(3, 8)
        yield from asyncio.sleep(sleeptime)
        print('{} ill ({}) be back after {} sceonds'.format(env_time(), self.name, sleeptime))


class Item:
    class_counter = 0

    def __init__(self, name):
        self.name = name
        self.itemid = Item.class_counter
        Item.class_counter += 1

    def __repr__(self):
        return 'Item {} id {}'.format(self.name, self.itemid)


class Recipe:
    def __init__(self, name):
        self.name = name
        self.state = 'not ready'
        self.dict = {}

    def fill_recipe(self, args):
        for i, q in args:
            self.dict[i] = (q, 0)
        self.state = 'filled'

    def set_filled(self, item):
        self.dict[item] = (self.dict[item][0], 1)
        # check_all_elements()

    def check_all_elements(self):
        pass

    def __repr__(self):
        return str(self.dict)


class NodeSteve(BaseNode):
    def __init__(self, name, inputs, outputs):
        super().__init__(name, inputs, outputs)

        # make custom recipe
        torch_dict = {'alias': 'Torch',
                      'items': ['Coal', 'sticks'],
                      'qtty': [1, 2]}

        items = [Item(i) for i in torch_dict['items']]
        qtty = torch_dict['qtty']

        torch_rec = Recipe(torch_dict['alias'])
        torch_rec.fill_recipe(zip(items, qtty))
        print(torch_rec)

        self.myqueue = asyncio.Queue(10)

    def get_action(self):
        return False

    @asyncio.coroutine
    def strange_func(self):
        while True:
            yield from asyncio.sleep(2)
            yield from self.myqueue.put('test')
            print("{} what a good day - ({}) ".format(env_time(), self.name))
            print(self.myqueue)
        yield asyncio.sleep(0)



    @asyncio.coroutine
    def printer(self, par=None, chld=None):
        print('{} hello im {} with parents {} and children {}'.format(env_time(), self.name, self.inputs, self.ouputs))


@asyncio.coroutine
def simple_coro():
    sleeptime = randint(1, 5)
    yield from asyncio.sleep(sleeptime)
    print('PTNHL-lalala after {} sleep'.format(sleeptime))


def simple_coro2():
    for _ in range(5):
        sleeptime = randint(1, 3)
        # yield from asyncio.sleep(sleeptime)
        yield from asyncio.sleep(sleeptime)
        print('PTNHL-lalala after {} sleep'.format(sleeptime))


def env_time():
    """
    Better use of asynch.time() later
    """
    env_t = time.clock()
    env_t = round(env_t)
    return env_t


class Graph():
    @asyncio.coroutine
    def make_cor_with_dt(self, func, dt):
        yield from asyncio.sleep(dt)
        func()

    def __init__(self):
        self.nodes = []

    def start(self):

        event_loop = asyncio.get_event_loop()

        # start clock
        # print('time now {}'.format(env_time()))
        env_time()

        tasks = []

        gg = asyncio.coroutine(simple_coro2)
        print(asyncio.iscoroutine(gg))
        print(asyncio.iscoroutinefunction(gg))
        gg_task = event_loop.create_task(gg())

        tasks += [gg_task]

        for nd in self.nodes:
            try:
                func_on_fly, dt = nd.get_action()()
                some_cor = self.make_cor_with_dt(func_on_fly, dt)
                tasks += [event_loop.create_task(some_cor)]

            except Exception as e:
                print('[WARNING] Got a {}'.format(e))

            # print(nd.some_synchfunc())

            tasks += [event_loop.create_task(nd.printer())]

            if isinstance(nd, NodeSteve):
                tasks += [event_loop.create_task(nd.strange_func())]
            # tasks += [event_loop.create_task(simple_coro())]

        # tasks += [event_loop.create_task(self.nodes[0].get_action())]

        print('tasks : {}'.format(tasks))

        event_loop.run_until_complete(asyncio.wait(tasks))
        event_loop.close()
        print('{} EVENT LOOP Done !!!'.format(env_time()))


if __name__ == '__main__':
    # define set of node types
    Steve = NodeSteve('Steve', inputs=[], outputs=[])
    Workbench = Node('Workbench', inputs=[], outputs=[])
    Woodcutter = Node('Woodcutter', inputs=[], outputs=[])
    CoalProducer = Node('CoalProducer', inputs=[], outputs=[])
    Warehouse = Node('Warehouse', inputs=[], outputs=[])

    Steve.connectOutputNode(Workbench)
    Workbench.connectInputNode(Woodcutter)
    Workbench.connectInputNode(CoalProducer)
    Workbench.connectOutputNode(Warehouse)
    node_graph = Graph()
    node_graph.nodes += [Steve, Workbench, Woodcutter, CoalProducer, Warehouse]

    node_graph.start()

