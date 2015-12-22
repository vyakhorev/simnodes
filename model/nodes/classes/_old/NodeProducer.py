
import model.nodes.metatypes as metatypes
from model.nodes.classes.SimBase import cSimNode
import model.nodes.classes.Ports as ports
import simpy
import model.nodes.UoW as uows

class cNodeProducer(cSimNode):
    """
        1. Takes UoW "produce something" from the input job port
        2. Takes produces it somehow out of thin air (wasting some money)
        3. Stores it and sends "take it" UoW to the output job port
    """
    name = metatypes.String('cNodeProducer')
    production_lead_time = metatypes.Float(None)
    chocopile = metatypes.nPile(None)
    # TODO: shipment_out_port = metatypes.Port()

    def __init__(self, name, production_lead_time):
        super().__init__(name)
        self.prod_lot = 100 #TODO
        self.production_lead_time = production_lead_time
        self.shipment_port = ports.cPortUoWQueue(self.node_id, self)
        self.register_port(self.shipment_port)
        self.pile_chocopile = metatypes.mtPile(0)

    #########################################################################

    def init_sim(self):
        super().init_sim()

    def my_generator(self):
        self.simpy_env.process(self.gen_production())
        self.simpy_env.process(self.gen_serve_shipments())
        yield self.simpy_env.timeout(0)

    def gen_production(self):
        # Produce a few chocolates
        while 1:
            yield self.simpy_env.timeout(2)
            self.pile_chocopile.put(self.prod_lot)
            self.sent_log('New chocolate produced')

    def gen_serve_shipments(self):
        while 1:
            yield self.simpy_env.timeout(2)
            self.sent_log('waiting for shipment')
            uow = yield self.shipment_port.get_uow()
            self.sent_log('received shipment request')
            yield self.pile_chocopile.get(uow.howmuch)
            uow_ans = uows.cSellGoodsUoW('smth', uow.howmuch)
            self.shipment_port.put_uow(uow_ans)

