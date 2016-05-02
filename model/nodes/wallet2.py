from model.nodes.metatypes import mtQueue, mtPile
import model.nodes.simulengin.simulengin as simulengin
import simpy

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
            print('hi')
            yield self.timeout(1)
            print('my wallet : {}'.format(self.res_all))
            self.sent_log('my wallet : {}'.format(self.res_all))

    def my_generator(self):
        self.as_process(self.gen_dumb_printer())
        yield self.empty_event()

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


if __name__ == '__main__':
    import datetime
    from model.model import cNodeFieldModel
    the_model = cNodeFieldModel()

    wal_a = cWallet()
    wal_a.spawn_pile('rubles', 100)
    wal_b = cWallet()
    wal_b.spawn_item('gold ingots', 4)

    # the_model.addNodes([wal_a, wal_b])
    the_model.addOtherSimObj(wal_a)
    the_model.addOtherSimObj(wal_b)
    the_model.run_sim(datetime.date(2016, 5, 2), until=25, seed=555, debug=True)
