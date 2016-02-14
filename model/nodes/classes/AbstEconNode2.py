__author__ = 'Vyakhorev'
import model.nodes.metatypes as metatypes
import model.nodes.classes.Ports as ports
from model.nodes.classes.SimBase import cSimNode
import model.nodes.simulengin.simulengin as simulengin
from model.nodes.wallet import cWallet, cDealWallet, cWorkForceWallet
import model.nodes.requests as requests
import simpy


class cEconNode(cSimNode):
    def __init__(self, name):
        super().__init__(name)
        # property
        self.item_wallet = cWallet()
        self.worker_pool = [] # -> simpy.FilterStore
        self.resource_requests_queue = [] # -> simpy.FilterStore
        self.info_requests_queue = [] # -> simpy.FilterStore
        self.resource_requests_out_queue = [] # -> simpy.FilterStore
        self.info_requests_out_queue = [] # -> simpy.FilterStore
        # daemons
        self.daemons = []
        # ports
        self.resource_request_port = ports.cPortUoWQueue(self)
        self.register_port(self.resource_request_port)
        self.info_request_port = ports.cPortUoWQueue(self)
        self.register_port(self.info_request_port)
        # other nodes
        self.connected_nodes = []

    def register_daemon(self, new_daemon):
        self.daemons += [new_daemon]
    
    def connect_other_node(self, other_node):
        self.connected_nodes += [other_node]
        other_node.connected_nodes += [self]
        self.the_port.connect_to_port(other_node.the_port)

    def spawn_item(self, item_name, item_qtty):
        self.item_wallet.spawn_item(item_name, item_qtty)

    ################################################

    def init_sim(self):
        super().init_sim()
        for daem_i in self.daemons:
            daem_i.s_set_devs(self.devs)
            daem_i.init_sim()
        self.resource_requests_queue = simpy.FilterStore(self.devs.simpy_env)
        self.info_requests_queue = simpy.FilterStore(self.devs.simpy_env)
        self.resource_requests_out_queue = simpy.FilterStore(self.devs.simpy_env)
        self.info_requests_out_queue = simpy.FilterStore(self.devs.simpy_env)

    def my_generator(self):
        for daem_i in self.daemons:
            self.as_process(daem_i.my_generator())
        self.as_process(self.gen_receive_resource_requests())
        self.as_process(self.gen_receive_info_requests())         
        yield self.empty_event()

    def gen_receive_resource_requests(self):
        # scan incoming port queue for requests
        while 1:
            new_request = yield self.resource_request_port.get_uow()
            self.resource_requests_queue.put(new_request)
    
    def gen_receive_info_requests(self):
        # scan incoming port queue for requests
        while 1:
            new_request = yield self.info_request_port.get_uow()
            self.info_requests_queue.put(new_request)

    def gen_send_resource_requests(self):
        # sends a request to every connected node
        while 1:
            new_request = yield self.resource_requests_out_queue.get()
            # won't work without messages..
            self.resource_request_port.put_uow_to_all(new_request)
    
    def gen_send_info_requests(self):
        # sends a request to every connected node
        while 1:
            new_request = yield self.info_requests_out_queue.get()
            # won't work without messages..
            self.info_request_port.put_uow_to_all(new_request)
    
    
################
# Daemons
################

# Generators (do something out thin air)
        
class cAbstRequestGenerator(simulengin.cConnToDEVS):
    # Generate requests to a queue
    def __init__(self, output_queue = None):
        super().__init__()
        self.requests_queue = output_queue
        
    def set_output_queue(self, output_queue):
        self.requests_queue = output_queue
        
    def do_the_thing(self):
        yield self.empty_event()

class cAbstRegularRequestGenerator(cAbstRequestGenerator):
    # Generate requests to a queue periodically
    def __init__(self, interval=1):
        super().__init__()
        self.interval = interval
        self.running = True
    
    def set_interval(self, new_interval):
        self.interval = new_interval
    
    def my_generator(self):
        while True:
            if self.running:
                self.as_process(self.do_the_thing())
            yield self.timeout(self.interval)

class cItemRequestRegularGenerator(cAbstRegularRequestGenerator):
    # Periodically request an item
    def __init__(self, item, qtty, interval=1):
        super().__init__(interval)
        self.item = item
        self.qtty = qtty
    
    def do_the_thing(self):
        new_request = requests.cItemRequest(self.item, self.qtty, 0)
        self.requests_queue.put(new_request)
        yield self.empty_event()
        
    
# Listeners (wait for queue and process it)   

class cAbstRequestListener(simulengin.cConnToDEVS):
    # Do something with a new request
    # expected_req_classname - take only this requests (filtered queue)
    expected_req_classname = ""

    def __init__(self):
        super().__init__()
        # take from this filtered queue
        self.requests_queue = None

    def set_input_queue(self, input_queue):
        self.requests_queue = input_queue

    def my_generator(self):
        my_mark_filter = lambda f: f.__class__.__name__ == self.expected_req_classname
        while 1:
            new_request = yield self.commitment_wallet.get(my_mark_filter)
            if new_request.try_to_block():
                yield self.do_the_thing(new_request)

    def do_the_thing(self, new_request):
        raise NotImplementedError()        

class cItemRequestListener(cAbstRequestListener):
    # Handle item requests and ask dispenser daemon for items
    expected_req_classname = "cItemRequest"
    
    def __init__(self):
        super().__init__()
        self.item_dispenser = None
    
    def set_item_dispenser(self, an_item_dispenser):
        self.item_dispenser = an_item_dispenser
   
    def do_the_thing(self, new_request):
        
        yield self.item_dispenser.get_item(new_request.item, new_request.qtty)
        new_request.release_done() # or undone if we wish to
        # Convert request to uow here
        
class cItemDispenser(simulengin.cConnToDEVS):
    # Interface to wallet.
    # Production reqests may be handled same way..
    def __init__(self):
        super().__init__()
        self.item_wallet = None
        
    def set_wallet(self, node_item_wallet):
        self.item_wallet = node_item_wallet
        
    def get_item(self, item, qtty):
        yield self.item_wallet.gen_take_qtty(item, qtty)
        
class cItemSellContractCreator(simulengin.cConnToDEVS):
    # Handles sell requests for items. For each request
    # creates a new contract handler daemon.
    
    def __init__(self):
        super().__init__()
        self.price_terms = {}
        self.contracts_pool = None
        
    def set_price_terms(self, item, price, defferment):
        if not(item in self.price_terms):
            self.price_terms[item] = {}
        self.price_terms[item]["price"] = price
        self.price_terms[item]["defferment"] = defferment
    
    def set_contracts_pool(self, a_contracts_pool):
        # We should think of it as a link between
        # subnodes (daemons). A strong typed-one.
        self.contracts_pool = a_contracts_pool
    
    def compose_contract_daemon(self, item_request):
        terms = self.price_terms[item_request.item]
        new_contract = cItemSellContract(item_request, terms["price"], terms["defferment"])
        self.contracts_pool.add_contract(new_contract)
        
class cItemSellContract(simulengin.cConnToDEVS):
    # Handles a single contract with all
    # requests.
    
    def __init__(self, item_request, price, defferment):
        self.init_request = item_request
        self.terms = {} # Generalize this?..
        self.terms["item"] = item_request.item
        self.terms["buyer"] = item_request.requester_node
        self.terms["seller"] = item_request.provider_node
        self.terms["price"] = price
        self.terms["defferment"] = defferment
        
    def sell
        
        
class cContractsPool(simulengin.cConnToDEVS):
    # Stores all active contracts and handles
    # their collisions. So it's a daemon
    # that works as a container for other
    # daemons.
    def __init__(self):
        self.active_contracts = []
        
    def add_contract(self, new_contract):
        self.active_contracts += [new_contract]
   