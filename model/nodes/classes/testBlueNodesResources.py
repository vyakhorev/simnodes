
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
# Tasks help to provide events. That'a
# the most important idea behind them
# (at least at the moment).
########################################

# TODO: STATES should not be shared!!!
# I think that states container should be a part of
# task's logic - at least STATES and transition rules
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

# TODO: link to the environment should be shared among all the instances
class BaselogicTask(BaseTask):
    """
    Concrete implementation of 'BaseTask'
    :param name : str | name of 'RequestGoods' instance
    :param env : 'simpy.Enviroment' cls | delegated from node environment
    """

    def __init__(self, name='', env=None):
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

# an example how to create new task types
class SimpleStatesTask(BaselogicTask):
    pass

########################################
# New special "tasks" for resource
# requests. Will have to implement
# something like this for tasks..
########################################

# have to inherit this one to change states
class StatesContainerResourcePullRequest(StatesContainer):
    """
    created - just created and not yet sent
    requested - sent by port
    received - some process got the request and is going to work with it
    deny - refused by receiver
    cancel - cancelled by sender
    supplied - fully supplied
    The transition system should forbid to go "deny" after
    "cancel" or "supplied" or the other way. This would help
    to prevent async. errors. We should do this ASAP.
    """
    STATES = ['created', 'requested', 'received', 'deny', 'cancel', 'supplied']

class cResourceIDInterface():
    # TODO: "root" task base class
    pass

class cResourcePullRequest(BaselogicTask, cResourceIDInterface):
    """
    pull request to the provider port
    is a task itself (and may contain
    another task inside).
    """
    def __init__(self, name='', env=None):
        super().__init__(name, env)
        # FIXME: this is not right to destroy one state machine to create another
        self.states = None
        self.states = StatesContainerPullRequest(self)

######################################
# Some nice classes for information
# exchange.
######################################

# A package that represents resources in the system
# This a payload for a resource task
class cResourcePackage():
    pass

######################################
# Refined port mechanics
######################################

###
# Pull-port relationships
###

# Provides resources to the connected cResAvtivePuller
class cResPassiveProviderPort(ports.cManytoOneQueue):
    """
    Listens to incoming pull requests from cResAvtivePuller
    (can be connected only to this class of ports).
    When the pull request comes, checks (if nessecary)
    for correlation id compliance and if it's ok,
    triggers the state "fulfilled" in the pull request.
    """
    pass

# Pulls resources from cResPassiveProviderPort
class cResAvtivePullerPort(ports.cOnetoOneOutQueue):
    def __init__(self, parent_node=None):
        super().__init__(parent_node)

###
# Push-port relationships
###

# Passively receives new tasks
class cTaskPassiveReceiverPort(ports.cManytoOneQueue):
    def __init__(self, parent_node=None):
        super().__init__(parent_node)

# Actively sends new tasks
class cTaskActivePusherPort(ports.cOnetoOneOutQueue):
    def __init__(self, parent_node=None):
        super().__init__(parent_node)



# ######################################
# Nodes
# ######################################

# Base class for active nodes
class cBlueNode(cNodeBase, cSimNode):
    pass

# An example of a resource provider
class cNodeDoer(cBlueNode):
    def __init__(self):
        self._res_passive_provide_port = cResPassiveProviderPort(self)
        self._task_passive_receive_port = cTaskPassiveReceiverPort(self)

    def my_generator(self):
        # gen_do_a_task for each new task
        pass

    def gen_do_a_task(self):
        # get new task from _task_passive_receive_port and
        # put a resource to _res_passive_provide_port
        pass

# An example of a resource puller
class cNodeOrderer(cBlueNode):
    def __init__(self):
        self._res_active_pull_port = cResAvtivePullerPort(self)
        self._task_active_push_port = cTaskActivePusherPort(self)

    def my_generator(self):
        # order_new_task with a timeout
        pass

    def order_new_task(self):
        # old-scheme push a task via _task_active_push_port
        pass


# Good old Hub (maybe we have to add something here)
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

