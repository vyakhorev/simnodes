__author__ = 'User'
import model.nodes.metatypes as metatypes
import model.nodes.classes.Ports as ports
from model.nodes.classes.SimBase import cSimNode
import model.nodes.simulengin.simulengin as simulengin
from model.nodes.wallet import cWallet
import simpy

class cAbstEconNode(cSimNode):
    def __init__(self, name):
        super().__init__(name)
        self.res_wallet = cWallet()
        self.the_port = ports.cPortUoWQueue(self)
        self.register_port(self.the_port)
        self.connected_nodes = []

    def connect_other_node(self, other_node):
        self.connected_nodes += [other_node]
        other_node.connected_nodes += [self]
        self.the_port.connect_to_port(self.the_port)

    def spawn_item(self, item_name, item_qtty):
        self.res_wallet.spawn_item(item_name, item_qtty)

    ################################################

    def init_sim(self):
        pass

    def my_generator(self):
        raise NotImplemented()

class cItemConsumer(cAbstEconNode):
    def __init__(self, name):
        super().__init__(name)
        self.item_to_consume = ""
        self.consumption_qtty = 0
        self.consumption_freq = 0

    def set_cons_conv(self, item, qtty, freq):
        self.item_to_consume = item
        self.consumption_qtty = qtty
        self.consumption_freq = freq

    def my_generator(self):

    def gen_cons_conv(self):
        while 1:
            yield self.timeout(self.consumption_freq)
            # yield from wallet !

class cItemGenerator(cAbstEconNode):
    def __init__(self, name):
        super().__init__(name)
        self.item_to_produce = ""
        self.production_qtty = 0
        self.production_freq = 0

    def set_prod_conv(self, item, qtty, freq):
        self.item_to_produce = item
        self.production_qtty = qtty
        self.production_freq = freq

    def my_generator(self):
        self.as_process(self.gen_prod_conv())
        self.as_process(self.gen_food_service_conv())

    def gen_prod_conv(self):
        while 1:
            yield self.timeout(self.production_freq)

    def gen_food_service_conv(self):
        # offer a deal for money -> food
        while 1:
            # yield from wallet !

# Conveyors are structure bricks for node's logic

class cConveyor(simulengin.cConnToDEVS):
    # something that takes from one wallet and puts to other wallet
    def __init__(self):
        self.source_wallet = None
        self.

class cDetermConsumptionConveyor(cConveyor):
    # Consumes an item from wallet every interval
    def __init__(self, item, volume, interval):
        super().__init__()
        self.item = item
        self.volume = volume
        self.interval = interval

    def set_source_wallet(self, wallet):
        self.source_wallet = wallet

    def set_surplus_wallet(self, wallet):
        self.surplus_wallet = wallet

    def init_sim(self):
        pass

    def my_generator(self):
        pass








