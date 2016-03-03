__author__ = 'User'
import model.nodes.metatypes as metatypes
# import model.nodes.classes.Ports as ports
import model.nodes.classes.Ports_v2 as ports
from model.nodes.classes.SimBase import cSimNode
from itertools import chain
import model.nodes.UoW as uows
from model.nodes.classes.Task import cTask, cDelivery
from model.nodes.classes.cMessage import cMessage


class cAgentNode(cSimNode):
    def __init__(self, name):
        super().__init__(name)
        self.in_orders = ports.cManytoOneQueue(self)
        self.out_orders = ports.cOnetoManyQueue(self)  # ??
        self.register_port(self.in_orders)
        self.register_port(self.out_orders)
        self.connected_buddies = []
        self.debug_on = True

        self.pushing = True
        self.messages = []

    def connect_buddies(self, buddies):
        self.connected_buddies += buddies
        for bud in self.connected_buddies:
            bud.connected_buddies += [self]
            # DO NOT CONNECT TO EACH OTHER this way
            # TODO make one-one port in agent and connect many-one to one-one
            self.in_orders.connect_to_port(bud.out_orders)
            self.out_orders.connect_to_port(bud.in_orders)

    def send_msg(self, task, receiver):
        msg = [task, self, [receiver]]
        self.messages.append(msg)
        if not self.pushing:
            self.pushing = True

    def init_sim(self):
        super().init_sim()

    def gen_send_spam(self):
        for i in range(5):
            for msg in self.messages:
                msg = cMessage(*msg)
                # print(msg)
                self.out_orders.port_to_place.put(msg)
            yield self.timeout(5)

    def gen_send_msg(self):
        self.as_process(self.gen_send_spam())
        yield self.timeout(0)

    def my_generator(self):
        print("I'm {} with connected buddies : {}".format(self.name, self.connected_buddies))

        if self.pushing:
            self.as_process(self.gen_send_msg())

        if self.debug_on:
            self.as_process(self.gen_debug())

        yield self.empty_event()

    def gen_debug(self):
        while True:
            for port in self.ports.values():
                self.sent_log(port.queues)

            # cTask.tm.status()
            yield self.timeout(2)
