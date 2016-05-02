from model.nodes.classes.Node_func_v2 import cNodeBase
from model.nodes.classes.SimBase import cSimNode
import model.nodes.classes.Ports_v2 as ports
from model.nodes.classes.cMessage import cMessage
from random import randint, choice
from model.nodes.utils.custom_operators import do_expression
from collections import namedtuple
from simpy.events import Event,AllOf,AnyOf
from model.nodes.wallet import cWallet
import logging

class StatesContainer():
    """
    State holding class. Its provide tasks switching mechanics and sending reply events
    :param parent | parent cls
    """
    STATES = ['null', 'fulfilled', 'failed']

    def __init__(self, parent):
        self.curstate = None
        self.parent = parent
        # self.event_mapping = {}


    def set_event_mapping(self, state, ev):
        """
        Set from tasks dictionary like : {fulfilled: 'simpy.event' class, failed: 'simpy.event' class...}
        :param state: str| key for mapping
        :param ev: 'simpy.event'| event for mapping
        """
        if state not in self.STATES:
            pass
        else:
            self.event_mapping[state] = ev

    def set_init_state(self, state):
        self.curstate = state

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
            # print(self.parent.events_map)
            if self.curstate in self.parent.events_map:
                sim_event = self.parent.events_map[self.curstate]
                self.parent.notify(sim_event)
            return True

        else:
            return False


class BaseTask():
    """
    Non typed task , which have callback system to announce its subscribers
    """

    def __init__(self, name, env):
        self.taskname = name
        self.env = env
        self.states = StatesContainer(self)
        self.events_map = {}

        # dict like {event : [sub1, sub2...], ...}
        self.task_callbacks = {}

    def notify(self, event):
        """
        Triggering signal for given event, and calling old-style callbacks
        :param event : 'simpy.event' instance
        """
        # todo Error checking
        # subs = self.task_callbacks[event]
        event.succeed()

    def __repr__(self):
        return 'Task {}'.format(self.taskname)


class BaselogicTask(BaseTask):
    """
    Concrete implementation of 'BaseTask'
    :param name : str | name of 'RequestGoods' instance
    :param env : 'simpy.Enviroment' cls | delegated from node environment
    """

    def __init__(self, name='Some buy task', env=None):
        super().__init__(name, env)
        self.states.set_init_state('null')
        self.party = None
        self.good = None
        self.qtty = None

    def subscribe(self, event_name, subscriber=None):
        """
        Subscribing for event
        :param event_name : 'simpy.event' | simpy event
        :param subscriber : 'cNodeBase' instance | link to class which should have callback function
        """
        if event_name not in self.events_map.keys():
            my_event = self.env.event()
            self.events_map[event_name] = my_event
        else:
            my_event = self.events_map[event_name]

        return my_event

    def setup(self, good, qtty):
        self.good, self.qtty = good, qtty

    def change_state(self, to_state):
        self.states.change_state(to_state)

class RequestGoods(BaselogicTask):
    pass

class DeliveryGoods(BaselogicTask):
    pass

class RequestMoney(BaselogicTask):
    pass

class DeliveryMoney(BaselogicTask):
    pass


# Nodes
# ######################################


# Client (Blue Node)
class cClient(cNodeBase, cSimNode):

    def __init__(self, name):
        super().__init__(name)
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)
        self.connected_nodes = []
        self.pushing = True

        self.item_wallet = cWallet()
        self.money_wallet = cWallet()

    def connect_node(self, node):
        self.connected_nodes += [node]
        self.out_orders.connect_to_port(node.in_orders)

    def init_sim(self):
        super().init_sim()
        self.item_wallet.spawn_pile('Sushi', 0)
        self.money_wallet.spawn_pile('USD', 1000)

    # GENERATORS
    def my_generator(self):
        self.sent_log("I'm {} with connected buddies : {}".format(self.name, self.connected_nodes))

        if self.pushing:
            self.as_process(self.gen_run_incoming_tasks())
            self.as_process(self.sushi_buyer(timing=4))

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()

    # IN LOGIC
    def gen_run_incoming_tasks(self):
        while True:
            # listen to incomes
            msg = yield self.in_orders.queue_local_jobs.get()
            task = msg.uows

            if isinstance(task, RequestMoney):
                self.as_process(self.gen_sent_money(task))

            elif isinstance(task, DeliveryGoods):
                self.item_wallet.add_items(task.good, task.qtty)

            yield self.empty_event()

    # OUT LOGIC
    def sushi_buyer(self, timing):
        while True:
            yield self.timeout(timing)
            self.sent_log('new request fro sushi',logging.DEBUG)
            # creating task
            sushi_request_task = RequestGoods('Sushi_request', self.simpy_env)
            good, qtty = 'Sushi', 5
            sushi_request_task.setup(good, qtty)
            fulfilled_event = sushi_request_task.subscribe('fulfilled')

            self.send_msg(sushi_request_task, self.connected_nodes[0])
            for msg in self.messages:
                msg_to_send = cMessage(*msg)
                self.out_orders.port_to_place.put(msg_to_send)
            self.messages = []

    def gen_sent_money(self, requester_task):
        # take 'from warehouse/wallet
        yield self.as_process(self.money_wallet.gen_take_qtty(requester_task.good, requester_task.qtty))

        requester_task.change_state('fulfilled')
        delivery_task = DeliveryMoney('USD', self.simpy_env)
        delivery_task.setup(requester_task.good, requester_task.qtty)
        delivery_event = delivery_task.subscribe('fulfilled')
        msg_to_send = cMessage(delivery_task, self, [self.connected_nodes[0]])
        self.out_orders.port_to_place.put(msg_to_send)


# Shop(Blue Node)
class cShop(cNodeBase, cSimNode):

    def __init__(self, name):
        super().__init__(name)
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)
        self.connected_nodes = []
        self.pushing = True

        self.item_wallet = cWallet()
        self.money_wallet = cWallet()

    def connect_node(self, node):
        self.connected_nodes += [node]
        self.out_orders.connect_to_port(node.in_orders)


    def init_sim(self):
        super().init_sim()
        self.item_wallet.spawn_pile('Sushi', 999)
        self.money_wallet.spawn_pile('USD', 1000)

    # GENERATORS
    def my_generator(self):
        if self.pushing:
            self.as_process(self.gen_run_incoming_tasks())

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()

    # IN LOGIC
    def gen_run_incoming_tasks(self):
        while True:
            # listen to incomes
            msg = yield self.in_orders.queue_local_jobs.get()
            task = msg.uows
            if isinstance(task, RequestGoods):
                self.as_process(self.gen_deliver_good(task))
            if isinstance(task, DeliveryMoney):
                self.money_wallet.add_items(task.good, task.qtty)
            yield self.empty_event()

    def gen_deliver_good(self, requester_task):
        # take from warehouse/wallet
        yield self.as_process(self.item_wallet.gen_take_qtty(requester_task.good, requester_task.qtty))

        requester_task.change_state('fulfilled')
        delivery_task = DeliveryGoods('DeliveryGoods', self.simpy_env)
        delivery_task.setup('Sushi', self.simpy_env)
        delivery_task.setup(requester_task.good, requester_task.qtty)
        delivery_event = delivery_task.subscribe('fulfilled')
        msg_to_send = cMessage(delivery_task, self, [self.connected_nodes[0]])
        self.out_orders.port_to_place.put(msg_to_send)

# Agreement (Blue Node)
class cAgreement(cNodeBase, cSimNode):
    partyA = 0
    partyB = 1

    def __init__(self, name):
        super().__init__(name)
        # 1st pair
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)

        self.connected_nodes = []
        self.pushing = True

        self.price_dict = {'Sushi': 100}

    def connect_node(self, node):
        self.connected_nodes += [node]
        self.out_orders.connect_to_port(node.in_orders)

    # GENERATORS
    def my_generator(self):
        if self.pushing:
            self.as_process(self.gen_run_incoming_tasks())
            # self.as_process()

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()

    # IN LOGIC
    def gen_run_incoming_tasks(self):
        while True:
            msg = yield self.in_orders.queue_local_jobs.get()

            task = msg.uows
            # check if task is request
            if isinstance(task, RequestGoods):
                evdone = task.subscribe('fulfilled')
                task.party = self.partyB
                msg_to_send = cMessage(task, self, [self.connected_nodes[0]])
                self.out_orders.port_to_place.put(msg_to_send)

            elif isinstance(task, DeliveryGoods):
                evdone = task.subscribe('fulfilled')
                money_sum = task.qtty * self.price_dict[task.good]
                self.as_process(self.gen_ask_money(evdone, money_sum), repr='ask_money')
                task.party = self.partyA

                msg_to_send = cMessage(task, self, [self.connected_nodes[0]])
                self.out_orders.port_to_place.put(msg_to_send)

            elif isinstance(task, DeliveryMoney):
                evdone = task.subscribe('fulfilled')
                task.party = self.partyA
                msg_to_send = cMessage(task, self, [self.connected_nodes[0]])
                self.out_orders.port_to_place.put(msg_to_send)

            yield self.empty_event()

    def gen_ask_money(self, event_delivered, money_sum):
        yield event_delivered
        task = RequestMoney('RequestMoney', self.simpy_env)
        task.setup(good='USD', qtty=money_sum)
        task.party = self.partyA
        msg_to_send = cMessage(task, self, [self.connected_nodes[0]])
        self.out_orders.port_to_place.put(msg_to_send)

# Hub (Orange Node)

class cHubNode(cNodeBase, cSimNode):
    """
        ?? 1 input--->[HUB]--->Multiple outputs
    """

    # todo check double connect
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

        self.connected_nodes = []
        self.pushing = True

        self.conditions_dict = {}

    def connect_nodes(self, inp_nodes=None, out_nodes=None):
        if inp_nodes:
            self.inp_nodes = inp_nodes
            self.connected_nodes += inp_nodes

            for bud in inp_nodes:
                # bud.connected_nodes += [self]
                self.in_orders.connect_to_port(bud.out_orders)

        if out_nodes:
            self.out_nodes = out_nodes
            self.connected_nodes += out_nodes
            # inp_nodes.connected_buddies += [self]
            for bud in out_nodes:
                # bud.connected_nodes += [self]
                self.out_orders.connect_to_port(bud.in_orders)

    def condition(self, conds=None, randomize=False):
        self.pushing = True

        expression = namedtuple('expression', 'attr expr val')
        for node, express in conds.items():
            attr, expr, val = express.split(' ')
            self.conditions_dict[expression(attr, expr, val)] = node


    def _action(self, task):
        got_match = False
        # TODO make attributes priority to solve multiple successful conditions
        for attr_i in task.__dict__.keys():
            for expression in self.conditions_dict.keys():
                if attr_i == expression.attr:
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
                            self.sent_log('sending to {}'.format(receiver))
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
                pass
                # tsk.run('True')
            else:
                self.sent_log('DID NOT MATCH')
                self.out_orders.wrong_jobs.put(msg)

            for msg in self.messages:
                msg_to_send = cMessage(*msg)
                self.messages.remove(msg)
                self.out_orders.port_to_place.put(msg_to_send)

            yield self.empty_event()

    # GENERATORS
    def my_generator(self):
        if self.debug_on:
            self.as_process(self.gen_debug())

        if self.pushing:
            self.as_process(self.gen_do_incoming_tasks(), repr='FILTERING')

        yield self.empty_event()


# System setup
def test1():
    from model.model import cNodeFieldModel
    the_model = cNodeFieldModel()
    node1 = cClient('Retail client')
    node2 = cAgreement('Retail agreement')
    node3 = cShop('Shop')
    node4 = cHubNode('Filter hub')

    node1.connect_node(node2)
    node2.connect_node(node4)
    node4.connect_nodes(inp_nodes=[node2], out_nodes=[node1, node3])
    node3.connect_node(node2)

    cond_dict = {node1: 'party = 0',
                 node3: 'party = 1'}
    node4.condition(cond_dict)

    the_model.addNodes([node1, node2, node3, node4])

    return the_model
