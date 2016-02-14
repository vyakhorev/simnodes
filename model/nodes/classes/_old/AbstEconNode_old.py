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
        # property and obligations
        self.item_wallet = cWallet()
        self.commitment_wallet = []
        self.wrong_address_commitments = []
        self.worker_wallet = cWorkForceWallet()
        # daemons
        self.conveyors = []
        self.listeners = []
        # ports
        self.the_port = ports.cPortUoWQueue(self)
        self.register_port(self.the_port)
        # other nodes
        self.connected_nodes = []
        # some kind of interface to other nodes..
        self.commitment_types = []

    def connect_other_node(self, other_node):
        self.connected_nodes += [other_node]
        other_node.connected_nodes += [self]
        self.the_port.connect_to_port(other_node.the_port)

    def spawn_item(self, item_name, item_qtty):
        self.item_wallet.spawn_item(item_name, item_qtty)

    ################################################

    def init_sim(self):
        super().init_sim()
        for conv_i in self.conveyors:
            conv_i.s_set_devs(self.devs)
            conv_i.init_sim()
        for list_i in self.listeners:
            list_i.s_set_devs(self.devs)
            list_i.init_sim()
        self.commitment_wallet = simpy.FilterStore(self.devs.simpy_env)
        self.wrong_address_commitments = simpy.FilterStore(self.devs.simpy_env)

    def my_generator(self):
        for conv_i in self.conveyors:
            self.as_process(conv_i.my_generator())
        for list_i in self.listeners:
            self.as_process(list_i.my_generator())
        self.as_process(self.gen_sort_wrong_commitments())
        self.as_process(self.gen_recent_wrong_comm_queue())
        yield self.empty_event()

    def gen_sort_wrong_commitments(self):
        # get rid from all the commitments that this node is not able to fulfill.
        wr_address_filter = lambda f: not(f.expected_comm_type in self.commitment_types)
        while 1:
            wrong_commitment = yield self.commitment_wallet.get(wr_address_filter)
            self.sent_log("received a wrong commitment " + str(wrong_commitment))
            self.wrong_address_commitments.append(wrong_commitment)

    def gen_recent_wrong_comm_queue(self):
        # (re-)sent all the commitments that are typed like not(expected_comm_type in self.commitment_types)-wrong ones
        while 1:
            new_wrong_comm = yield self.wrong_address_commitments.get()
            if not(self.node_id in new_wrong_comm.visited_nodes):
                # may be it's better to register this thing when the commitment is created
                new_wrong_comm.add_visitor(self)
            else:
                # by def, else is not possible
                self.sent_log("Something impossible happend in [gen_recent_wrong_comm_queue]")
            self.the_port.put_uow_to_all(new_wrong_comm)

    def gen_receive_new_commitments(self):
        # scan incoming port queue for commitments
        while 1:
            # TODO: filter "already been here" commitments!
            new_commitment = yield self.the_port.get_uow()
            is_it_new = not(self.node_id in new_commitment.visited_nodes)
            if is_it_new:
                self.commitment_wallet.put(is_it_new)
                new_commitment.add_visitor(self)
            else:
                self.sent_log("already been here case")
                yield self.timeout(1) # filter would eliminate this timeout
            yield self.empty_event()

# Concrete nodes

class cNodeClientSupplyLine(cAbstEconNode):
    # Deals with all relationships regarding sales to a single customer

    def __init__(self, name):
        super().__init__(name)
        self.supply_lines = {}
        self.exchange_listener = cGoodsExchangeContractorListener()
        self.exchange_listener.set_commitment_wallet(self.commitment_wallet)
        self.commitment_types.append(self.exchange_listener.expected_comm_type)

    def add_supply_line(self, item, price, qtty, interval):
        # this one may be done as an explicit Conveyor creation
        new_supply_conveyor = cExchangeDealsConveyor(item, price, qtty, interval)
        new_supply_conveyor.set_output_wallet(self.commitment_wallet) #Put new deals here
        self.conveyors += [new_supply_conveyor]
        self.supply_lines[item] = new_supply_conveyor

class cNodeClient(cAbstEconNode):
    # imitates customer presence (someone that can receive goods and make a payment)
    def __init__(self, name):
        super().__init__(name)
        self.trade_listener = cTradeGoodContractorListener()
        self.trade_listener.set_commitment_wallet(self.commitment_wallet)
        self.commitment_types.append(self.trade_listener.expected_comm_type)

    def init_sim(self):
        super().init_sim()

class cNodeWarehouse(cAbstEconNode):
    # Owns and manages pile-type goods
    def __init__(self, name):
        super().__init__(name)
        self.shipments_listener = cShipmentContractorListener()
        self.shipments_listener.set_commitment_wallet(self.commitment_wallet)
        self.commitment_types.append(self.shipments_listener.expected_comm_type)

    def init_sim(self):
        super().init_sim()

class cNodeTreasury(cAbstEconNode):
    # Owns and manages money (pile-type)
    def __init__(self, name):
        super().__init__(name)
        self.payments_listener = cPaymentContractorListener()
        self.payments_listener.set_commitment_wallet(self.commitment_wallet)
        self.commitment_types.append(self.payments_listener.expected_comm_type)

    def init_sim(self):
        super().init_sim()

###############
# Conveyors are structure bricks for node's logic.
# They generate something with some frequency and
# have access to Node's wallets (set explicitly which
# wallet to use).
###############

class cSimpleConveyor(simulengin.cConnToDEVS):
    # something that takes from one wallet and puts to other wallet
    def __init__(self):
        super().__init__()
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

class cExchangeDealsConveyor(cSimpleConveyor):
    # Generates sales orders
    def __init__(self, item="", price=0, qtty=0, interval=1):
        super().__init__()
        self.item = item
        self.price = price
        self.qtty = qtty
        self.interval = interval

    def set_params(self, item, price, qtty, interval):
        self.item = item
        self.price = price
        self.qtty = qtty
        self.interval = interval

    #####################################################

    def my_generator(self):
        # Creates a new exchange deal with 1/self.interval frequency
        while 1:
            trade = cGoodsExchangeCommitment()
            trade.set_commitment_params(self.item, self.price, self.qtty, 3, 5)
            self.output_wallet.put(trade)
            yield self.timeout(self.interval)

###############
# Listeners are almost the same thing as conveyors except the
# starting mechanism - they listen to a queue and do something
# with that queue items.
###############

class cContractorListener(simulengin.cConnToDEVS):
    expected_comm_type = ""

    def __init__(self):
        super().__init__()
        # take from this wallet
        self.commitment_wallet = None
        # maybe put to this wallet
        self.output_wallet = None
        # maybe block resources from this wallet
        self.resource_wallet = None

    def set_commitment_wallet(self, wallet):
        self.commitment_wallet = wallet

    def set_output_wallet(self, wallet):
        self.output_wallet = wallet

    def set_resource_wallet(self, wallet):
        self.resource_wallet = wallet

    def my_generator(self):
        my_mark_filter = lambda f: f.expected_comm_type == self.expected_comm_type
        while 1:
            new_commitment = yield self.commitment_wallet.get(my_mark_filter)
            yield self.gen_do_commitment(new_commitment)

    def gen_do_commitment(self, new_commitment):
        raise NotImplementedError()

class cGoodsExchangeContractorListener(cContractorListener):
    expected_comm_type = "exchange"

    def __init__(self):
        super().__init__()

    def gen_do_commitment(self, new_commitment):
        # generate (unpack) 2 new commitments (? and send them?)
        self.sent_log("doing a commitment:" + str(new_commitment))
        for child_comm in new_commitment.child_commitments:
            self.commitment_wallet.put(child_comm)
        yield self.empty_event()

class cTradeGoodContractorListener(cContractorListener):
    # Do the thing when cTradeGoodsCommitment is received
    expected_comm_type = "trade"

    def __init__(self):
        # generate (unpack) 2 new commitments (? and send them?)
        super().__init__()

    def gen_do_commitment(self, new_commitment):
        self.sent_log("doing a commitment:" + str(new_commitment))

class cShipmentContractorListener(cContractorListener):
    # Do the thing when cShipmentCommitment is received
    expected_comm_type = "shipment"

    def __init__(self):
        super().__init__()

    def gen_do_commitment(self, new_commitment):
        # Send an item package to the other node
        # (or expect to receive one)
        self.sent_log("doing a commitment:" + str(new_commitment))

class cPaymentContractorListener(cContractorListener):
    # Do the thing when cPaymentCommitment is received
    expected_comm_type = "payment"

    def __init__(self):
        super().__init__()

    def gen_do_commitment(self, new_commitment):
        # Send an item (money) package to the other node
        # (or expect to receive one)
        self.sent_log("doing a commitment:" + str(new_commitment))


###############
# Commitments are a special kind of resources that help
# to govern async. run of different parties generators.
# IDEA: there always should be a balance inside one commitment
###############

class cCommitment(simulengin.cConnToDEVS):
    comm_type = "abstract"

    # side = ["take", "give", "neutral"]
    def __init__(self, parent=None, side="give"):
        super().__init__()
        self.actor = None
        # We should do a pretty complicated commitment structure (BPMN-like)
        self.child_commitments = [] #any commitment is a tree of elementary commitments
        self.parent_commitment = parent
        self.side = side
        # Exchange network settings
        self.visited_nodes = []

    def add_visitor(self, new_visitor):
        self.visited_nodes += [new_visitor.node_id]

    def switch_side_to_give(self):
        # Passive operation
        self.side = "give"

    def switch_side_to_take(self):
        # Active operation
        self.side = "take"

    def switch_side_to_neutral(self):
        # Active-passive operation
        self.side = "neutral"

    def set_actor(self, some_node):
        self.actor = some_node

    def set_commitment_params(self, *args, **kwargs):
        raise NotImplementedError()

class cGoodsExchangeCommitment(cCommitment):
    comm_type = "exchange"

    def __init__(self, parent=None):
        super().__init__(parent, "neutral")

    def set_commitment_params(self, good, price, qtty, payment_delay, shipment_delay):
        take_side = cTradeGoodsCommitment(self)
        take_side.set_commitment_params(good, price, qtty, payment_delay, shipment_delay)
        take_side.switch_side_to_take()
        take_side.s_set_devs(self.devs)
        give_side = cTradeGoodsCommitment(self)
        give_side.set_commitment_params(good, price, qtty, payment_delay, shipment_delay)
        give_side.switch_side_to_give()
        give_side.s_set_devs(self.devs)
        self.child_commitments += [take_side, give_side]

class cTradeGoodsCommitment(cCommitment):
    comm_type = "trade"

    def __init__(self, parent=None, side="give", good="", price=0, qtty=0, payment_delay=0, shipment_delay=0):
        super().__init__(parent, side)
        self.good = good
        self.price = price
        self.qtty = qtty
        self.payment_delay = payment_delay
        self.shipment_delay = shipment_delay

    def set_commitment_params(self, good, price, qtty, payment_delay, shipment_delay):
        # basic params (may be a way more complicated further)
        self.good = good
        self.price = price
        self.qtty = qtty
        self.payment_delay = payment_delay
        self.shipment_delay = shipment_delay
        # construct commitment tree (should be BPMN-like)
        the_shipment = cShipmentCommitment(self)
        the_shipment.set_commitment_params(self.good, self.qtty, self.shipment_delay)
        the_shipment.side = self.side
        the_shipment.s_set_devs(self.devs)
        the_payment = cPaymentCommitment(self)
        amount_to_pay = self.price * self.qtty
        the_payment.set_commitment_params(amount_to_pay, self.payment_delay)
        if self.side == "give":
            the_payment.switch_side_to_take()
        else:
            the_payment.switch_side_to_give()
        the_payment.s_set_devs(self.devs)
        self.child_commitments += [the_shipment, the_payment]

class cShipmentCommitment(cCommitment):
    comm_type = "shipment"

    def __init__(self, parent=None, side="give", good = "", qtty=0, shipment_delay=0):
        super().__init__(parent, side)
        self.side = side
        self.good = good
        self.qtty = qtty
        self.shipment_delay = shipment_delay

    def set_commitment_params(self, good, qtty, shipment_delay):
        self.good = good
        self.qtty = qtty
        self.shipment_delay = shipment_delay

class cPaymentCommitment(cCommitment):
    comm_type = "payment"

    def __init__(self, parent=None, side="give", money_amount=0, payment_delay=0):
        super().__init__(parent, side)
        self.side = side
        self.money_amount = money_amount
        self.payment_delay = payment_delay

    def set_commitment_params(self, money_amount, payment_delay):
        self.money_amount = money_amount
        self.payment_delay = payment_delay
        
