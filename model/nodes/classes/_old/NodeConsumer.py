from model.nodes.classes._old.NodeEconAgent import cNodeEconAgent


class cNodeConsumer(cNodeEconAgent):
    


# class cNodeConsumer(cSimNode):
#     """
#         1. Makes a UoW "require item" and puts in outgoing job port
#         2. Listens to ingoing ports and consumes everything, wasting money
#         3. In parallel, generates new money out of thin air
#     """
#     name = metatypes.String('cNodeConsumer')
#     hunger_level = metatypes.Float(None)
#     hunger_freq = metatypes.Float(None)
#     test_queue = metatypes.nQueue
#
#
#     def __init__(self, name, hunger_level, hunger_freq):
#         super().__init__(name)
#         self.hunger_level = hunger_level
#         self.hunger_freq = hunger_freq
#         self.consuming_port = ports.cPortUoWQueue(self.node_id, self)
#         self.register_port(self.consuming_port)
#
#         a_uow1 = uows.cBuyGoodsUoW(what='Something1', howmuch=125)
#         a_uow2 = uows.cBuyGoodsUoW(what='Something2', howmuch=125)
#         a_uow3 = uows.cBuyGoodsUoW(what='Something3', howmuch=125)
#         self.consuming_port.queue_out_node.add(a_uow1)
#         self.consuming_port.queue_out_node.add(a_uow2)
#         self.consuming_port.queue_out_node.add(a_uow3)
#
#         #self.test_queue = metatypes.mtQueue([1, 2, 4])
#
#     ############################################################
#
#     def init_sim(self):
#         super().init_sim()
#
#     def my_generator(self):
#         self.simpy_env.process(self.gen_hunger())
#         self.simpy_env.process(self.gen_consuming())
#         yield self.simpy_env.timeout(0)
#
#     def gen_hunger(self):
#         while 1:
#             self.sent_log('Hungry, want to buy a chocolate')
#             buy_uow = uows.cBuyGoodsUoW("chocolate", self.hunger_level)
#             self.consuming_port.put_uow(buy_uow)
#             yield self.simpy_env.timeout(self.hunger_freq)
#
#     def gen_consuming(self):
#         while 1:
#             uow = yield self.consuming_port.get_uow()
#             self.sent_log('Got a chocolate! ' + str(uow))
