from model.nodes.classes.Node_func_v2 import cNodeBase
from model.nodes.classes.SimBase import cSimNode
import model.nodes.classes.Ports_v2 as ports
from model.nodes.classes.cMessage import cMessage
from random import randint, choice

class TaskEvent():
    """
    Base class for Tasks events
    """

    def __init__(self, name='Event'):
        self.name = name
        self.trigger_count = 0

    def __repr__(self):
        return '<{} Event({})>'.format(self.name, self.trigger_count)

READY = TaskEvent('READY')
DONE = TaskEvent('DONE')
FAILED = TaskEvent('FAILED')


class StateMech():
    """
    State holding class. Its provide tasks switching mechanics and sending reply events
    :param parent | parent cls
    """
    STATES = ['ready_state', 'finish_state', 'failed_state']

    def __init__(self, parent):
        self.curstate = None
        self.parent = parent

    def change_state(self, to_state):
        """
        :param to_state | str, string alias for pseudo-state
        """
        # todo check if state dont actually changing
        if to_state in self.STATES:
            self.curstate = to_state

            if self.curstate == 'finish_state':
                self.parent.notify(DONE)
            elif self.curstate == 'failed_state':
                self.parent.notify(FAILED)

        else:
            print('i dont know {} state'.format(to_state))
            return False


class newTask():
    """
    Non typed task , which have callback system to announce its subscribers
    """

    def __init__(self, name):
        self.taskname = name
        self.statem = StateMech(self)

        # dict like {event : [sub1, sub2...], ...}
        self.task_callbacks = {}

    def add_callback(self, event, subscriber):
        self.task_callbacks.setdefault(event, []).append(subscriber)

    def remove_callback(self, event, subscriber):
        # todo implement
        pass
        # self.task_callbacks.remove(cb)

    def notify(self, event):
        print('[{}] Notifing ... my dict : {}'.format(self, self.task_callbacks))
        try:
            subs = self.task_callbacks[event]
            for sub_i in subs:
                event.trigger_count += 1
                sub_i.someone_called_me('{} event {} triggered'.format(self, event))
        except KeyError as e:
            print('Error :', e)
            print('No-one to subscribe')

    def __repr__(self):
        return 'Task {}'.format(self.taskname)


class BuyGood(newTask):

    def __init__(self, name='Some buy task'):
        super().__init__(name)
        self.statem.change_state('ready_state')
        self.urgent = False

    def subscribe(self, event, subscriber):
        if isinstance(event, TaskEvent):
            self.add_callback(event, subscriber)
        else:
            print('event : {} \n subscriber : {}'.format(event, subscriber))
            print('nothing to subscribe')

    def do_work(self):
        success = choice([True, False])
        if success:
            self.statem.change_state('finish_state')
        else:
            self.statem.change_state('failed_state')


class DeliverGood(newTask):

    def __init__(self, name='Some deliver task'):
        super().__init__(name)
        self.statem.change_state('ready_state')
        self.urgent = False

    def subscribe(self, event, subscriber):
        if isinstance(event, TaskEvent):
            self.add_callback(event, subscriber)
        else:
            print('event : {} \n subscriber : {}'.format(event, subscriber))
            print('nothing to subscribe')


class cClient(cNodeBase, cSimNode):
    """
    many inputs - one output
    """
    def __init__(self, name):
        super().__init__(name)
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)
        self.connected_nodes = []
        self.debug_on = True

        self.pushing = True
        self.items = []
        self.items_ready_to_send = []
        self.conferment_jobs = []

    def connect_node(self, node):
        self.connected_nodes += [node]
        self.out_orders.connect_to_port(node.in_orders)

        # for bud in self.connected_buddies:
        #     # bud.connected_buddies += [self]
        #     # TODO make one-one port in agent and connect many-one to one-one
        #     # self.in_orders.connect_to_port(bud.out_orders)
        #     self.out_orders.connect_to_port(bud.in_orders)

    def someone_called_me(self, message=''):
        print('[{}] WHO CALLED MEH? with message {}'.format(self, message))
        self.gen_send_msg(when=8)

        print('HOLA')

    def gen_push_messages(self, when):
        """
        some custom gen, which creating a task
        :param when: int| wait time until task will create
        """
        yield self.timeout(when)
        task = BuyGood('Wanna_goods_C')
        self.send_msg(task, self.connected_nodes[0])
        print('[INFO]self.messages : ', self.messages)
        for msg in self.messages:
            msg = cMessage(*msg)
            self.sent_log('SENDING NEW TASK {}'.format(msg))
            self.out_orders.port_to_place.put(msg)
        self.messages = []
        yield self.timeout(5)

    def gen_send_msg(self, when=4):
        """
        adding  process on the fly
        """
        self.as_process(self.gen_push_messages(when))

    def gen_populate_tasks(self):
        tasks = [BuyGood('Wanna_goods_A'), BuyGood('Wanna_goods_B')]
        # sub for Done and Failed events
        [tsk.subscribe(DONE, self) for tsk in tasks]
        [tsk.subscribe(FAILED, self) for tsk in tasks]

        for tsk in tasks:
            self.send_msg(tsk, self.connected_nodes[0])

        for msg in self.messages:
            msg_to_send = cMessage(*msg)
            self.out_orders.port_to_place.put(msg_to_send)
        self.messages = []

        yield self.timeout(0)


    # GENERATORS
    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_nodes))

        if self.pushing:
            self.as_process(self.gen_populate_tasks())
            # self.as_process(self.gen_run_incoming_tasks())

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()


class cAgreement(cNodeBase, cSimNode):
    def __init__(self, name):
        super().__init__(name)
        # 1st pair
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)

        self.connected_nodes = []
        self.debug_on = True

        self.pushing = True
        self.items = []
        self.items_ready_to_send = []
        self.conferment_jobs = []


    def connect_node(self, node):
        self.connected_nodes += [node]
        self.out_orders.connect_to_port(node.in_orders)
    # def connect_buddies(self, buddies):
    #     self.connected_buddies += buddies
    #     for bud in self.connected_buddies:
    #         # bud.connected_buddies += [self]
    #         # TODO make one-one port in agent and connect many-one to one-one
    #         self.in_orders.connect_to_port(bud.out_orders)
    #         self.out_orders.connect_to_port(bud.in_orders)

    def someone_called_me(self, message=''):
        print('[{}] WHO CALLED MEH? with message {}'.format(self, message))

    # IN LOGIC
    def gen_run_incoming_tasks(self):
        """
        Task managing generator, where node reply to sender node if job was done successfully
        """
        while True:
            msg = yield self.in_orders.queue_local_jobs.get()
            tsk = msg.uows
            # Sub for done event
            tsk.subscribe(DONE, self)

            msg_to_send = cMessage(tsk, self, [self.connected_nodes[0]])
            self.out_orders.port_to_place.put(msg_to_send)

            yield self.empty_event()

    # GENERATORS
    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_nodes))

        if self.pushing:
            self.as_process(self.gen_run_incoming_tasks())
            # self.as_process(self.gen_run_incoming_tasks())

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()


class cMarketPlace(cNodeBase, cSimNode):
    def __init__(self, name):
        super().__init__(name)
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)
        self.connected_nodes = []
        self.debug_on = True

        self.pushing = True
        self.items = []
        self.items_ready_to_send = []
        self.conferment_jobs = []

    def connect_node(self, node):
        self.connected_nodes += [node]
        self.out_orders.connect_to_port(node.in_orders)
    # def connect_buddies(self, buddies):
    #     self.connected_buddies += buddies
    #     # for bud in self.connected_buddies:
    #         # bud.connected_buddies += [self]
    #         # TODO make one-one port in agent and connect many-one to one-one
    #         # self.in_orders.connect_to_port(bud.out_orders)
    #         # self.out_orders.connect_to_port(bud.in_orders)

    def someone_called_me(self, message=''):
        print('[{}] WHO CALLED MEH? with message {}'.format(self, message))

    def do_work(self, task):
        """
        Do work on task
        """
        success = choice([True, False])
        if success:
            task.statem.change_state('finish_state')
            return True
        else:
            task.statem.change_state('failed_state')
            return False

    # IN LOGIC
    def gen_run_incoming_tasks(self):
        """
        Task managing generator, where node reply to sender node if job was done successfully
        """
        while True:
            msg = yield self.in_orders.queue_local_jobs.get()
            tsk = msg.uows
            success = self.do_work(tsk)
            # Sub for done event
            # tsk.subscribe(DONE, self)
            # self.conferment_jobs.append(tsk)
            print('KTO KTO ?', self.connected_nodes)
            self.out_orders.wrong_jobs.put(msg)
            # todo make new Task to deliver goods if do_work succeed
            if success:
                deliver_task = DeliverGood('Take my goods')
                deliver_task.urgent = True
                msg_to_send = cMessage(deliver_task, self, [self.connected_nodes[0]])
                self.out_orders.port_to_place.put(msg_to_send)

            # msg_to_send = cMessage(tsk, self, [self.connected_buddies[0]])
            # self.out_orders.port_to_place.put(msg_to_send)

            print('{} is success ? :{}'.format(tsk, success))

            yield self.empty_event()

    # GENERATORS
    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_nodes))

        if self.pushing:
            self.as_process(self.gen_run_incoming_tasks())
            # self.as_process(self.gen_run_incoming_tasks())

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()