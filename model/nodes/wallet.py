from model.nodes.metatypes import mtQueue, mtPile
import model.nodes.simulengin.simulengin as simulengin
import model.nodes.meta
import simpy
from collections import namedtuple


class cValuedResource(simulengin.cConnToDEVS):


    def __init__(self, name, value=0):
        super().__init__()
        self.name = name
        # self.value = value
        self.value = mtPile(level=value)

    # def __add__(self, other):
    #     return self.value + other.value
    #
    # def __sub__(self, other):
    #     return self.value - other.value

    def set_capacity(self, value):
        self.value.add(value)

    def init_sim(self):
        raise NotImplemented()

    def my_generator(self):
        raise NotImplemented()

    def __repr__(self):
        return str(self.name) + " : " + str(self.value)

class cItem(cValuedResource): #store
    pass

class cPile(cValuedResource): #container
    pass

class cWallet(simulengin.cConnToDEVS):
    # Todo: different types of resources

    def __init__(self):
        self.res_all = {}

    def spawn_item(self, name, qtty):
        self.res_all[name] = cItem(name, qtty)

    def spawn_pile(self, name, qtty):
        self.res_all[name] = cPile(name, qtty)

    def spawn_worker(self, name, qtty):
        self.res_all[name] = cWorker(name, qtty)

    # ?
    def check_existance(self, name):
        if name in self.res_all:
            return 1
        else:
            return 0

    def my_generator(self):
        self.as_process(self.gen_do_conversion('rubles', 40, 'dollars', 0.8))
        yield self.empty_event()

    def check_qtty(self, name):
        if not self.check_existance(name):
            return 0
        qtty = self.res_all[name].value
        return qtty

    def add_items(self, name, qtty):
        if not self.check_existance(name):
            yield self.spawn_item(name, 0)
        self.res_all[name].value.put(qtty)
        yield self.empty_event()

    def take_qtty(self, name, qtty):
        qtty_available = self.check_qtty(name)
        self.sent_log('qtty_available {}'.format(qtty_available))
        if qtty_available.level < qtty:
            # todo partly consume
            return 'not enough'
        yield self.res_all[name].value.get(qtty)

    # /?

    # *** INTERFACE

    def res_slice(self, res_type):
        return [(name, res) for (name, res) in self.res_all.items() if type(res) == res_type]

    # *** OPERATIONS
    # TODO: for multiple items to multiple items
    # TODO: yield "gen_do"
    # TODO: apply worker for conversion?

    def gen_do_exchange(self, resource_from, qtty_from, resource_to, qtty_to):

        # istaken = self.take_qtty(resource_from, qtty_from)
        istaken = self.as_process(self.take_qtty(resource_from, qtty_from))
        self.sent_log('Im here')
        if istaken:
            # type check? Which to spawn - item/pile/...?
            self.add_items(resource_to, qtty_to)
            yield self.empty_event()
        yield self.empty_event()

    def gen_do_conversion(self, resource_from, qtty_from, resource_to, qtty_to):
        yield self.timeout(40)
        self.as_process(self.gen_do_exchange(resource_from, qtty_from, resource_to, qtty_to))

    def gen_do_multiple_exchange(self):
        pass

    def gen_do_multiple_conversion(self):
        pass

    def __repr__(self):
        return str(self.res_all)

#####################################
class cWorker:
    pass

class cWorkForceWallet:
    pass

######################################

class cDeal:
    def __init__(self):
        self.activity_enabled = simpy.Resource(env)

    def release(self):
        pass
        # realease resource

class cDealWallet:
    def create_deal(self):
        # simpy resource that would be used in the Node

        pass
    #???

    # def do_instance_exchange(self, resource_in, resource_out):
    #     if self.check_existance(resource_in) or not(self.check_existance(resource_out)):
    #         return False
    #
    #     return True

if __name__ == '__main__':
    import datetime
    from model.model import cNodeFieldModel
    the_model = cNodeFieldModel()

    a = cWallet()
    a.spawn_item('rubles', 100)
    # b = cWallet()
    # b.spawn_item('dollars', 1.5)

    # print('a : {}, b : {}'.format(a, b))
    the_model.addOtherSimObj(a)
    # the_model.addOtherSimObj(b)
    loganddata, runner = the_model.run_sim(datetime.date(2015, 11, 15), until=100, seed=555)
    # a.gen_do_conversion('rubles', 40, 'dollar', 1)
    # print(a.res_slice(cItem))
    # print('a : {}, b : {}'.format(a, b))

