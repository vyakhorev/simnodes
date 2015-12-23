from model.nodes.metatypes import mtQueue, mtPile
import model.nodes.simulengin.simulengin as simulengin
import model.nodes.meta
import simpy
from collections import namedtuple


class cValuedResource(simulengin.cConnToDEVS):

    def __init__(self, name):
        super().__init__()
        self.name = name

    def my_generator(self):
        yield self.empty_event()

    def __repr__(self):
        return str(self.name)


class cItem(cValuedResource):
    def __init__(self, name, count=0):
        super().__init__(name)
        self.count = ['name' for i in range(count)]

        if self.is_simulation_running:
            self.count = simpy.Store(self.simpy_env)
        else:
            self.count = mtQueue(*self.count)

    def __repr__(self):
        return str(self.name) + " : " + str(self.count.items)


class cPile(cValuedResource):
    def __init__(self, name, value=0):
        super().__init__(name)

        if self.is_simulation_running:
            self.value = simpy.Container(self.simpy_env)
        else:
            self.value = mtPile(level=value)

    def __repr__(self):
        return str(self.name) + " : " + str(self.value.level)


class cWallet(simulengin.cConnToDEVS):
    # Todo: different types of resources

    def __init__(self):
        super().__init__()
        self.res_all = {}
        self.refused_queue = mtQueue()
        self.my_pile = mtPile(level=100)

    def spawn_item(self, name, qtty):
        # Todo: depending on the state (simulated or not) create mtPile or Container
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

    def init_sim(self):
        super().init_sim()
        for key_i, res_i in self.res_all.items():
            res_i.s_set_devs(self.devs)
            res_i.init_sim()

    def my_generator(self):
        # Refused event
        self.refused = self.devs.simpy_env.event()

        yield self.empty_event()

    def check_qtty(self, name):
        if not self.check_existance(name):
            return 0
        qtty = self.res_all[name].value
        return qtty

    def gen_add_items(self, name, qtty):
        if not self.check_existance(name):
            self.spawn_item(name, 0)
            # This was a workaround before self.is_simulation_running
            self.res_all[name].s_set_devs(self.devs)
        if type(self.res_all[name]) == cPile:
            self.res_all[name].level.put(qtty)
        if type(self.res_all[name]) == cItem:
            for i in range(qtty):
                self.res_all[name].count.put('name')
        yield self.empty_event()

    def gen_take_qtty(self, name, qtty):
        # if name not in self.res_all:
        #     self.sent_log('{} has not {} key'.format(type(self), name))
        #     return False

        if type(self.res_all[name]) == cPile:
            print('value {} '.format(self.res_all[name].value.level))

            if self.res_all[name].value.level < qtty:
                self.sent_log("not enough value level ")
                # Alternative path?
            yield self.res_all[name].value.get(qtty)

        elif type(self.res_all[name]) == cItem:
            print('count {} '.format(self.res_all[name]))
            if len(self.res_all[name].count.items()) <= 0:
                self.sent_log("not enough items")
            yield self.res_all[name].value.get(qtty)

        yield self.empty_event()
    def gen_take_qtty2(self, name, qtty):
        # if name not in self.res_all:
        #     self.sent_log('{} has not {} key'.format(type(self), name))
        #     return False

        if type(self.res_all[name]) == cPile:
            print('value {} '.format(self.res_all[name].value.level))
            if self.res_all[name].value.level < qtty:
                self.refused.succeed()

            res_event = yield self.res_all[name].value.get(qtty) | self.refused
            print('res_event {}'.format(res_event))

            if self.res_all[name].value.get(qtty) in res_event:
                self.sent_log('managed to take')
                return self.res_all[name].value.get(qtty)

            elif self.refused in res_event:
                self.sent_log('refused event')
                self.refused_queue.put('cant take {} from {}'.format(qtty, self.res_all[name].value.level))
                self.refused = self.simpy_env.event()

            else:
                self.sent_log('smth wrong')
        #
        #     if self.res_all[name].value.level < qtty:
        #         self.sent_log("not enough value level ")
        #         # Alternative path?
        #     yield self.res_all[name].value.get(qtty)
        #
        # elif type(self.res_all[name]) == cItem:
        #     print('count {} '.format(self.res_all[name]))
        #     if len(self.res_all[name].count.items()) <= 0:
        #         self.sent_log("not enough items")
        #     yield self.res_all[name].value.get(qtty)

        yield self.empty_event()


    # *** INTERFACE

    def res_slice(self, res_type):
        return [(name, res) for (name, res) in self.res_all.items() if type(res) == res_type]

    # *** OPERATIONS
    # TODO: for multiple items to multiple items
    # TODO: yield "gen_do"
    # TODO: apply worker for conversion?
    # TODO: rejected logic

    def gen_wallet_take(self, resource, qtty):
        yield self.simpy_env.process(self.gen_take_qtty(resource, qtty))
        self.sent_log('item taken !')

    def gen_wallet_add(self, resource, qtty):
        yield self.simpy_env.process(self.gen_add_items(resource, qtty))
        self.sent_log('item added !')

    # more logic, filling refusals queue
    def gen_wallet_take_with_ev(self, resource, qtty):
        yield self.simpy_env.process(self.gen_take_qtty2(resource, qtty))
        self.sent_log('item may be taken !')

    # def gen_do_exchange(self, resource_from, qtty_from, resource_to, qtty_to):
    #     yield self.take_qtty(resource_from, qtty_from)
    #     self.sent_log('item taken!')
    #     self.as_process(self.add_items(resource_to, qtty_to))
    #     self.sent_log('item added!')
    #     yield self.empty_event()
    #
    # def gen_do_conversion(self, resource_from, qtty_from, resource_to, qtty_to):
    #     yield self.timeout(40)
    #     self.as_process(self.gen_do_exchange(resource_from, qtty_from, resource_to, qtty_to))
    #
    # def gen_do_multiple_exchange(self):
    #     pass
    #
    # def gen_do_multiple_conversion(self):
    #     pass

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
        pass

    def release(self):
        pass
        # realease resource

class cDealWallet:
    def create_deal(self):
        # simpy resource that would be used in the Node
        pass


class nodochka(simulengin.cConnToDEVS):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def my_generator(self):
        self.as_process(self.gen_debug())
        self.as_process(self.some_gen('Take', self.a, 'rubles', 40, 80))
        self.as_process(self.some_gen('Take', self.a, 'rubles', 80, 80))
        self.as_process(self.some_gen('Add', self.b, 'gold ingots', 40, 7))
        self.as_process(self.refusals_listen(self.a))
        self.as_process(self.refusals_listen(self.b))
        yield self.empty_event()

    def refusals_listen(self, who):
        msg = yield who.refused_queue.get()
        self.sent_log('some catched {}'.format(msg))

    def gen_debug(self):
        while True:
            print(self.a)
            print(self.b)
            yield self.timeout(2)

    def some_gen(self, operation, patient, resource, when, qtty):
        yield self.simpy_env.timeout(when)
        if operation == 'Take':
            self.as_process(patient.gen_wallet_take_with_ev(resource, qtty))
            print('taker')
            yield self.simpy_env.timeout(1)
        elif operation == 'Add':
            print('adder')
            self.as_process(patient.gen_wallet_add(resource, qtty))
            yield self.simpy_env.timeout(1)
        else:
            print('none operation')
            yield self.simpy_env.timeout(1)


if __name__ == '__main__':
    import datetime
    from model.model import cNodeFieldModel
    the_model = cNodeFieldModel()

    a = cWallet()
    a.spawn_pile('rubles', 100)
    b = cWallet()
    b.spawn_item('gold ingots', 4)

    nod1 = nodochka(a, b)

    # print('a : {}, b : {}'.format(a, b))
    the_model.addOtherSimObj(a)
    the_model.addOtherSimObj(b)
    the_model.addOtherSimObj(nod1)

    loganddata, runner = the_model.run_sim(datetime.date(2015, 11, 15), until=100, seed=555)
    # a.gen_do_conversion('rubles', 40, 'dollar', 1)
    # print(a.res_slice(cItem))
    # print('a : {}, b : {}'.format(a, b))

