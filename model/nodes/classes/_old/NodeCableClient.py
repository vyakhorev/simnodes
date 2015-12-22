import model.nodes.UoW as uows
from model.nodes.classes._old.NodeEconAgent import cNodeEconAgent


class cNodeCableClient(cNodeEconAgent):

    def __init__(self, name):
        super().__init__(name)

        # This helping to dispatch in parent class
        self.msgtype = uows.cBuyGoodsUoW(None, None, None)

        self.orders_delta = None
        # Checking neighbours ; sending orders according tp plan
        if (self.port_orders and self.orders_delta):
            # Port open for gen orders
            msg = self.next_order()

    def set_orders_plan(self, t):
        # Order every t time
        self.orders_delta = t

    # make this in EconAgent ???
    def next_order(self):
        basic_uow = uows.cShipmentUoW('cable', 57, 100)
        yield self.timeout(self.orders_delta)
        yield basic_uow



#     mat_flows = metatypes.List(None)
#     defferment_of_payment = metatypes.Float(None)
#     name = metatypes.String('cNodeCableClient')
#     # TODO Port
#
#     def __init__(self, name):
#         super().__init__(name)
#         self.orders_port = ports.cPortUoWQueue(self)
#         self.shipments_port = ports.cPortUoWQueue(self)
#         self.register_port(self.orders_port) #TODO automate
#         self.register_port(self.shipments_port)
#         self.mat_flows = []
#
#     def add_mat_flow(self, good, price, freq, freq_std, qtty, qtty_std, lastorderdate):
#         new_matfl = cMaterialFlow(good, price, freq, freq_std, qtty, qtty_std, lastorderdate)
#         self.mat_flows += [new_matfl]
#
#     #########################################################################
#
#     def init_sim(self):
#         super().init_sim()
#         for mf_i in self.mat_flows:
#             mf_i.lastorderdate = self.devs.convert_datetime_to_simtime(mf_i.lastorderdate)
#
#     def my_generator(self):
#         for mf_i in self.mat_flows:
#             self.as_process(self.gen_supply_line(mf_i))
#
#         self.as_process(self.gen_receive_shipments())
#         yield self.simpy_env.timeout(0)
#
#     def gen_supply_line(self, a_material_flow):
#         while 1:
#             for next_date, buy_uow in a_material_flow.iterate_over_orders(self.devs):
#                 self.sent_log('new order for ' + str(buy_uow))
#                 self.orders_port.put_uow(buy_uow)
#                 dt = max(next_date - self.devs.nowsimtime(), 1)
#                 yield self.simpy_env.timeout(dt)
#
#     def gen_receive_shipments(self):
#         while 1:
#             uow = yield self.shipments_port.get_uow()
#             self.as_process(self.gen_do_deal(uow))
#             self.sent_log('revecieved shipment ' + str(uow))
#
#     def gen_do_deal(self, ship_uow):
#         self.sent_log("received " + str(ship_uow))
#         yield self.timeout(self.defferment_of_payment)
#         pay_uow = uows.cPaymentUoW("EUR", ship_uow.get_value())
#         self.sent_log("sending " + str(pay_uow))
#         self.shipments_port.put_uow(pay_uow)
#
# class cMaterialFlow():
#     def __init__(self, good, price, freq, freq_std, qtty, qtty_std, lastorderdate):
#         self.good = good
#         self.price = price
#         self.freq = freq
#         self.freq_std = freq_std
#         self.qtty = qtty
#         self.qtty_std = qtty_std
#         self.lastorderdate = lastorderdate
#
#     def iterate_over_orders(self, devs):
#         # not simpy
#         while 1:
#             self.lastorderdate += abs(devs.random_generator.normalvariate(self.freq, self.freq_std))
#             new_qtty = abs(devs.random_generator.normalvariate(self.qtty, self.qtty_std))
#             yield [self.lastorderdate, uows.cBuyGoodsUoW(self.good, new_qtty, self.price)]