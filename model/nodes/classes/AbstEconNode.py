__author__ = 'User'
import model.nodes.metatypes as metatypes
import model.nodes.classes.Ports as ports
from model.nodes.classes.SimBase import cSimNode
import model.nodes.simulengin.simulengin as simulengin
from model.nodes.wallet import cWallet, cDealWallet, cWorkForceWallet
import simpy


class cAbstEconNode(cSimNode):
    def __init__(self, name):
        super().__init__(name)
        self.item_wallet = cWallet()
        self.deal_wallet = cDealWallet()
        self.worker_wallet = cWorkForceWallet()
        self.the_port = ports.cPortUoWQueue(self)
        self.connected_nodes = []

        self.conveyors = []
        # registering
        self.register_port(self.the_port)

    def connect_other_node(self, other_node):
        self.connected_nodes += [other_node]
        other_node.connected_nodes += [self]
        self.the_port.connect_to_port(self.the_port)

    def spawn_item(self, item_name, item_qtty):
        self.item_wallet.spawn_item(item_name, item_qtty)

    ################################################

    def my_generator(self):
        for conv_i in self.conveyors:
            self.as_process(conv_i.my_generator())
        yield self.empty_event()


class cItemConsumer(cAbstEconNode):
    def __init__(self, name):
        super().__init__(name)
        self.cons_conveyor = cDetermConversionConveyor()
        self.conveyors += [self.cons_conveyor]

    def set_cons_conv(self, item_from, item_to, conversion_ratio, qtty, freq):
        self.cons_conveyor.set_params(item_from, item_to, conversion_ratio, qtty, freq)
        self.cons_conveyor.set_input_wallet(self.item_wallet)


class cItemGenerator(cAbstEconNode):
    def __init__(self, name):
        super().__init__(name)
        self.prod_conveyor = cDetermConversionConveyor()
        self.conveyors += [self.prod_conveyor]

    def set_prod_conv(self, item_from, item_to, conversion_ratio, qtty, freq):
        self.prod_conveyor.set_params(item_from, item_to, conversion_ratio, qtty, freq)
        self.prod_conveyor.set_input_wallet(self.item_wallet)

# Conveyors are structure bricks for node's logic

class cSimpleConveyor(simulengin.cConnToDEVS):
    # something that takes from one wallet and puts to other wallet
    def __init__(self):
        # take from this wallet
        self.input_wallet = None
        # put to this wallet
        self.output_wallet = None
        # block resources from this wallet
        self.resource_wallet = None

    def set_input_wallet(self, wallet):
        #todo: wallet type checking
        self.input_wallet = wallet

    def set_output_wallet(self, wallet):
        #todo: wallet type checking
        self.output_wallet = wallet

    def set_resource_wallet(self, wallet):
        #todo: wallet type checking
        self.resource_wallet = wallet


class cDetermConversionConveyor(cSimpleConveyor):
    # Consumes an item from wallet every interval
    def __init__(self, input_item="", output_item="", conversion_ratio=1, volume=0, interval=0):
        super().__init__()
        self.input_item = input_item
        self.output_item = output_item
        self.conversion_ratio = conversion_ratio
        self.volume = volume
        self.interval = interval

    def set_params(self, input_item, output_item, conversion_ratio, volume, interval):
        self.input_item = input_item
        self.output_item = output_item
        self.conversion_ratio = conversion_ratio
        self.volume = volume
        self.interval = interval

    def set_input_item(self, input_item):
        self.input_item = input_item

    def set_output_item(self, output_item):
        self.output_item = output_item

    def set_conversion_ratio(self, conversion_ratio):
        self.conversion_ratio = conversion_ratio

    def set_volume(self, volume):
        self.volume = volume

    def set_interval(self, interval):
        self.interval = interval

    #####################################################

    def my_generator(self):
        while 1:
            output_qtty = self.conversion_ratio * self.volume
            yield self.input_wallet.gen_do_conversion(self.input_item, self.volume, self.output_item, output_qtty)
            yield self.timeout(self.interval)