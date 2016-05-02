from model.nodes.metatypes import mtQueue, mtPile
import model.nodes.simulengin.simulengin as simulengin
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
        self.items = [name for i in range(count)]
        self.count = count

        if self.is_simulation_running:
            self.items_store = simpy.Store(self.simpy_env)
        else:
            self.items_store = mtQueue(self, self.items)

    def __repr__(self):
        return str(self.name) + " : count of " + str(self.count) + " " + str(self.items_store.items)[:25]


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

    def __init__(self):
        super().__init__()
        self.res_all = {}

    def spawn_item(self, name, qtty):
        self.res_all[name] = cItem(name, qtty)

    def spawn_pile(self, name, qtty):
        self.res_all[name] = cPile(name, qtty)

    def init_sim(self):
        super().init_sim()
        for key_i, res_i in self.res_all.items():
            res_i.s_set_devs(self.devs)
            res_i.init_sim()

    def gen_dumb_printer(self):
        while True:
            # print('hi')
            yield self.timeout(1)
            # print('my wallet : {}'.format(self.res_all))
            self.sent_log('my wallet : {}'.format(self.res_all))

    def my_generator(self):
        self.as_process(self.gen_dumb_printer())
        yield self.empty_event()

    def get_some(self, name, qtty):
        qtty = yield self.res_all[name].value.get(qtty)
        return qtty


    def gen_take_qtty(self, name, qtty):
        if name not in self.res_all:
            self.sent_log('{} has not {} key'.format(type(self), name))
            return False

        if type(self.res_all[name]) == cPile:
            if self.debug_on:
                print('value {} '.format(self.res_all[name].value.level))

            if self.res_all[name].value.level < qtty:
                self.sent_log("not enough value level ")
                # Alternative path?

            yield self.res_all[name].value.get(qtty)


        elif type(self.res_all[name]) == cItem:
            if self.debug_on:
                print('count {} '.format(self.res_all[name]))
            if len(self.res_all[name].count.items()) <= 0:
                self.sent_log("not enough items")
            yield self.res_all[name].value.get(qtty)

        yield self.empty_event()


class test_node(simulengin.cConnToDEVS):

    def __init__(self):
        super().__init__()
        self.processes_tuple = namedtuple('planned_procs', 'gen wallet item qtty when')
        self.planned_processes = []

    def init_sim(self):
        super().init_sim()
        for proc in self.planned_processes:
            self.as_process(proc.gen(proc.wallet, proc.item, proc.qtty, proc.when))

    def my_generator(self):
        yield self.empty_event()

    def some_process(self, wallet, item, qtty, when):
        yield self.simpy_env.timeout(when)
        getter = wallet.gen_take_qtty(item, qtty)
        getter_event = next(getter)
        if getter_event.triggered:
            self.sent_log('taken {}'.format(getter_event.amount))
        else:
            self.sent_log('cant take {}'.format(getter_event.amount))

    def get_goods(self, wallet, item, qtty, when):
        self.planned_processes.append(self.processes_tuple(self.some_process, wallet, item, qtty, when))


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.INFO)
    # from logging.config import fileConfig
    # fileConfig('logging_config.ini')

    import datetime
    from model.model import cNodeFieldModel
    the_model = cNodeFieldModel()

    wal_a = cWallet()
    wal_a.spawn_pile('rubles', 100)
    wal_b = cWallet()
    wal_b.spawn_item('gold ingots', 4)

    test_obj = test_node()
    test_obj.get_goods(wal_a, 'rubles', qtty=25, when=5)
    test_obj.get_goods(wal_a, 'rubles', qtty=80, when=7)
    # test_obj.place_goods(wal_b, 'rubles', goods, 10)

    # the_model.addNodes([wal_a, wal_b])
    the_model.addOtherSimObj(wal_a)
    the_model.addOtherSimObj(wal_b)
    the_model.addOtherSimObj(test_obj)
    the_model.run_sim(datetime.date(2016, 5, 2), until=25, seed=555, debug=True)

    # test_obj.get_goods(wal_a, 'rubles', qtty=25, when=5)
