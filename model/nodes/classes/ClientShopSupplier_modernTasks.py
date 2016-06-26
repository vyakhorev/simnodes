
from model.nodes.classes.Node_func_v2 import cNodeBase
from model.nodes.classes.SimBase import cSimNode
import model.nodes.classes.Ports_v2 as ports
from model.nodes.classes.cMessage import cMessage
from random import randint, choice
from model.nodes.utils.custom_operators import do_expression
from collections import namedtuple
from simpy.events import Event,AllOf,AnyOf
from model.nodes.wallet2 import cWallet

import model.nodes.simulengin.simulengin as simulengin

import logging # each node has it's own logger

# ######################################
# Tasks
# ######################################

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
    CLS_ID = 0

    def __init__(self, name, env):
        self.taskname = name
        self.env = env
        self.states = StatesContainer(self)
        self.events_map = {}

        self.id = BaseTask.CLS_ID
        BaseTask.CLS_ID += 1

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
        return 'Task id_{} {}'.format(self.id, self.taskname)

class BaselogicTask(BaseTask):
    """
    Concrete implementation of 'BaseTask'
    :param name : str | name of 'RequestGoods' instance
    :param env : 'simpy.Enviroment' cls | delegated from node environment
    """

    def __init__(self, name='Some buy task', env=None):
        super().__init__(name, env)
        self.states.set_init_state('null')
        self.fields = {}

    def add_fields(self, **kwargs):
        self.fields.update(kwargs)

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

# ######################################
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

        self.item_wallet = cWallet(self)
        self.register_wallet(self.item_wallet)
        self.money_wallet = cWallet(self)
        self.register_wallet(self.money_wallet)

        self.list_of_unknown_req = []



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

            if task.fields['role'] == 'delivery_goods':
                self.sent_log('[gen_run_incoming_tasks] handling DeliveryGoods')
                task.change_state('fulfilled') # fast solution
                self.item_wallet.add_items(task.fields['order']['good'], task.fields['order']['qtty'])

            elif task.fields['role'] == 'request_money':
                self.sent_log('[gen_run_incoming_tasks] handling RequestMoney')
                self.as_process(self.gen_sent_money(task))

            yield self.empty_event()

    # OUT LOGIC
    def sushi_buyer(self, timing):
        while True:
            yield self.timeout(timing)
            self.sent_log('new request for sushi', logging.DEBUG)
            # creating task
            sushi_request_task = RequestGoods('Sushi_request', self.simpy_env)
            sushi_request_task.add_fields(role='request_goods', order={'good': 'Sushi', 'qtty': 5},
                                          company_token=self.fields['company_token'])

            fulfilled_event = sushi_request_task.subscribe('fulfilled')

            self.send_msg(sushi_request_task, self.connected_nodes[0])
            for msg in self.messages:
                msg_to_send = cMessage(*msg)
                self.out_orders.port_to_place.put(msg_to_send)
            self.messages = []

    def gen_sent_money(self, requester_task):
        # take 'from warehouse/wallet
        self.sent_log('[gen_sent_money] taking money')
        wal_good = requester_task.fields['order']['good']
        wal_qtty = requester_task.fields['order']['qtty']

        yield self.as_process(self.money_wallet.gen_take_qtty(wal_good, wal_qtty))
        self.sent_log('[gen_sent_money] money are taken, sending')

        requester_task.change_state('fulfilled')

        delivery_task = DeliveryMoney('DeliveryMoney', self.simpy_env)
        # company_token is not employed anywhere further
        delivery_task.add_fields(role='delivery_money', order={'good': wal_good, 'qtty': wal_qtty},
                                 company_token=self.fields['company_token'])

        # delivery_task.setup(requester_task.good, requester_task.qtty)
        delivery_event = delivery_task.subscribe('fulfilled')
        msg_to_send = cMessage(delivery_task, self, [self.connected_nodes[0]])
        self.out_orders.port_to_place.put(msg_to_send)

    def func_add_company_token(self, some_task):
        # this function is added in a node way
        some_task.add_fields('company_token')

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

        self.item_wallet = cWallet(self)
        self.register_wallet(self.item_wallet)
        self.money_wallet = cWallet(self)
        self.register_wallet(self.money_wallet)

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

            if task.fields['role'] == 'request_goods':
                self.sent_log('[gen_run_incoming_tasks] handling RequestGoods')
                self.as_process(self.gen_deliver_good(task))

            elif task.fields['role'] == 'delivery_money':
                self.sent_log('[gen_run_incoming_tasks] handling DeliveryMoney')
                self.money_wallet.add_items(task.fields['order']['good'], task.fields['order']['qtty'])
            yield self.empty_event()

    def gen_deliver_good(self, requester_task):
        # take from warehouse/wallet
        self.sent_log('[gen_deliver_good] getting items from wallet')
        yield self.as_process(self.item_wallet.gen_take_qtty(requester_task.fields['order']['good'],
                                                             requester_task.fields['order']['qtty']))

        self.sent_log('[gen_deliver_good] items taken, delivering')

        requester_task.change_state('fulfilled')

        delivery_task = DeliveryGoods('DeliveryGoods', self.simpy_env)
        delivery_task.add_fields(role='delivery_goods', order={'good': requester_task.fields['order']['good'],
                                                         'qtty': requester_task.fields['order']['qtty']},
                                 buyer_company=requester_task.fields['company_token'],
                                 seller_company=self.fields['company_token'])

        delivery_event = delivery_task.subscribe('fulfilled')
        msg_to_send = cMessage(delivery_task, self, [self.connected_nodes[0]])
        self.out_orders.port_to_place.put(msg_to_send)

    def gen_replenish_inventory(self):
        pass

# Agreement (Blue Node)
class cAgreement(cNodeBase, cSimNode):

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

            if task.fields['role'] == 'request_goods':
                self.sent_log('[gen_run_incoming_tasks] handling RequestGoods')
                evdone = task.subscribe('fulfilled')
                msg_to_send = cMessage(task, self, [self.connected_nodes[0]])
                self.out_orders.port_to_place.put(msg_to_send)

            elif task.fields['role'] == 'delivery_goods':
                self.sent_log('[gen_run_incoming_tasks] handling DeliveryGoods')
                evdone = task.subscribe('fulfilled')
                money_sum = task.fields['order']['qtty'] * self.price_dict[task.fields['order']['good']]
                # money_sum = task.qtty * self.price_dict[task.good]
                self.as_process(self.gen_ask_money(evdone, money_sum), repr='ask_money')

                msg_to_send = cMessage(task, self, [self.connected_nodes[0]])
                self.out_orders.port_to_place.put(msg_to_send)

            elif task.fields['role'] == 'delivery_money':
                self.sent_log('[gen_run_incoming_tasks] handling DeliveryMoney')
                evdone = task.subscribe('fulfilled')
                msg_to_send = cMessage(task, self, [self.connected_nodes[0]])
                self.out_orders.port_to_place.put(msg_to_send)

            yield self.empty_event()

    def gen_ask_money(self, event_delivered, money_sum):
        self.sent_log('[gen_ask_money] waiting for item delivery')
        yield event_delivered
        self.sent_log('[gen_ask_money] item delivered, requesting money')
        rm_task = RequestMoney('RequestMoney', self.simpy_env)
        rm_task.add_fields(role='request_money', order={'good': 'USD', 'qtty': money_sum})

        # task.setup(good='USD', qtty=money_sum)
        msg_to_send = cMessage(rm_task, self, [self.connected_nodes[0]])
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


    def condition_extra(self, conds=None):
        # todo implement logic parsing from string
        self.pushing = True

        if conds:
            expression = namedtuple('expression', 'attr expr val')

            for node, express_list in conds.items():
                for express in express_list:
                    attr, expr, val = express.split(' ')
                    self.conditions_dict[expression(attr, expr, val)] = node
        else:
            raise AttributeError('No condition were set')


    def _action(self, task):
        got_match = False
        # TODO make attributes priority to solve multiple successful conditions
        # for attr_i in task.__dict__.keys():
        for attr_i in task.fields.keys():
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
                        if do_expression(task.fields[attr_i], expression.expr, expression.val):
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
            self.sent_log('handling new message: ' + str(msg))
            tsk = msg.uows
            success = self._action(tsk)
            if not success:
                self.sent_log('DID NOT MATCH')
                self.out_orders.wrong_jobs.put(msg)

            for msg in self.messages:
                self.sent_log('sending new message: ' + str(msg))
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

# Observers
class cPeriodicWalletObserver(simulengin.cAbstPeriodicObserver):
    def __init__(self, wallet, period=1):
        obs_name = "wallet" #compose from wallet
        super().__init__(obs_name, period)
        self.wallet = wallet

    def observe_data(self):
        for name_i, level_i in self.wallet.check_inventory():
            ts_name = name_i + ' @ ' + self.wallet.parent_node.name
            self.record_data(ts_name, level_i)

def create_wallet_observers(a_node):
    # Scans a node for wallets and creates observers for them
    obs = []
    for wal_i in a_node.wallets.values():
        obs += [cPeriodicWalletObserver(wal_i)]
    return obs


def test1():
    from model.model import cNodeFieldModel
    the_model = cNodeFieldModel()

    nodeShop = cShop('Shop')
    nodeShop.add_fields(company_token='Shop Inc.')
    nodeHub4Shop = cHubNode('Hub for shop')
    nodeShop.connect_node(nodeHub4Shop)

    nodeClient1 = cClient('Retail client 1')
    nodeClient1.add_fields(company_token='ClientABC')
    nodeAgreement1 = cAgreement('Retail agreement 1')
    nodeHub1 = cHubNode('Filter hub 1')
    nodeClient1.connect_node(nodeAgreement1)
    nodeAgreement1.connect_node(nodeHub1)
    nodeHub1.connect_nodes(inp_nodes=[nodeAgreement1], out_nodes=[nodeClient1, nodeShop])
    nodeHub1.condition_extra({nodeShop: ['role = request_goods', 'role = delivery_money'],
                             nodeClient1: ['role = delivery_goods', 'role = request_money']})

    nodeClient2 = cClient('Retail client 2')
    nodeClient2.add_fields(company_token='ClientXYZ')
    nodeAgreement2 = cAgreement('Retail agreement 2')
    nodeHub2 = cHubNode('Filter hub 2')
    nodeClient2.connect_node(nodeAgreement2)
    nodeAgreement2.connect_node(nodeHub2)
    nodeHub2.connect_nodes(inp_nodes=[nodeAgreement2], out_nodes=[nodeClient2, nodeShop])
    nodeHub2.condition_extra({nodeShop: ['role = request_goods', 'role = delivery_money'],
                             nodeClient2: ['role = delivery_goods', 'role = request_money']})

    nodeHub4Shop.connect_nodes(inp_nodes=[nodeShop], out_nodes=[nodeAgreement1, nodeAgreement2])
    nodeHub4Shop.condition_extra({nodeAgreement1: ['buyer_company = ClientABC'],
                                 nodeAgreement2: ['buyer_company = ClientXYZ']})


    # create and add observers
    obs = []
    obs += create_wallet_observers(nodeClient2)
    obs += create_wallet_observers(nodeClient1)
    obs += create_wallet_observers(nodeShop)
    for obs_i in obs:
        the_model.addObserver(obs_i)

    the_model.addNodes([nodeClient1, nodeAgreement1, nodeShop, nodeHub1])
    the_model.addNodes([nodeClient2, nodeAgreement2, nodeShop, nodeHub2])

    return the_model
