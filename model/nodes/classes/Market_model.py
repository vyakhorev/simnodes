from model.nodes.classes.Node_func_v2 import cNodeBase
from model.nodes.classes.SimBase import cSimNode
import model.nodes.classes.Ports_v2 as ports
from model.nodes.classes.cMessage import cMessage
from random import randint, choice
from simpy.events import Event,AllOf,AnyOf

class TaskEvent():
    """
    Base class for Tasks events
    deprecated ???
    """

    def __init__(self, name='Event'):
        self.name = name
        self.trigger_count = 0

    def __repr__(self):
        return '<{} Event({})>'.format(self.name, self.trigger_count)

# READY = TaskEvent('READY')
# DONE = TaskEvent('DONE')
# FAILED = TaskEvent('FAILED')


class StateMech():
    """
    State holding class. Its provide tasks switching mechanics and sending reply events
    :param parent | parent cls
    """
    STATES = ['ready_state', 'finish_state', 'failed_state']

    def __init__(self, parent):
        self.curstate = None
        self.parent = parent
        self.event_mapping = {}

    def set_event_mapping(self, state, ev):
        """
        Set from tasks dictionary like : {finish_state: 'simpy.event' class, failed_state: 'simpy.event' class...}
        :param state: str| key for mapping
        :param ev: 'simpy.event'| event for mapping
        """
        if state not in self.STATES:
            print('dont know about this state')
        else:
            self.event_mapping[state] = ev

    def change_state(self, to_state):
        """
        Changing self state and calling parent's notify method
        :param to_state : str| string alias for pseudo-state
        """
        """
        :param to_state | str, string alias for pseudo-state
        """
        # todo check if state dont actually changing
        if to_state in self.STATES:
            self.curstate = to_state

            if self.curstate == 'finish_state':
                DONE = self.event_mapping[self.curstate]
                self.parent.notify(DONE)
            elif self.curstate == 'failed_state':
                pass
                # FAILED = self.event_mapping[self.curstate]
                # self.parent.notify(FAILED)

        else:
            print('i dont know {} state'.format(to_state))
            return False


class newTask():
    """
    Non typed task , which have callback system to announce its subscribers
    """

    def __init__(self, name, env):
        self.taskname = name
        self.env = env
        self.statem = StateMech(self)
        self.events_map = {}

        # dict like {event : [sub1, sub2...], ...}
        self.task_callbacks = {}

    def add_callback(self, event, subscriber):
        """
        Adding old-style callback
        """
        self.task_callbacks.setdefault(event, []).append(subscriber)

    def remove_callback(self, event, subscriber):
        # todo implement
        pass
        # self.task_callbacks.remove(cb)

    def notify(self, event):
        """
        Triggering signal for given event, and calling old-style callbacks
        :param event : 'simpy.event' instance
        """
        # todo Error checking
        print('[{}] Notifing ... my dict : {}'.format(self, self.task_callbacks))
        subs = self.task_callbacks[event]
        print('subs {}'.format(subs))
        event.succeed()
        # this could be integrated in event callbacks
        for sub_i in subs:
            sub_i.someone_called_me('{} event {} triggered'.format(self, event))

            # try:
            #     subs = self.task_callbacks[event]
            #     for sub_i in subs:
            #         event.trigger_count += 1
            #         if self.events_map[event]:
            #             print('AAAAAAAAAAAAAAAAAAAAAAAAA', self.events_map)
            #             print(self.events_map[event].callbacks)
            #             self.events_map[event].succeed()
            #             self.events_map[event] = self.env.event()
            #         sub_i.someone_called_me('{} event {} triggered'.format(self, event))
            #
            # except KeyError as e:
            #     print('Error :', e)
            #     print('No-one to subscribe')

    def __repr__(self):
        return 'Task {}'.format(self.taskname)


class BuyGood(newTask):
    """
    Concrete implementation of 'newTask'
    :param name : str | name of 'BuyGood' instance
    :param env : 'simpy.Enviroment' cls | delegated from node environment
    """

    def __init__(self, name='Some buy task', env=None):
        super().__init__(name, env)
        self.statem.change_state('ready_state')
        self.urgent = False

    def subscribe(self, event, subscriber):
        """
        Subscribing for event
        :param event : 'simpy.event' | simpy event
        :param subscriber : 'cNodeBase' instance | link to class which should have callback function
        """
        if event not in self.events_map.keys():
            my_event = self.env.event()
            self.events_map[event] = my_event
            self.statem.set_event_mapping('finish_state', my_event)
            self.add_callback(my_event, subscriber)
        else:
            my_event = self.events_map[event]
            self.statem.set_event_mapping('finish_state', my_event)
            self.add_callback(my_event, subscriber)
        return my_event
        # # old
        # if isinstance(event, TaskEvent):
        #     self.add_callback(event, subscriber)
        #     if self.env:
        #         my_event = self.env.event()
        #         self.events_map[event] = my_event
        #         return my_event
        # else:
        #     print('event : {} \n subscriber : {}'.format(event, subscriber))
        #     print('nothing to subscribe')


class DeliverGood(newTask):

    def __init__(self, name='Some deliver task', env=None):
        super().__init__(name, env)
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
        task = BuyGood('Wanna_goods_C', self.simpy_env)
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
        tasks = [BuyGood('Wanna_goods_A', self.simpy_env), BuyGood('Wanna_goods_B', self.simpy_env)]
        # sub for Done and Failed events
        cb_events = [tsk.subscribe('DONE', self) for tsk in tasks]
        print('EVENTSSSSSSSSSSSSSSSSSSSSSS', cb_events)
        for ev in cb_events:
            ev.callbacks.append(self.my_callback)
        #     print(ev.triggered)
        self.as_process(self.wait_for_callbacks_any(cb_events))
        self.as_process(self.wait_for_callbacks_all(cb_events))
        [tsk.subscribe('FAILED', self) for tsk in tasks]

        for tsk in tasks:
            self.send_msg(tsk, self.connected_nodes[0])

        for msg in self.messages:
            msg_to_send = cMessage(*msg)
            self.out_orders.port_to_place.put(msg_to_send)
        self.messages = []

        yield self.timeout(0)

    def my_callback(self, event):
        self.sent_log('Called back from {}'.format(event))

    # Events working with Any and All conditions
    # ###########################################
    def wait_for_callbacks_any(self, events):
        a = AnyOf(self.simpy_env, events)
        yield a
        print('ANY DONE SUCCESSFULLY !!!')

    def wait_for_callbacks_all(self, events):
        a = AllOf(self.simpy_env, events)
        yield a
        print('ALL DONE SUCCESSFULLY !!!')
    # ###########################################

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
            # print('RRRRRRRR', tsk)
            evdone = tsk.subscribe('DONE', self)

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