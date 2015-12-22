import model.nodes.metatypes as metatypes
from model.nodes.classes.NodeEconAgent import cNodeEconAgent
import model.nodes.classes.Ports as ports
import model.nodes.UoW as uows

# class cNodeCableSupplier(cNodeEconAgent):



# class cNodeCableSupplier(cSimNode):
#     money_pile = metatypes.nPile
#     name = metatypes.String('cNodeCableSupplier')
#
#     def __init__(self, name):
#         super().__init__(name)
#         self.money_pile = metatypes.mtPile()
#         self.clients = []
#         self.good_params = {}
#         self.pair_ports = {}
#         self.orders_count = 0
#
#     def add_money(self, money_amount):
#         self.money_pile.add(money_amount)
#
#     def set_good_params(self, good, lead_time, lead_cost, cost):
#         self.good_params[good] = {'lead_time': lead_time, 'lead_cost': lead_cost, 'cost': cost}
#
#     def connect_client(self, new_client):
#         self.clients += [new_client]
#
#         # make 2 ports
#         orders_port = ports.cPortUoWQueue(self)
#         shipments_port = ports.cPortUoWQueue(self)
#
#         self.pair_ports[new_client.node_id] = [orders_port, shipments_port]
#
#         self.register_port(orders_port) #todo automate
#         self.register_port(shipments_port) #todo automate
#
#         # connect 2 ports
#         orders_port.connect_to(new_client.orders_port)
#         shipments_port.connect_to(new_client.shipments_port)
# #
#     ###########################################
#
#     def init_sim(self):
#         super().init_sim()
#
#     def my_generator(self):
#         for port_orders, port_shipments in self.pair_ports.values():
#             self.as_process(self.gen_listen_to_orders(port_orders, port_shipments))
#             self.as_process(self.gen_receive_payments(port_shipments))
#         yield self.empty_event()
#
#     def gen_receive_payments(self, a_port):
#         while 1:
#             received_payment = yield a_port.get_uow()
#             self.sent_log("received " + str(received_payment))
#             yield self.money_pile.put(received_payment.howmuch)
#
#     def gen_listen_to_orders(self, order_port, shipment_port):
#         while 1:
#             new_order = yield order_port.get_uow()
#             self.orders_count += 1
#             self.sent_log("received " + str(new_order))
#             #sh_port = self.client_ports_shipments[shipment_port.parent_node.node_id]  #todo make this clean
#             self.as_process(self.gen_make_shipment_to_client(new_order, shipment_port))
#
    # def gen_make_shipment_to_client(self, an_order, sh_port):
    #     sh_uow = uows.cShipmentUoW(an_order.what, an_order.howmuch, an_order.price)
    #     # 1 Convert money to goods
    #     total_cost = self.good_params[sh_uow.what]['cost'] * sh_uow.howmuch
    #     # self.sent_log("goint to take money: " + str(total_cost)) #TODO format
    #     self.sent_log("goint to take money: {:,}".format(total_cost))
    #     yield self.money_pile.get(total_cost)
    #     self.sent_log("bought at supplier " + str(sh_uow.what))
    #     # 2 Goods are bought - now we have to deliver it
    #     delivery_time = self.good_params[sh_uow.what]['lead_time']
    #     delivery_cost_per_unit = self.good_params[sh_uow.what]['lead_cost']
    #     total_del_cost = delivery_cost_per_unit * sh_uow.howmuch
    #     self.sent_log("delivery of " + str(sh_uow.what) + " shall take " + str(delivery_time) + " days") #TODO format
    #     yield self.timeout(delivery_time)
    #     self.sent_log("delivered " + str(sh_uow.what))
    #     yield self.money_pile.get(total_del_cost)
    #     # 3 Send to the client
    #     sh_port.put_uow(sh_uow)
    #     self.sent_log("sent to client " + str(sh_uow))
    #     self.orders_count -= 1