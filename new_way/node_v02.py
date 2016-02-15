import asyncio
import time
from random import randint
import functools
from itertools import chain
import logging
logging.basicConfig(level=logging.INFO)

ALL_ITEMS = []


class BaseNode:
    """
    Base class for nodes subclasses

    """
    all_nodes = []

    def __init__(self, name, inputs, outputs):
        self.name = name
        self.inputs = inputs
        self.ouputs = outputs
        # self._action = action
        self.gl_event_loop = None
        self.channels = []
        # This is result of node processing
        self.result = None
        # register new node
        self.all_nodes += [self]

    def add_channel(self, chan):
        self.channels += [chan]

    def set_event_loop(self, event_loop):
        self.gl_event_loop = event_loop

    def listen_input(self, inp):
        res = inp.result
        return res

    @asyncio.coroutine
    def spam_spam_spam(self):
        # Instead of spam we need asking to scheduler
        while True:
            yield from asyncio.sleep(1)
            print('{} - {} : {}'.format(env_time(), self, randint(2, 4)*' spam'))

    def run(self):
        """
        run's generator
        """
        # todo ASAP : implement properly channels infrastructure
        vals = []
        self.gl_event_loop.create_task(self.spam_spam_spam())

        if self.inputs:
            for inp in self.inputs:
                val = self.listen_input(inp)
                vals += [val]
                # vals += [self._action(val)]

        if not self.inputs:
            self.result = self._action(None)

        else:
            print('{} my channels : {}'.format(self, vals))
            # self.result = sum(vals)
            self.result = self._action(vals)



        # match input pattern
        # if ok call action
        # res = self._action(self.name, self.inputs, self.ouputs)
        # self.result = res

    def __repr__(self):
        return 'node {}'.format(self.name)

    def _action(self, args):
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


class FuncNode(BaseNode):
    """
    This node just run _action inside
    """
    def __init__(self, name, inputs, outputs):
        super().__init__(name, inputs, outputs)
        # self._action = None

    def _action(self, args):
        print('im poor *Func* {}'.format(self.name))
        return True


class HubNode(BaseNode):
    """
    This node working as stateful with req/rep to outter world
    complex one...
    """
    pass


class SourceNode(BaseNode):
    """
    This node hast got any inputs
    """
    def __init__(self, name, outputs):
        super().__init__(name, None, outputs)

    def _action(self, args):
        print('im poor *Source* {}'.format(self.name))
        return True


class SinkNode(BaseNode):
    """
    This node grabbing results, thus its doesnt have outputs
    """
    pass


# ########################################
# ####### END OF NODE TYPES ##############
# ########################################
class BaseResource:
    """
    Its base class for all resources
    """
    def __init__(self, name):
        self.name = name
        # If shared : dont block resource
        self.shared = True


class Schedule(BaseResource):
    """
    Basic scheduler : dict with {task : time} elements
    """
    def __init__(self, name):
        super().__init__(name)
        self.task_sched = {}

    def add_task(self, when, task):
        self.task_sched[task] = when


class Store(BaseResource):
    def __init__(self, name):
        super().__init__(name)
        self.store_queue = asyncio.Queue()

    def add_items(self, items):
        self.store_queue.put(items)


class Item:
    class_counter = 0

    def __init__(self, name):
        self.name = name
        self.itemid = Item.class_counter
        Item.class_counter += 1

    def __repr__(self):
        return 'Item {} id {}'.format(self.name, self.itemid)

# ########################################
# ####### END OF RESOURCE TYPES ##########
# ########################################


# ###########################################
# ##### START CONCRETE IMPLEMENTATIONS ######
# ###########################################
class BasicSourceNode(SourceNode):
    def __init__(self, name, outputs):
        super().__init__(name, outputs)
        self.value = None

    def _action(self, args):
        super()._action(args)
        return self.value


class MultiplyNode(FuncNode):
    def __init__(self, name, inputs, outputs):
        super().__init__(name, inputs, outputs)
        self.name = 'Multiply'

    def _action(self, args):
        super()._action(args)
        res = 1
        for el in args:
            res *= el
        print('{} successfully calculated'.format(self))
        return res

class Odd_conditionNode(FuncNode):
    def __init__(self, name, inputs, outputs):
        super().__init__(name, inputs, outputs)

    def _action(self, args):
        if len(self.inputs) > 1 :
            raise ValueError('must be one input channel')

        if args[0]%2 == 0:
            return False
        else:
            return True

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

        # self.myqueue = asyncio.Queue(10)


def env_time():
    """
    Better use of asynch.time() later
    """
    env_t = time.clock()
    env_t = round(env_t)
    return env_t


@asyncio.coroutine
def print_time():
    while True:
        yield from asyncio.sleep(1)
        print(env_time())


class Graph():
    def __init__(self, nodes):
        self.nodes = nodes

    def propagate_loop(self, loop):
        for nd in self.nodes:
            nd.set_event_loop(loop)


if __name__ == '__main__':
    # define set of node types
    main_loop = asyncio.get_event_loop()
    env_time()

    # Test case setup #2
    node1 = BasicSourceNode('basic 5 emmitor', outputs=[])
    node1.value = 5
    node2 = BasicSourceNode('basic 13 emmitor', outputs=[])
    node2.value = 13
    node3 = BasicSourceNode('basic 7 emmitor', outputs=[])
    node3.value = 6
    node_multiply1 = MultiplyNode('multiply node', inputs=[node1, node2, node3], outputs=[])
    node_odd_or_not1 = Odd_conditionNode('Odd condition', inputs=[node_multiply1], outputs=[])
    node_odd_or_not2 = Odd_conditionNode('Odd condition', inputs=[node1], outputs=[])

    # Test case setup #1
    SteveEmmitorNode = SourceNode('SteveEmmittor', outputs=None)
    SteveStartNode = HubNode('SteveStartNode', inputs=[], outputs=[])
    SteveCopyNode1 = None
    SteveResource = Schedule('SteveTasks')

    FactoryEmmitorNode = SourceNode('FactoryEmmitor', outputs=None)
    FactoryStartNode = HubNode('FactoryStarter', inputs=[], outputs=[])
    FactoryCopyNode1 = None
    FactoryResource = Schedule('FactoryTasks')
    FactoryCraft1 = FuncNode('Torch_craft', inputs=[FactoryEmmitorNode], outputs=[])
    FactoryCraft2 = FuncNode('Shovel_craft', inputs=[FactoryCraft1, SteveEmmitorNode], outputs=[])

    # Configure pseudo-graph
    all_nodes = BaseNode.all_nodes
    a_Graph = Graph(all_nodes)
    a_Graph.propagate_loop(main_loop)

    # all_done = asyncio.Future()
    # all_done.add_done_callback(functools.partial(callback, 1))

    # # Test case run #1
    # SteveEmmitorNode.run()
    # FactoryEmmitorNode.run()
    # FactoryCraft1.run()
    # FactoryCraft2.run()
    # print('result : {}'.format(SteveEmmitorNode.result))
    # print('result : {}'.format(FactoryEmmitorNode.result))
    # print('result : {}'.format(FactoryCraft1.result))
    # print('result : {}'.format(FactoryCraft2.result))


    print('Test 2 ###############')
    # Test case run #2
    node1.run()
    node2.run()
    node3.run()
    node_multiply1.run()
    node_odd_or_not1.run()
    node_odd_or_not2.run()
    print('result : {}'.format(node_multiply1.result))
    print('result : {}'.format(node_odd_or_not1.result))
    print('result : {}'.format(node_odd_or_not2.result))
    main_loop.stop()



    # Some debug printer
    main_loop.create_task(print_time())

    # trigger endless loop with exit callback
    main_loop.run_forever()

