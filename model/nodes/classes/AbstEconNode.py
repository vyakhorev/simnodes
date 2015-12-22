__author__ = 'User'
import model.nodes.metatypes as metatypes
import model.nodes.classes.Ports as ports
from model.nodes.classes.SimBase import cSimNode
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
            # yield below?
            yield self.res_wallet.do_conversion('good',self.consumption_qtty,'energy', )


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
            self.res_wallet

    def gen_food_service_conv(self):
        # offer a deal for money -> food
        while 1:















# class cAbstEconNode(cSimNode):
#
#     def __init__(self, name):
#         super().__init__(name)
#         self.res_threads = {}
#         self.resources = []
#         self.request_resource_port = ports.cPortUoWQueue(self)
#         self.offer_resource_port = ports.cPortUoWQueue(self)
#         self.register_port(self.request_resource_port)
#         self.register_port(self.offer_resource_port)
#
#         self.resource_nodes = []
#
#     def add_resource(self, new_resource):
#         self.resources += [new_resource]
#
#     def connect_resource_nodes(self, buddies):
#         self.resource_nodes += buddies
#         for bud in buddies:
#             #bud.connected_buddies += [self]
#             self.request_resource_port.connect_to_port(bud.offer_resource_port)
#
#     #################################
#
#     def init_sim(self):
#         pass
#
#     def my_generator(self):
#         self.as_process(self.request_generator())
#         self.as_process(self.offer_generator())
#         yield self.empty_event()
#
#     def request_generator(self):
#         raise NotImplementedError()
#
#     def offer_generator(self):
#         raise NotImplementedError()
#
#     def request_res(self):
#         pass
#
#     def release_res(self):
#         pass
#
#
# class cWarehouse(cAbstEconNode):
#     def __init__(self, name):
#         super().__init__(name)
#
#     def request_generator(self):
#         msg = {'type':'gimme_men'}
#         self.request_resource_port.put_uow(msg)
#
#     def offer_generator(self):
#         yield self.empty_event()
#
#
# class cManNode(cAbstEconNode):
#     def __init__(self, name):
#         super().__init__(name)
#
#     def add_man(self):
#         self.resources += [eRes.resMan('Ivan')]
#
#     ###################
#
#     def init_sim(self):
#         super().init_sim()
#         men_count = 0
#         for res in self.resources:
#             if type(res) == eRes.resMan:
#                 men_count += 1
#         self.men = simpy.Resource(self.simpy_env, men_count)
#
#     def request_generator(self):
#         yield self.empty_event()
#
#     def offer_generator(self):
#         self.as_process(self.serve_offers())
#         yield self.empty_event()
#
#     def serve_offers(self):
#         while 1:
#             msg = yield self.offer_resource_port.get_uow()
#             if msg['type'] == 'gimme_men':
#                 yield self.give_man()
#
#     def give_man(self):
#         yield self.men.request()



