__author__ = 'User'
import model.nodes.metatypes as metatypes
import model.nodes.classes.Ports as ports
from model.nodes.classes.SimBase import cSimNode
from itertools import chain
import model.nodes.UoW as uows
from model.nodes.classes.Task import cTask, cDelivery
from model.nodes.classes.cMessage import cMessage


class cNode(cSimNode):
    """
        Base class of Economic agent. The point is that each agent could be connected to each other in \
        in free mode. They have popular communication method's and routine's.

        :method:'connect_buddies' provide neighbours connecting
            :par:'buddies' must be a list

        :method:'send_msg' sends message to all connected neighbours, but it doesnt duplicate to each ones
        :method:'send_msg_to' sends message to concrete neighbours, also they must be connected before
        :method:'stop_sending' force stopping of send generator

    """
    def __init__(self, name):
        super().__init__(name)
        self.money_account = metatypes.mtPileAccount()
        self.port_orders = ports.cPortUoWQueue(self)
        self.register_port(self.port_orders)
        self.msgtype = uows.cShipmentUoW(None, None, None)
        self.debug_on = True
        self.debug_delta = 5
        self.connected_buddies = []
        self.orders_count = 0
        self.pushing = False
        self.msg_count = 0
        self.neighbours = None
        self.messages = []

        # Pipeline logic

    # ================== Setup =======================

    def connect_buddies(self, buddies):
        self.connected_buddies += buddies
        for bud in buddies:
            bud.connected_buddies += [self]
            self.port_orders.connect_to_port(bud.port_orders)

    def send_msg_to(self, task, receiver):
        print('set to send to described one ')
        # basic_uow = uows.cBuyGoodsUoW('water', 11, 15)
        msg = [task, self, [receiver]]
        self.messages.append(msg)
        if not self.pushing:
            self.pushing = True
    # =================================================

    def stop_sending(self):
        self.pushing = False

    def init_sim(self):
        super().init_sim()

    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()

    # ================ Sim methods ====================
    '''
    def stop_sending(self):
        self.pushing = False

    def init_sim(self):
        super().init_sim()

    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.debug_on:
            self.as_process(self.gen_debug())

        # IDEA for action in self.actions ; actions declare in children
        if self.pushing:
            # print("I AM HERE")
            self.as_process(self.gen_send_spam())

        yield self.empty_event()

    def gen_send_spam(self):
        for i in range(5):
            for msg in self.messages:
                msg = cMessage(*msg)
                self.port_orders.put_uow(msg)
            yield self.timeout(5)
    '''
    # =====================================================

    # ================ DEBUG Generator ====================

    def debug(self, state, t=5):
        if state:
            self.debug_on = True
            self.debug_delta = t
        elif not state:
            self.debug_on = False
        else:
            raise ValueError('state must be True or False')

    def gen_debug(self):
        while True:
            for port in self.ports.values():
                self.sent_log(port.queues)

            cTask.tm.status()
            yield self.timeout(self.debug_delta)

    # =====================================================


class cNone_source(cNode):
    """
        Source node, dont have inputs
    """

    def __init__(self, name):
        super().__init__(name)


class cNone_sink(cNode):
    """
        Sink node, dont have outputs
    """
    def __init__(self, name):
        super().__init__(name)


class cNone_hub(cNode):
    """
        Hub node, controls flow of data
    """
    def __init__(self, name, inp_node=None, out_nodes=None):
        super().__init__(name)
        self.input = inp_node
        self.out_nodes = out_nodes

        self.in_port = self.port_orders
        self.out_port = ports.cPortUoWQueue(self)

    def connect_nodes(self, inp_node, out_nodes):
        self.connected_buddies.append(inp_node)
        self.connected_buddies += out_nodes

        # FIXME implement abstract port naming
        self.in_port.connect_to_port(inp_node.port_orders)
        inp_node.connected_buddies += [self]

        for bud in out_nodes:
            bud.connected_buddies += [self]
            self.out_port.connect_to_port(bud.port_orders)

    def connect_buddies(self, buddies):
        raise Exception('This node use in_port and out_ports')

    def activate(self):
        for bud in self.connected_buddies:
            # self.filtered_ports[]
            pass
        self.pushing = True

    def condition(self, **kwargs):
        self.condition = kwargs

    def _action(self, task):
        for attr, node in self.condition.items():
            if hasattr(task, attr):
                temp_attr = getattr(task, attr)
                print('TEMP ATTR', temp_attr)
                if temp_attr:
                    task.run('True')
                    msg = [task, self, [self.condition[attr]]]
                    self.messages.append(msg)
                else:
                    task.set_state('NO-WAY')
                    msg = [task, self, [self]]
                    self.in_port.put_uow(cMessage(*msg))


    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.debug_on:
            self.as_process(self.gen_debug())

        if self.pushing:
            self.as_process(self.gen_filter())

        yield self.empty_event()

    def gen_filter(self):
        while True:
            msg = yield self.in_port.get_uow()
            print('NOVOSELOY ', msg)
            # unpack message
            task = msg.uows
            self._action(task)

            for msg in self.messages:
                msg_to_send = cMessage(*msg)
                self.messages.remove(msg)

                self.out_port.put_uow(msg_to_send)

            yield self.timeout(0)


class cNone_agent(cNode):
    """
        Blue node, complex
    """
    def __init__(self, name):
        super().__init__(name)

    def activate(self):
        self.pushing = True

    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.debug_on:
            self.as_process(self.gen_debug())

        if self.pushing:
            self.as_process(self.populate_tasks())

        yield self.empty_event()

    def populate_tasks(self):
        items = [cDelivery('matflow1', True), cDelivery('matflow2'),
                 cDelivery('matflow3', True), cDelivery('matflow4'),
                 cDelivery('matflow5'), cDelivery('matflow6', True),
                 cDelivery('matflow7'), cDelivery('matflow8')]

        [tsk.set_start('PENDING') for tsk in items]

        for el in items:
            self.send_msg_to(el, self.connected_buddies[0])

        for msg in self.messages:
            msg_to_send = cMessage(*msg)
            self.port_orders.put_uow(msg_to_send)

        yield self.timeout(0)


class cNone_func(cNode):
    """
        Green node, simple in-time operations
    """
    def __init__(self, name):
        super().__init__(name)