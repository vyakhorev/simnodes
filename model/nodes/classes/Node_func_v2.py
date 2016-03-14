__author__ = 'User'
import model.nodes.metatypes as metatypes
# import model.nodes.classes.Ports as ports
import model.nodes.classes.Ports_v2 as ports
from model.nodes.classes.SimBase import cSimNode
import model.nodes.UoW as uows
from model.nodes.classes.Task import cTask, cDelivery
from model.nodes.classes.cMessage import cMessage

from model.nodes.utils.custom_operators import do_expression

from itertools import chain
from functools import partialmethod
from random import choice, randint
from collections import namedtuple
from pprint import pprint

# Node types :
class NodeType(type):
    def __str__(cls):
        return cls.mystr

Registry = {}
class AgentType(metaclass=NodeType):
    mystr = 'AgentType'

class HubType(metaclass=NodeType):
    mystr = 'HubType'

class FuncType(metaclass=NodeType):
    mystr = 'FuncType'

class SinkType(metaclass=NodeType):
    mystr = 'SinkType'

node_types = {AgentType, HubType, FuncType, SinkType}

class cNodeBase():
    """
    Node's type-free logic here.
    Compound class, don't call it directly
    """
    def __init__(self, name):
        self.messages = []
        super(cNodeBase, self).__init__(name)
        self.parent = None

    def send_msg(self, task, receiver):
        msg = [task, self, [receiver]]
        self.messages.append(msg)
        if not self.pushing:
            self.pushing = True

    def init_sim(self):
        super().init_sim()

    def gen_debug(self):
        while True:
            for port in self.ports.values():
                self.sent_log(port.queues)

            cTask.tm.status()
            yield self.timeout(2)


class cAgentNodeSimple(cNodeBase, cSimNode):
    """
    many inputs - one output
    """
    def __init__(self, name):
        super().__init__(name)
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)
        self.connected_buddies = []
        self.debug_on = True

        self.pushing = True
        self.items = []
        self.items_ready_to_send = []
        self.conferment_jobs = []

    def connect_buddies(self, buddies):
        self.connected_buddies += buddies
        for bud in self.connected_buddies:
            # bud.connected_buddies += [self]
            # TODO make one-one port in agent and connect many-one to one-one
            self.in_orders.connect_to_port(bud.out_orders)
            self.out_orders.connect_to_port(bud.in_orders)

    def activate(self):
        self.pushing = True

    def set_tasks(self, tasks=None):
        self.items = tasks

    def gen_populate_tasks(self):
        while True:
            [self.items_ready_to_send.append(tsk) for tsk in self.items if tsk.start_time == self.simpy_env.now]

            self.sent_log('populating... {}'.format(self.items_ready_to_send))

            # make additional state
            [tsk.set_start('PENDING') for tsk in self.items_ready_to_send]

            for el in self.items_ready_to_send:
                # FIXME poor line... self.connected_buddies[0]
                if hasattr(el, 'direct_address'):
                    print('ALOHA')
                    self.send_msg(el, el.direct_address)
                else:
                    self.send_msg(el, self.connected_buddies[0])
                    self.items.remove(el)

            for msg in self.messages:
                msg_to_send = cMessage(*msg)
                self.out_orders.port_to_place.put(msg_to_send)
                self.messages = []

            # clear buffer
            self.items_ready_to_send = []
            yield self.timeout(1)

    def gen_push_messages(self):
        for msg in self.messages:
            msg = cMessage(*msg)
            self.out_orders.port_to_place.put(msg)
        yield self.timeout(5)

    def gen_send_msg(self):
        self.as_process(self.gen_push_messages())
        yield self.timeout(0)

    # IN LOGIC
    def gen_run_incoming_tasks(self):
        """
        Task managing generator, where node reply to sender node if job was done successfully
        """
        while True:
            msg = yield self.in_orders.queue_local_jobs.get()
            tsk = msg.uows
            self.sent_log('got {}'.format(tsk))

            if tsk.curState == 'CONFERMENT':
                self.conferment_jobs.append(tsk)

            elif tsk.curState == 'PENDING':
                tsk.run('True')

                if tsk.curState == 'DONE':
                    self.sent_log('send reply to sender node {} , task : {}'.format(msg.sender, tsk))
                    tsk.name = str(tsk.name)+' reply'
                    tsk.set_state('CONFERMENT')

                    msg_to_send = cMessage(tsk, self, [msg.sender])
                    self.out_orders.port_to_place.put(msg_to_send)

            yield self.empty_event()

    # GENERATORS
    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.pushing:
            self.as_process(self.gen_populate_tasks())
            # self.as_process(self.gen_run_incoming_tasks())

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()


class cAgentNode(cNodeBase, cSimNode):
    """
        Multiple inputs--->[AGENT]
                       <---
    """
    myType = AgentType

    def __init__(self, name):
        super(cAgentNode, self).__init__(name)
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoManyQueue(self)  # ??
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)
        self.connected_buddies = []
        self.debug_on = True

        self.pushing = True
        self.items = []
        self.items_ready_to_send = []
        self.conferment_jobs = []
        # self.messages = []

    def connect_buddies(self, buddies):
        print('buddies : ', buddies)
        self.connected_buddies += buddies
        for bud in self.connected_buddies:
            print('69696')
            print(self.connected_buddies)
            print(bud)
            # bud.connected_buddies += [self]
            # TODO make one-one port in agent and connect many-one to one-one
            self.in_orders.connect_to_port(bud.out_orders)
            self.out_orders.connect_to_port(bud.in_orders)

    # OUT LOGIC

    def activate(self):
        self.pushing = True

    def set_tasks(self, tasks=None):
        self.items = tasks

    def gen_populate_tasks(self):
        while True:
            [self.items_ready_to_send.append(tsk) for tsk in self.items if tsk.start_time == self.simpy_env.now]

            self.sent_log('populating... {}'.format(self.items_ready_to_send))

            # make additional state
            [tsk.set_start('PENDING') for tsk in self.items_ready_to_send]

            for el in self.items_ready_to_send:
                # FIXME poor line... self.connected_buddies[0]
                if hasattr(el, 'direct_address'):
                    print('ALOHA')
                    self.send_msg(el, el.direct_address)
                else:
                    self.send_msg(el, self.connected_buddies[0])
                    self.items.remove(el)

            for msg in self.messages:
                msg_to_send = cMessage(*msg)
                self.out_orders.port_to_place.put(msg_to_send)
                self.messages = []

            # clear buffer
            self.items_ready_to_send = []
            yield self.timeout(1)

    def gen_push_messages(self):
        for msg in self.messages:
            msg = cMessage(*msg)
            self.out_orders.port_to_place.put(msg)
        yield self.timeout(5)

    def gen_send_msg(self):
        self.as_process(self.gen_push_messages())
        yield self.timeout(0)

    # IN LOGIC
    def gen_run_incoming_tasks(self):
        """
        Task managing generator, where node reply to sender node if job was done successfully
        """
        while True:
            msg = yield self.in_orders.queue_local_jobs.get()
            tsk = msg.uows
            self.sent_log('got {}'.format(tsk))

            if tsk.curState == 'CONFERMENT':
                self.conferment_jobs.append(tsk)

            elif tsk.curState == 'PENDING':
                tsk.run('True')

                if tsk.curState == 'DONE':
                    self.sent_log('send reply to sender node {} , task : {}'.format(msg.sender, tsk))
                    tsk.name = str(tsk.name)+' reply'
                    tsk.set_state('CONFERMENT')

                    msg_to_send = cMessage(tsk, self, [msg.sender])
                    self.out_orders.port_to_place.put(msg_to_send)

            yield self.empty_event()

    # GENERATORS
    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.pushing:
            self.as_process(self.gen_populate_tasks())
            # self.as_process(self.gen_run_incoming_tasks())

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()


class cHubNode(cNodeBase, cSimNode):
    """
        ?? 1 input--->[HUB]--->Multiple outputs
    """
    myType = HubType

    def __init__(self, name, inp_nodes=None, out_nodes=None):
        self.inp_nodes = inp_nodes
        self.out_nodes = out_nodes

        super().__init__(name)
        # here we pull tasks
        self.in_orders = ports.cManytoOneQueue(self)
        # here we push tasks
        self.out_orders = ports.cOnetoManyQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)

        self.connected_buddies = []
        self.debug_on = True

        self.pushing = True

        self.conditions_dict = {}
        self.randomize = False

    def add_out_nodes(self, out_nodes):
        self.out_nodes += out_nodes
        self.connected_buddies += out_nodes
        for bud in out_nodes:
            bud.connected_buddies += [self]
            self.out_orders.connect_to_port(bud.in_orders)

    def connect_nodes(self, inp_nodes=None, out_nodes=None):
        if inp_nodes:
            self.inp_nodes = inp_nodes
            self.connected_buddies += inp_nodes
            for bud in inp_nodes:
                bud.connected_buddies += [self]
                self.in_orders.connect_to_port(bud.out_orders)

        if out_nodes:

            self.out_nodes = out_nodes
            self.connected_buddies += out_nodes
            # inp_nodes.connected_buddies += [self]
            for bud in out_nodes:
                bud.connected_buddies += [self]
                self.out_orders.connect_to_port(bud.in_orders)

    # def condition(self, **kwargs):
    #     self.pushing = True
    #     expression = namedtuple('expression', 'attr expr val')
    #
    #     for node, express in kwargs.items():
    #         print(node)
    #         attr, expr, val = express.split(' ')
    #         self.conditions_dict[expression(attr, expr, val)] = node

    def condition(self, conds=None, randomize=False):
        self.pushing = True

        if (not randomize) and conds:
            expression = namedtuple('expression', 'attr expr val')

            for node, express in conds.items():
                print(node)
                attr, expr, val = express.split(' ')
                self.conditions_dict[expression(attr, expr, val)] = node
        elif (not randomize) and (not conds):
            raise AttributeError('No condition were set')

        else:
            self.randomize = True
            self._action = self._randomaction

    def _randomaction(self, task):
        receiver = choice(self.out_nodes)
        self.sent_log('Gonna send task {} to receiver {}'.format(task, receiver))
        msg = [task, self, [receiver]]
        self.messages.append(msg)
        return True

    def _action(self, task):
        got_match = False
        # TODO make attributes priority to solve multiple successful conditions
        for attr_i in task.__dict__.keys():
            for expression in self.conditions_dict.keys():
                if attr_i == expression.attr:
                    print('CHECKING :{}, and  {} fulfill {} {}'.format(attr_i, expression.attr, expression.expr,
                                                                       expression.val))

                    # TODO solve duplicating...
                    if expression.val in ['true', 'True', 'false', 'False']:
                        if getattr(task, attr_i) == (expression.val in ['True', 'true']):
                            got_match = True
                            self.sent_log('Gonna send task {} to receiver {}'.format(task,
                                                                                     self.conditions_dict[expression]))
                            receiver = self.conditions_dict[expression]
                            msg = [task, self, [receiver]]
                            self.messages.append(msg)
                    else:
                        if do_expression(getattr(task, attr_i), expression.expr, expression.val):
                            got_match = True
                            self.sent_log('Gonna send task {} to receiver {}'.format(task,
                                                                                     self.conditions_dict[expression]))
                            receiver = self.conditions_dict[expression]
                            msg = [task, self, [receiver]]
                            self.messages.append(msg)
        if got_match:
            return True
        else:
            return False

    # IN / OUT LOGIC
    def gen_do_incoming_tasks(self):
        while True:
            msg = yield self.in_orders.queue_local_jobs.get()
            tsk = msg.uows
            success = self._action(tsk)
            if success:
                tsk.run('True')
            else:
                self.out_orders.wrong_jobs.put(msg)

            for msg in self.messages:
                msg_to_send = cMessage(*msg)
                self.messages.remove(msg)

                self.out_orders.port_to_place.put(msg_to_send)

            yield self.empty_event()

    # GENERATORS
    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.debug_on:
            self.as_process(self.gen_debug())

        if self.pushing:
            self.as_process(self.gen_do_incoming_tasks(), repr='FILTERING')

        yield self.empty_event()


class cFuncNode(cNodeBase, cSimNode):
    """
      input(1) ---> [FUNC] ---> output(1)
    """
    myType = FuncType

    def __init__(self, name, inp_node=None, out_node=None):
        self.input_node, self.out_node = inp_node, out_node

        super().__init__(name)
        # TODO add 'out' or 'in' to Queue repr
        self.in_orders = ports.cOnetoOneInpQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)

        self.connected_buddies = []
        self.debug_on = True
        self.pushing = True

    def connect_nodes(self, inp_node, out_node):
        self.input_node, self.out_node = inp_node, out_node
        self.connected_buddies += [inp_node]

        self.in_orders.connect_to_port(inp_node.out_orders)
        inp_node.connected_buddies += [self]

        if out_node:
            self.connected_buddies += [out_node]
            self.out_orders.connect_to_port(out_node.in_orders)
            out_node.connected_buddies += [self]

    def _action(self, task):
        task.tags = '#I_was_in {}'.format(self.name)
        return True

    # IN LOGIC
    def gen_do_incoming_tasks(self):
        while True:
            msg = yield self.in_orders.queue_local_jobs.get()
            self.sent_log('Got {}'.format(msg))
            tsk = msg.uows
            success = self._action(tsk)
            if success:
                # FIXME bad
                msg = [tsk, self, [self.connected_buddies[0]]]
                self.messages.append(msg)
            else:
                self.out_orders.wrong_jobs.put(msg)

            for msg in self.messages:
                msg_to_send = cMessage(*msg)
                self.messages.remove(msg)
                self.out_orders.port_to_place.put(msg_to_send)

        yield self.empty_event()

    # GENERATORS
    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.debug_on:
            self.as_process(self.gen_debug())

        if self.pushing:
            self.as_process(self.gen_do_incoming_tasks())

        yield self.empty_event()

node_types_dict = {'AgentType': cAgentNodeSimple,
                   'HubType': cHubNode,
                   'FuncType': cFuncNode}
