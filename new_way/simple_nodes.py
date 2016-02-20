import asyncio
from random import randint, choice


class StateMachine:
    def __init__(self):
        self.handlers = {}
        self.startState = None
        self.endStates = []

    def add_state(self, name, handler, end_state=0):
        name = name.upper()
        self.handlers[name] = handler
        if end_state:
            self.endStates.append(name)

    def set_start(self, name):
        self.startState = name.upper()

    def run(self, cargo):
        try:
            handler = self.handlers[self.startState]
        except:
            raise RuntimeError("must call .set_start() before .run()")
        if not self.endStates:
            raise RuntimeError("at least one state must be an end_state")

        while True:
            (newState, cargo) = handler(cargo)
            if newState.upper() in self.endStates:
                print("State reached ", newState)
                break
            else:
                handler = self.handlers[newState.upper()]


class Recipe(StateMachine):
    def __init__(self, name):
        self.name = name
        super(Recipe, self).__init__()

        self.add_state('PENDING', self.pending, 0)
        self.add_state('CRAFTING', self.craft, 0)
        self.add_state('CANCELLED', None, end_state=1)

        self.add_state('DONE', None, end_state=1)

        self.set_start('')

        self.accepted = True

    def pending(self, cargo):
        if self.accepted:
            newState = 'CRAFTING'
        else:
            newState = 'CANCELLED'
        return newState, cargo

    def craft(self, cargo):
        self.crafted = choice([True, False])
        print(self.crafted)
        print('{} is {} to craft'.format(self, self.crafted))
        if self.crafted:
            newState = 'DONE'
        else:
            newState = 'CANCELLED'
        return newState, cargo

    def step(self, cargo):
        try:
            handler = self.handlers[self.startState]
        except:
            raise RuntimeError("must call .set_start() before .run()")
        if not self.endStates:
            raise RuntimeError("at least one state must be an end_state")

        (newState, cargo) = handler(cargo)
        print('newState = {}'.format(newState))

        if newState.upper() in self.endStates:
            print("reached ", newState)
        else:
            handler = self.handlers[newState.upper()]

class Torch(Recipe):
    class_id = 0

    def __init__(self):
        super(Torch, self).__init__('Torch')
        self.howto = 'stick and coal'

        self.itemid = Torch.class_id
        Torch.class_id += 1

    def __repr__(self):
        return 'Torch #{}'.format(self.itemid)

class Nodebase:
    all_nodes = []

    def __init__(self, name, inputs, outputs):
        self.name = name
        self.inputs = inputs
        self.ouputs = outputs
        self.gl_event_loop = None
        self.all_nodes += [self]

        self.actions = []
        self.act_queue = asyncio.Queue()
        self.results = []
        self.res_queue = asyncio.Queue()

    @asyncio.coroutine
    def dumb_printer(self):
        while True:
            yield from asyncio.sleep(1)
            print('{} - im {}'.format(round(self.gl_event_loop.time()), self))
            print(self.act_queue)

    def make_task(self):
        return NotImplementedError('implement in children')

    def __repr__(self):
        return ' node {}'.format(self.name)

    def set_event_loop(self, event_loop):
        self.gl_event_loop = event_loop


class Graph:
    def __init__(self, nodes):
        self.nodes = nodes

    def propagate_loop(self, loop):
        for nd in self.nodes:
            nd.set_event_loop(loop)

    def run(self):
        for nd in self.nodes:
            nd.make_task()


class TorchEater(Nodebase):
    def __init__(self, name, inputs=None, outputs=None):
        super(TorchEater, self).__init__(name, inputs, outputs)
        self.alias = 'Torch'


    @asyncio.coroutine
    def actions_filler(self):
        rand = randint(4, 8)
        for n in range(rand):
            self.recipe = Torch()
            self.recipe.set_start('PENDING')

            yield from self.act_queue.put(self.recipe)
            yield from asyncio.sleep(1)
            # print('lalal')
        print('produced {} tasks'.format(rand))

    def make_task(self):

        # tasks = [self.gl_event_loop.create_task(self.dumb_printer()),
        tasks = [self.gl_event_loop.create_task(self.actions_filler())]


class CraftMan(Nodebase):
    def __init__(self, name, inputs=None, outputs=None):
        super(CraftMan, self).__init__(name, inputs, outputs)
        self.todo = asyncio.Queue()

    @asyncio.coroutine
    def fetch_all_incomes(self):
        while True:
            for inp in self.inputs:
                try:
                    item = inp.act_queue.get_nowait()
                    self.res_queue.put_nowait(item)
                except asyncio.queues.QueueEmpty:
                    # print('QueueEmpty')
                    pass

            yield from asyncio.sleep(1)

    @asyncio.coroutine
    def actions_listen(self):
        while True:
            msg = yield from self.res_queue.get()
            print('got {}'.format(msg))
            yield from self.todo.put(msg)
            print('{} todo : {}'.format(self, self.todo))
            yield from asyncio.sleep(3)

    @asyncio.coroutine
    def craft_it(self):
        while True:
            # crafted  = choice([True, False])
            item = yield from self.todo.get()

            item.run('spam')

            yield from asyncio.sleep(5)

    def make_task(self):
        # tasks = [self.gl_event_loop.create_task(self.dumb_printer()),
        tasks = [self.gl_event_loop.create_task(self.fetch_all_incomes()),
                 self.gl_event_loop.create_task(self.craft_it()),
                 self.gl_event_loop.create_task(self.actions_listen())]


if __name__ == '__main__':
    torch1 = TorchEater('torch1')
    # shovel1 = TorchEater('shovel1')
    # shovel1.alias = 'shovel'
    craftman1 = CraftMan('craftman1', inputs=[torch1])
    main_loop = asyncio.get_event_loop()

    nodes = Nodebase.all_nodes
    a_graph = Graph(nodes)
    a_graph.propagate_loop(main_loop)
    a_graph.run()

    main_loop.run_forever()
