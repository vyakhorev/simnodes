# -*- coding: utf-8 -*-
__author__ = 'User'
import model.nodes.metatypes as metatypes
from model.nodes.classes.SimBase import cSimPort
from model.nodes.classes.cMessage import cMessage

from model.nodes.classes.SimBase import cSimNode
import simpy

class cManytoOneQueue(cSimPort):
    """
    Many-to-one

    This port consist of bunch of queues:
        :attr queues_inputs: dict| dynamic dictionary which reflecting number of connected outside ports
        :attr queue_fetch_incomes: mtQueue| Queue which holding all receiving messages from
                                    outside nodes
        :attr queue_local_jobs: mtQueue| collection of all messages referred to parent Node
        :attr wrong_jobs: mtQueue| collection of all messages with bad receiver address

        :scheme:
                              (node_1)  (node_2) ...(node_n)
                                 |          |         |
        queues_inputs       {[mtQueue_1]  [mtQueue_2] [mtQueue_n] }
                                 |          |         |
                                 ----------------------
                                            |
        queue_fetch_incomes              [mtQueue]
                                           |  |
        queue_local_jobs       [mtQueue]<--   |
        wrong_jobs                             --> [mtQueue]

    """

    def __init__(self, parent_node=None):
        """
        Setup queues
        :arg parent_node: cNode| which node created this port
        """
        super().__init__(parent_node)
        self.queues_inputs = {}
        self.queue_fetch_incomes = metatypes.mtQueue(self)
        self._queue_output = metatypes.mtQueue(self)
        self.queue_local_jobs = metatypes.mtQueue(self)
        self.wrong_jobs = metatypes.mtQueue(self)


    def make_input_queue(self, who):
        """
        Creating new queue for each connected one
        """
        self.queues_inputs[who] = metatypes.mtQueue(self).give_sim_analog(self.simpy_env)
        self.as_process(self.gen_simple_waiter(self.queues_inputs[who]))
        return True

    @property
    def port_to_listen(self):
        """
        Universal attribute
        """
        # self.sent_log('Providing port {}'.format(self._queue_output))
        return self._queue_output

    def get_fetch_queue(self, who_calls):
        """
        :return mtQueue: queue belongs to `who_calls` - cOnetoManyQueue instance
        """
        if who_calls is self.queues_inputs:
            return self.queues_inputs[who_calls]
        else:
            self.make_input_queue(who_calls)
            return self.queues_inputs[who_calls]

    def init_sim(self):
        super().init_sim()

    def my_generator(self):
        self.sent_log('CONNECTED ? {}'.format(self.is_connected()))
        # if self.is_connected():
        self.as_process(self.fetch_all_queues())

        yield self.timeout(0)

    def gen_simple_waiter(self, queue):
        """
        listen every input queue
        """
        while True:
            msg = yield queue.get()
            self.sent_log('im got msg {}'.format(msg))
            self.sent_log(str(msg))
            self.queue_fetch_incomes.put(msg)
            yield self.timeout(0)

    def fetch_all_queues(self):
        """
        listening for self.queue_fetch_incomes queue and decide which message has wrong or correct address
        """
        # todo maybe dont work
        for nodeport_i, queue_i in self.queues_inputs.items():
            self.sent_log('SPAWNED listener  for {}'.format(queue_i))
            self.as_process(self.gen_simple_waiter(queue_i))
        # for port_id, neigh_i in self.connected_ports.items():
        #     self.sent_log('neigh {} <=> port {}'.format(neigh_i, port_id))
        #     self.as_process(self.gen_simple_waiter(neigh_i))

        while True:
            msg = yield self.queue_fetch_incomes.get()
            if self.parent_node in msg.receivers:
                self.queue_local_jobs.put(msg)
                # self._queue_output.put(msg)
                self.sent_log('[SUCCESS] got the {}'.format(msg))
            else:
                self.sent_log('[WARN] message {} have bad address'.format(msg))
                self.wrong_jobs.put(msg)
        yield self.timeout(0)

    @property
    def queues(self):
        i = 0
        contains = "\nqueue_fetch_incomes: \n"
        for it_i in self.queue_fetch_incomes.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "_queue_output: \n"
        for it_i in self._queue_output.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "queue_local_jobs: \n"
        for it_i in self.queue_local_jobs.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "wrong_jobs: \n"
        for it_i in self.wrong_jobs.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        for queue in self.queues_inputs.values():
            contains += "{}: \n".format(queue)
            for it_i in queue.items:
                i += 1
                contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        return contains

# Todo rename to not-queue
class cOnetoManyQueue(cSimPort):
    """
    One-to-many
    :attr port_to_place: mtQueue| place where node leave their own messages through 'cMessage' class
    :attr wrong_jobs: mtQueue| if node do not connected to destination node messages automatically placing here

    """
    def __init__(self, parent_node=None):
        """
        Setup queues
        """
        super().__init__(parent_node)
        # self.queues_inputs = []
        self._queue_nonsorted_jobs = metatypes.mtQueue(self)

        self._queue_output = metatypes.mtQueue(self)
        self.wrong_jobs = metatypes.mtQueue(self)

    def init_sim(self):
        super().init_sim()

    def my_generator(self):
        self.sent_log('CONNECTED ? {}'.format(self.is_connected()))
        # if self.is_connected():
        self.as_process(self.gen_sort_jobs(), repr='Sorting_Generator{} '.format(self.nodeid))

        yield self.timeout(0)

    @property
    def port_to_place(self):
        return self._queue_nonsorted_jobs

    @property
    def port_to_listen(self):
        """
        Universal attribute
        """
        # self.sent_log('Providing port {}'.format(self._queue_output))
        return self._queue_output

    def gen_sort_jobs(self):

        while True:
            msg = yield self._queue_nonsorted_jobs.get()
            self.sent_log('im got {}'.format(msg))
            print('self.connected_ports', self.connected_ports)
            if msg.receivers[0] in [neigh_i.parent_node for neigh_i in self.connected_ports.values()]:
                for port_id, neigh_i in self.connected_ports.items():
                    if neigh_i.parent_node in msg.receivers:
                        self.sent_log('msg.receivers : {}, neigh_i.parent_node : {}'.format(msg.receivers,
                                                                                            neigh_i.parent_node))
                        queue = neigh_i.get_fetch_queue(self)
                        queue.put(msg)
                        # print('queue', queue.items)
            else:
                self.sent_log('WRONG TASK : {}'.format(msg))
                task = msg.uows
                task.set_task_to_wrong()
                self.wrong_jobs.put(msg)

                # else:
                #     self.sent_log('WRONG TASK : {}'.format(msg))
                #     task = msg.uows
                #     task.set_task_to_wrong()
                #     self.wrong_jobs.put(msg)
            yield self.empty_event()

    @property
    def queues(self):
        i = 0
        contains = "\n_queue_nonsorted_jobs: \n"
        for it_i in self._queue_nonsorted_jobs.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "_queue_output: \n"
        for it_i in self._queue_output.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "wrong_jobs: \n"
        for it_i in self.wrong_jobs.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        return contains


# TODO if no receivers, handle an error
class cOnetoOneInpQueue(cSimPort):
    def __init__(self, parent_node=None):
        super().__init__(parent_node)

        # self.queues_inputs = []
        self.queue_fetch_incomes = metatypes.mtQueue(self)
        self._queue_output = metatypes.mtQueue(self)

        self.queue_local_jobs = metatypes.mtQueue(self)
        self.wrong_jobs = metatypes.mtQueue(self)

    def init_sim(self):
        super().init_sim()

    def my_generator(self):
        self.sent_log('CONNECTED ? {}'.format(self.is_connected()))
        # if self.is_connected():
        self.as_process(self.gen_listen_input())
        yield self.timeout(0)

    def get_fetch_queue(self, who_calls):
        # for k, v in self.parent_node.__dict__.items():
        #     print(k, ' : ', v)
        print('=========================')
        print(who_calls.parent_node.out_orders)
        print(who_calls.parent_node.in_orders)
        print('=========================')
        self.sent_log('{} calls for my {} queue'.format(who_calls, self))
        return self.queue_fetch_incomes

    @property
    def port_to_place(self):
        return self.queue_fetch_incomes

    @property
    def port_to_listen(self):
        return self._queue_output

    def gen_listen_input(self):
        while True:
            msg = yield self.queue_fetch_incomes.get()
            if self.parent_node in msg.receivers:
                self.queue_local_jobs.put(msg)
                self.sent_log('[SUCCESS] got the {}'.format(msg))
            else:
                self.sent_log('[WARN] message {} have bad address'.format(msg))
                self.wrong_jobs.put(msg)

        yield self.timeout(0)

    @property
    def queues(self):
        i = 0
        contains = "\nqueue_fetch_incomes: \n"
        for it_i in self.queue_fetch_incomes.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "_queue_output: \n"
        for it_i in self._queue_output.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "queue_local_jobs: \n"
        for it_i in self.queue_local_jobs.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "wrong_jobs: \n"
        for it_i in self.wrong_jobs.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        return contains


class cOnetoOneOutQueue(cSimPort):
    def __init__(self, parent_node=None):
        super().__init__(parent_node)

        # self.queues_inputs = []
        self.queue_fetch_incomes = metatypes.mtQueue(self)
        self._queue_output = metatypes.mtQueue(self)

        self.queue_local_jobs = metatypes.mtQueue(self)
        self.wrong_jobs = metatypes.mtQueue(self)

        # self.pinned_queue = None

    def init_sim(self):
        super().init_sim()

    def my_generator(self):
        self.sent_log('CONNECTED ? {}'.format(self.is_connected()))
        # if self.is_connected():
        self.as_process(self.gen_push_job())
        yield self.timeout(0)

    @property
    def port_to_place(self):
        return self._queue_output

    def connect_to_port(self, another_port):
        if another_port.port_id in self.connected_ports:
            print('Failed to connect !! ')
            return

        elif len(self.connected_ports) > 0:
            raise AttributeError('{} Coudnt connect to many ports'.format(self))

        print('connecting {} with {} port_id to {} with {} port_id '.format(self, self.port_id, another_port,
                                                                            another_port.port_id))

        self.connected_ports[another_port.port_id] = another_port
        another_port.connected_ports[self.port_id] = self

        print(self.connected_ports)
        return True

    def gen_push_job(self):
        while True:
            msg = yield self.port_to_place.get()
            # FIXME causes error if no output nodes
            print('self.connected_ports.values()', self.connected_ports.values())

            print('%%%%ALOAHAHAJHFBHFBLBFAEFAF',self.parent_node, list(self.connected_ports.values()) )
            neigh = list(self.connected_ports.values())[0]
            queue = neigh.get_fetch_queue(self)
            queue.put(msg)

        yield self.empty_event()

    @property
    def queues(self):
        i = 0
        contains = "\nqueue_fetch_incomes: \n"
        for it_i in self.queue_fetch_incomes.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "_queue_output: \n"
        for it_i in self._queue_output.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "queue_local_jobs: \n"
        for it_i in self.queue_local_jobs.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        contains += "wrong_jobs: \n"
        for it_i in self.wrong_jobs.items:
            i += 1
            contains += "\t" + str(i) + ":" + str(it_i) + "\n"

        return contains