import model.nodes.metatypes as metatypes
import model.nodes.classes.Ports as ports
from model.nodes.classes.SimBase import cSimNode
from itertools import chain
import model.nodes.UoW as uows
from model.nodes.classes.cMessage import cMessage
from functools import singledispatch, update_wrapper


# todo Move to some utils
def flatten_list(l):
    """
        This function produce [] from structure like [not_iterable, [ , ,]]
    """
    result = []
    if isinstance(l, (list, tuple)):
        for x in l:
            result.extend(flatten_list(x))
    else:
        result.append(l)
    return result


def methdispatch(func):
    """
        Single-dispatching in class methods based on functools.singledispatch
    """
    dispatcher = singledispatch(func)

    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)

    wrapper.register = dispatcher.register
    update_wrapper(wrapper, func)
    return wrapper


class cNodeEconAgent(cSimNode):
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

    # ================== Setup =======================

    def connect_buddies(self, buddies):
        self.connected_buddies += buddies
        for bud in buddies:
            bud.connected_buddies += [self]
            self.port_orders.connect_to_port(bud.port_orders)

    def send_msg(self):
        basic_uow = self.makeUow(self.msgtype)
        msg = [basic_uow, self, self.connected_buddies]
        self.messages.append(msg)
        if not self.pushing:
            self.pushing = True

    # Flexible Uow maker according to uow type
    @methdispatch
    def makeUow(self, uowtype):
        raise NotImplementedError("[ERROR] Unknown Uow Type")

    @makeUow.register(uows.cBuyGoodsUoW)
    def _(self, uowtype):
        print('cBuyGoodsUoW detected')
        return uows.cBuyGoodsUoW('buy cable', 33, 55)

    @makeUow.register(uows.cPaymentUoW)
    def _(self, uowtype):
        print('cPaymentUoW detected')
        return uows.cBuyGoodsUoW('pay for cable', 99, 111)

    @makeUow.register(uows.cShipmentUoW)
    def _(self, uowtype):
        print('cShipmentUoW detected')
        return uows.cBuyGoodsUoW('ship cable', 57, 100)

    def send_msg_to(self, receiver):
        print('set to send to described one ')
        basic_uow = uows.cBuyGoodsUoW('water', 11, 15)
        msg = [basic_uow, self, [receiver]]
        self.messages.append(msg)
        if not self.pushing:
            self.pushing = True
    # =================================================

    # ================ Sim methods ====================

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
            print("I AM HERE")
            self.as_process(self.gen_send_spam())

        yield self.empty_event()

    def gen_send_spam(self):
        for i in range(5):
            for msg in self.messages:
                msg = cMessage(*msg)
                self.port_orders.put_uow(msg)
            yield self.timeout(5)

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
            yield self.timeout(self.debug_delta)

    # =====================================================











