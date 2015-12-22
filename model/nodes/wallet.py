from model.nodes.metatypes import mtQueue, mtPile
import model.nodes.simulengin.simulengin as simulengin
import model.nodes.meta
import simpy
from collections import namedtuple

class cValuedResource(simulengin.cConnToDEVS):
    def __init__(self, name, value=0):
        super().__init__()
        self.name = name
        self.value = value

    def set_capacity(self, value):
        self.value = value

class cItem(cValuedResource): #store
    pass

class cPile(cValuedResource): #container
    pass

class cWallet:
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

    def check_qtty(self, name):
        if not self.check_existance(name):
            return 0
        qtty = self.res_all[name].value
        return qtty

    def add_items(self, name, qtty):
        if not self.check_existance(name):
            self.spawn_item(name, 0)
        self.res_all[name] += qtty
        return qtty

    def take_qtty(self, name, qtty):
        qtty_available = self.check_qtty(name)
        if qtty_available < qtty:
            return False
        self.res_all[name] -= qtty
        return True
    # /?

    #*** INTERFACE

    def res_slice(self, res_type):
        return [(name, res) for (name, res) in self.res_all.items() if type(res) == res_type]

    #*** OPERATIONS
    # TODO: for multiple items to multiple items
    # TODO: yield "gen_do"
    # TODO: apply worker for conversion?

    def gen_do_exchange(self, resource_from, qtty_from, resource_to, qtty_to):
        istaken = self.take_qtty(resource_from, qtty_from)
        if istaken:
            # type check? Which to spawn - item/pile/...?
            self.add_items(resource_to, qtty_to)
            return True
        return False

    def gen_do_conversion(self, resource_from, qtty_from, resource_to, qtty_to):
        return self.do_exchange(resource_from, qtty_from, resource_to, qtty_to)

    def gen_do_multiple_exchange(self):
        pass

    def gen_do_multiple_conversion(self):
        pass

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

