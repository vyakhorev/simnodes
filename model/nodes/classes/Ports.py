
import model.nodes.metatypes as metatypes
from model.nodes.classes.SimBase import cSimPort
import model.nodes.UoW as uows
import simpy


class cPortUoWQueue(cSimPort):
    """
        This class holds queue of UoW for a Node
    """
    # # FIXME This is never used, refactor types!
    # queue_in_neigh = metatypes.nQueue
    # queue_out_neigh = metatypes.nQueue
    # queue_in_node = metatypes.nQueue
    # queue_out_node = metatypes.nQueue
    # # FIXME ==================================  OKAY

    name = metatypes.String('cPortUoWQueue')

    def __init__(self, parent_node):
        # TODO #2: port_id should not be called here
        super().__init__(parent_node)

        print('inited port with id : {} for class : {}'.format(self.nodeid, parent_node))

        self.queue_in_neigh = metatypes.mtQueue()
        self.queue_out_neigh = metatypes.mtQueue()
        self.queue_in_node = metatypes.mtQueue()
        self.queue_out_node = metatypes.mtQueue()
        parent_node.register_port(self)
        self.debug = False

    ###############################################################

    def init_sim(self):
        super().init_sim()

    def my_generator(self):
        if not(self.is_connected() is None):
            self.simpy_env.process(self.gen_serve_sending())
            self.simpy_env.process(self.gen_serve_receiving())
            self.simpy_env.process(self.gen_serve_external_taking())
        if self.debug:
            self.simpy_env.process(self.gen_port_debugger())
        yield self.simpy_env.timeout(0)


    def put_uow(self, message): # node calls port to send this uow
        # CALL THIS FROM NODE, NOT FROM OTHER PORT

        msg = message
        # print('MSG :{}'.format(msg))
        self.sent_log('trying to send {}'.format(msg))
        self.queue_out_node.put(msg)
        self.sent_log("[put_uow] put "+str(msg) +" to queue_out_node")


    def put_uow_to(self, uow, port): # node calls port to send this uow
        # CALL THIS FROM NODE, NOT FROM OTHER PORT
        msg = (self, uow, port)
        self.sent_log('trying to send {}'.format(msg))
        self.queue_out_node.put(msg)
        # self.sent_log("[put_uow] put "+str(uow) +" to queue_out_node")


    def get_uow(self): # node wants to read incoming uow
        # CALL THIS FROM NODE, NOT FROM OTHER PORT
        ans = self.queue_in_node.get()
        self.sent_log("[get_uow] got "+str(ans)+" from queue_in_node")
        return ans


    def gen_serve_sending(self):
        # mark sendings for "available to be sent"
        while 1:
            # self.sent_log("[gen_serve_sending] listening to queue_out_node.. ")
            #yield self.simpy_env.timeout(5)
            msg = yield self.queue_out_node.get()
            # self.sent_log("[gen_serve_sending] got " + str(uow))
            self.queue_out_neigh.put(msg)
            self.sent_log("[gen_serve_sending] put " + str(msg) + " to queue_out_neigh ")


    def gen_serve_receiving(self):
        while 1:
            # self.sent_log("[gen_serve_receiving] listening to queue_in_neigh")
            # yield self.simpy_env.timeout(7)
            msg = yield self.queue_in_neigh.get()
            # self.sent_log("[gen_serve_receiving] got " + str(uow) + " from queue_in_neigh")
            self.queue_in_node.put(msg)
            self.sent_log("[gen_serve_receiving] put " + str(msg) + " to queue_in_node")

    def gen_serve_external_taking(self):
        while True:
            # Loop for all connected ports
            for port_id, neigh_i in self.connected_ports.items():

                # Loop for all queue_out_neigh items
                for i in range(len(neigh_i.queue_out_neigh.items)):

                    msg = yield neigh_i.queue_out_neigh.get()
                    if self.parent_node in msg.receivers:
                        self.queue_in_neigh.put(msg)
                        self.sent_log('[SUCCESS] got the {}'.format(msg))
                    else:
                        self.sent_log('[WARN] message {} forwarded to next agent'.format(msg))
                        neigh_i.queue_out_neigh.put(msg)
                    self.sent_log('gen_serve_external_taking got {} from  connected_to.queue_out_neigh'.format(msg))
                    
                #fixme Kinda strange unefficient workaround
                yield self.timeout(1)


            yield self.timeout(0)

    @property
    def queues(self):
        i = 0
        contains = "\nqueue_in_node: \n"
        for it_i in self.queue_in_node.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "queue_out_node: \n"
        for it_i in self.queue_out_node.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "queue_in_neigh: \n"
        for it_i in self.queue_in_neigh.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "queue_out_neigh: \n"
        for it_i in self.queue_out_neigh.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        return contains


    def gen_port_debugger(self):
        while 1:

            i = 0

            contains = "\nqueue_in_node: \n"
            for it_i in self.queue_in_node.items:
                i += 1
                contains += "\t" + str(i) + ":" + str(it_i) + "\n"

            contains += "queue_out_node: \n"
            for it_i in self.queue_out_node.items:
                i += 1
                contains += "\t" + str(i) + ":" + str(it_i) + "\n"

            contains += "queue_in_neigh: \n"
            for it_i in self.queue_in_neigh.items:
                i += 1
                contains += "\t" + str(i) + ":" + str(it_i) + "\n"

            contains += "queue_out_neigh: \n"
            for it_i in self.queue_out_neigh.items:
                i += 1
                contains += "\t" + str(i) + ":" + str(it_i) + "\n"
            if i > 0:
                self.sent_log(contains)
            yield self.simpy_env.timeout(1)
































