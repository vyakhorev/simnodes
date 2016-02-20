import asyncio
from random import randint, choice
import inspect


class Message:
    def __init__(self, data=None, adress=None):
        self.data = data
        self._adress = [adress]

    @property
    def adress(self):
        return self._adress

    def add_adress(self, val):
        self._adress += [val]

    def __repr__(self):
        return 'message from adresses {}'.format(self.adress)


class StateMachine:
    def __init__(self):
        self.handlers = {}
        self.startState = None
        self.endStates = []
        self.curState = self.startState

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
            self.curState = newState
            if newState.upper() in self.endStates:
                print("State reached ", newState)
                break
            else:
                handler = self.handlers[newState.upper()]

        return newState


class Recipe(StateMachine):
    def __init__(self, name):
        self.name = name
        super(Recipe, self).__init__()

        self.add_state('PENDING', self.pending, 0)
        self.add_state('CRAFTING', self.craft, 0)
        self.add_state('CANCELLED', None, end_state=1)
        self.add_state('DONE', None, end_state=1)
        self.set_start('')

        # list of node which handle me
        self.registry = []

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


class Crate(Recipe):
    class_id = 0

    def __init__(self):
        super(Crate, self).__init__('Crate')
        self.howto = '8 Wood'

        self.itemid = Crate.class_id
        Crate.class_id += 1

    def __repr__(self):
        return 'Crate #{}'.format(self.itemid)


class Nodebase:
    all_nodes = []

    def __init__(self, name, input_list, output_list):
        self.name = name

        self.input_list = input_list
        self.output_list = output_list

        self.gl_event_loop = None
        self.all_nodes += [self]

        self.actions = []
        self.act_queue = asyncio.Queue()
        self.results = []
        self.res_queue = asyncio.Queue()

    @property
    def input_list(self):
        return self._input_list

    @input_list.setter
    def input_list(self, val):
        print('{} inputs : {}'.format(self, val))
        self._input_list = val

    @property
    def output_list(self):
        return self._output_list

    @output_list.setter
    def output_list(self, val):
        print('{} outputs : {}'.format(self, val))
        self._output_list = val

    @asyncio.coroutine
    def fetch_all_incomes(self):
        while True:
            for inp in self.input_list:
                try:
                    item = inp.act_queue.get_nowait()
                    self.res_queue.put_nowait(item)
                except asyncio.queues.QueueEmpty:
                    # print('QueueEmpty')
                    pass

            yield from asyncio.sleep(0)

    @asyncio.coroutine
    def reply(self, msg):
        while True:
            for inp in self.input_list:
                if msg.adress == inp:
                    yield from inp.res_queue.put(msg)

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
    def __init__(self, name, input_list=None, output_list=None):
        super(TorchEater, self).__init__(name, input_list, output_list)
        self.alias = 'Torch'
        self.todo = asyncio.Queue()

    @asyncio.coroutine
    def actions_listen(self):
        while True:
            msg = yield from self.res_queue.get()
            print('got {}'.format(msg))
            if msg.curState == 'DONE':
                print('{} : My request {} successfully complited :D'.format(self, msg))
            elif msg.curState == 'CANCELLED':
                print('{} : My request {} got some issues... :X'.format(self, msg))
            else:
                yield from self.todo.put(msg)
                print('{} todo : {}'.format(self, self.todo))

            yield from asyncio.sleep(1)

    @asyncio.coroutine
    def actions_filler(self):
        rand = randint(4, 8)
        for n in range(rand):
            self.recipe = Torch()
            self.recipe.set_start('PENDING')
            my_message = Message(self.recipe, self)

            yield from self.act_queue.put(my_message)
            yield from asyncio.sleep(1)
            # print('lalal')
        print('PRODUCED {} tasks'.format(rand))

    def make_task(self):

        # tasks = [self.gl_event_loop.create_task(self.dumb_printer()),
        tasks = [self.gl_event_loop.create_task(self.actions_filler()),
                 self.gl_event_loop.create_task(self.fetch_all_incomes()),
                 self.gl_event_loop.create_task(self.actions_listen())]


class CrateEater(Nodebase):
    def __init__(self, name, input_list=None, output_list=None):
        super(CrateEater, self).__init__(name, input_list, output_list)
        self.alias = 'Torch'

    @asyncio.coroutine
    def actions_filler(self):
        rand = randint(4, 8)
        for n in range(rand):
            self.recipe = Crate()
            self.recipe.set_start('PENDING')

            yield from self.act_queue.put(self.recipe)
            yield from asyncio.sleep(1)
            # print('lalal')
        print('PRODUCED {} tasks'.format(rand))

    def make_task(self):

        # tasks = [self.gl_event_loop.create_task(self.dumb_printer()),
        tasks = [self.gl_event_loop.create_task(self.actions_filler())]


class CraftMan(Nodebase):
    def __init__(self, name, input_list=None, output_list=None):
        super(CraftMan, self).__init__(name, input_list, output_list)
        self.todo = asyncio.Queue()
        self.succeed_items = []
        self.replies = []

        self.neighbors_dict = {}

    @asyncio.coroutine
    def actions_listen(self):
        while True:
            msg = yield from self.res_queue.get()
            print('got {}'.format(msg))
            yield from self.todo.put(msg)
            print('{} todo : {}'.format(self, self.todo))
            yield from asyncio.sleep(3)

    # @asyncio.coroutine
    # def reply(self):
    #     while True:
    #         if self.replies:
    #             yield from self.act_queue.put(self.replies.pop(0))
    #         yield from asyncio.sleep(0)

    @asyncio.coroutine
    def craft_it(self):
        crafted_count, count = 0, 0

        while True:
            # crafted  = choice([True, False])
            msg = yield from self.todo.get()

            item = msg.data

            success = item.run('spam')
            count += 1
            if success == 'DONE':
                crafted_count += 1
                self.succeed_items += [item]

            msg.add_adress(self)
            self.replies += [msg]
            print(30*'**')
            print('Managed to craft {} of {} items'.format(crafted_count, count))
            print('List of crafted items : {}'.format(self.succeed_items))
            print(30*'**')
            yield from asyncio.sleep(5)

    def make_task(self):
        # tasks = [self.gl_event_loop.create_task(self.dumb_printer()),
        tasks = [self.gl_event_loop.create_task(self.fetch_all_incomes()),
                 self.gl_event_loop.create_task(self.craft_it()),
                 self.gl_event_loop.create_task(self.actions_listen())]
                 # self.gl_event_loop.create_task(self.reply())]

def boomfunc():
    f = Message('spam', 'hotkovo')
    print(f.adress)
    f.add_adress('mytishi')
    print(f.adress)


if __name__ == '__main__':
    torch1 = TorchEater('torch1')
    # crate1 = CrateEater('shovel1')
    # shovel1.alias = 'shovel'
    craftman1 = CraftMan('craftman1', input_list=[torch1])
    torch1.input_list = [craftman1]
    # crate1.input_list = [craftman1]

    main_loop = asyncio.get_event_loop()

    nodes = Nodebase.all_nodes
    a_graph = Graph(nodes)
    a_graph.propagate_loop(main_loop)
    a_graph.run()

    main_loop.run_forever()

    # boomfunc()

