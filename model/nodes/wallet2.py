from model.nodes.metatypes import mtQueue, mtPile
import model.nodes.simulengin.simulengin as simulengin
import simpy
from pprint import pprint
from random import shuffle
from collections import namedtuple
from model.nodes.simulengin.simulengin import cDiscreteEventSystem

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
        self.items = [name for _ in range(count)]
        self.count = count

        # fixme self.is_simulation_running never True
        if self.is_simulation_running:
            self.items_store = simpy.Store(self.simpy_env)
        else:
            self.items_store = mtQueue(self, *self.items)

    def __repr__(self):
        if hasattr(self.items_store, 'items'):
            return str(len(self.items_store.items)) + ' of ' + str(self.items_store.items[0])
            # return str(self.name) + " : count of " + str(self.count) + " " + str(self.items_store.items)[:75]
        else:
            return str(len(self.items_store.proxylist)) + ' of ' + str(self.items_store.proxylist[0])

class cPile(cValuedResource):
    def __init__(self, name, value=0):
        super().__init__(name)

        # fixme self.is_simulation_running never True
        if self.is_simulation_running:
            self.value = simpy.Container(self.simpy_env)
        else:
            self.value = mtPile(level=value)

    def __repr__(self):
        if hasattr(self.value, 'level'):
            return str(self.name) + " : " + str(self.value.level)
        else:
            return str(self.name) + " : " + str(self.value.proxyLevel)


class cWallet(simulengin.cConnToDEVS):
    """
    cWallet provide container facilities, where you could place 'Items' as objects or 'Piles' as homogeneous matter
    You can manipulate Wallet before, in-between and after

    :param glob_res_map: dict| class variable, which holds all known resource types

    """
    # holding known resource species
    glob_res_map = {}

    def __init__(self, name=None):
        """
        :param name: str| Wallet name
        """
        super().__init__()
        self.name = name
        self.res_all = {}

    def init_sim(self):
        super().init_sim()
        for _, res_i in self.res_all.items():
            self.init_resource(res_i)

    def my_generator(self):
        self.as_process(self.gen_dumb_printer())
        yield self.empty_event()

    # connect to DEVs
    def init_resource(self, res):
        """
        :param res: mtQueue or mtPile| resource which will converting into simulation
        :return: None
        """
        res.s_set_devs(self.devs)
        res.init_sim()

    # debug generator
    def gen_dumb_printer(self):
        while True:
            yield self.timeout(1)
            self.sent_log('my wallet : {}'.format(self.res_all))

    # Creating new resource species
    def spawn_item(self, name, qtty):
        """
        Spawning objects as 'Items'
        :param name: str| name of items
        :param qtty: int| quantity of items
        :return: None
        """
        self.res_all[name] = cItem(name, qtty)

        if self.is_simulation_running:
            self.init_resource(self.res_all[name])

        # register in base
        self.glob_res_map.setdefault(cItem, [])
        self.glob_res_map[cItem].append(name)

    def spawn_pile(self, name, qtty):
        """
        Spawning homogeneous matter as 'Pile'
        :param name: str | name of Pile
        :param qtty: int | volume of Pile
        :return: None
        """
        self.res_all[name] = cPile(name, qtty)

        if self.is_simulation_running:
            self.init_resource(self.res_all[name])

        # register in base
        self.glob_res_map.setdefault(cPile, [])
        self.glob_res_map[cPile].append(name)

    # Adding resources
    def add_to_items(self, name, qtty):
        """
        Adding items to existing wallet 'Item' type field. If not exist, creating new field
        :param name: str| name of items
        :param qtty: int| quantity of items
        :return: None
        """
        self.sent_log('trying to put <{}> into self dict {}'.format(name, self.res_all.keys()))

        if not self.check_existence(name):
            self.spawn_item(name, 0)

        # check for wrong operation
        if isinstance(self.res_all[name], cItem):
            for i in range(qtty):
                self.res_all[name].items_store.put(name)
        else:
            raise AttributeError('Cant add due to resource type mismatch : {} != {}'
                                 .format(self.res_all[name].__class__, cItem))

    def add_to_pile(self, name, qtty):
        """
        Adding matter to existing wallet 'Pile' type field. If not exist, creating new field
        :param name: str | name of Pile
        :param qtty: int | volume of Pile
        :return: None
        """
        self.sent_log('trying to put <{}> into self dict {}'.format(name, self.res_all))

        if not self.check_existence(name):
            self.spawn_pile(name, 0)

        # check for wrong operation
        if isinstance(self.res_all[name], cPile):
            self.res_all[name].value.put(qtty)
        else:
            raise AttributeError('Cant add due to resource type mismatch : {} != {}'
                                 .format(self.res_all[name].__class__, cPile))

    def add_to_existed(self, name, qtty):
        """
        Automaticly add given 'Item' of 'Pile' resource if these its belong to 'glob_res_map' dict base
        :param name: str | name of resource
        :param qtty: int | resource quantity or volume
        :return: None
        """

        if name in self.glob_res_map[cItem]:
            self.sent_log('found {} in cItem'.format(name))
            self.add_to_items(name, qtty)
        elif name in self.glob_res_map[cPile]:
            self.sent_log('found {} in cPile'.format(name))
            self.add_to_pile(name, qtty)
        else:
            raise AttributeError('Dont have such specie in base')


    def check_existence(self, name):
        """
        Checking existence of given resource
        :param name: resource name
        :return: Bool
        """
        return name in self.res_all

    def get_item(self, name):
        """
        Get items of given resource
        :param name: str| resource name
        :return int or list| for given type
        """

        if self.is_simulation_running:

            if isinstance(self.res_all[name], cPile):
                return self.res_all[name].value.level
            elif isinstance(self.res_all[name], cItem):
                return list(self.res_all[name].items_store.items)
        else:

            if isinstance(self.res_all[name], cPile):
                return self.res_all[name].value.proxyLevel
            elif isinstance(self.res_all[name], cItem):
                return list(self.res_all[name].items_store.proxylist)

    def add_items(self, name, qtty):
        # todo adapt from wallet.py
        self.sent_log('trying to put <{}> into self dict {}'.format(name, self.res_all))
        if not self.check_existence(name):

            # todo spawn apropriate item or pile
            if name in self.glob_res_map[cItem]:
                self.spawn_item(name, 0)
            elif name in self.glob_res_map[cPile]:
                self.spawn_pile(name, 0)
            else:
                self.spawn_item(name, 0)
            # This was a workaround before self.is_simulation_running
            self.res_all[name].s_set_devs(self.devs)

        if type(self.res_all[name]) == cPile:
            self.res_all[name].value.put(qtty)

        if type(self.res_all[name]) == cItem:
            for i in range(qtty):
                self.res_all[name].items_store.put(name)

    def gen_take_qtty(self, name, qtty):
        # todo adapt from wallet.py

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

            if len(self.res_all[name].items_store.items()) <= 0:
                self.sent_log("not enough items")

            yield self.res_all[name].value.get(qtty)

        yield self.empty_event()


class DumbNode(simulengin.cConnToDEVS):
    """
    Dumb "node" for testing purposes
    """
    ALL_DumbNode = []

    def __init__(self, name=None):
        super().__init__()
        self.ALL_DumbNode.append(self)
        self.name = name
        self.processes_tuple = namedtuple('planned_procs', 'gen wallet item qtty when')
        self.planned_processes = []

    def init_sim(self):
        super().init_sim()
        for proc in self.planned_processes:
            self.as_process(proc.gen(proc.wallet, proc.item, proc.qtty, proc.when))

    def my_generator(self):
        yield self.empty_event()

    def take_process(self, wallet, item, qtty, when):
        yield self.simpy_env.timeout(when)
        getter = wallet.gen_take_qtty(item, qtty)
        getter_event = next(getter)
        if getter_event.triggered:
            self.sent_log('taken {}'.format(getter_event.amount))
        else:
            self.sent_log('cant take {}'.format(getter_event.amount))

    def put_process(self, wallet, item, qtty, when):
        yield self.simpy_env.timeout(when)
        wallet.add_to_items(item, qtty)

    def put_process2(self, wallet, item, qtty, when):
        yield self.simpy_env.timeout(when)
        wallet.add_to_pile(item, qtty)

    def get_goods(self, wallet, item, qtty, when):
        self.planned_processes.append(self.processes_tuple(self.take_process, wallet, item, qtty, when))

    def place_goods(self, wallet, item, qtty, when):
        self.planned_processes.append(self.processes_tuple(self.put_process, wallet, item, qtty, when))

    def place_to_pile(self, wallet, item, qtty, when):
        self.planned_processes.append(self.processes_tuple(self.put_process2, wallet, item, qtty, when))


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    # from logging.config import fileConfig
    # fileConfig('logging_config.ini')

    import datetime
    from model.model import cNodeFieldModel
    the_model = cNodeFieldModel()

    wal_a = cWallet('wal_a')
    wal_a.spawn_pile('rubles', 100)

    wal_b = cWallet('wal_b')
    wal_b.spawn_item('gold ingots', 4)

    test_obj = DumbNode(name='test_obj')
    test_obj.get_goods(wal_a, 'rubles', qtty=60, when=5)
    test_obj.get_goods(wal_a, 'rubles', qtty=80, when=7)
    test_obj.place_goods(wal_a, 'plumbum_ingots', qtty=130, when=14)

    test_obj.place_goods(wal_b, 'ruble_packs', qtty=15, when=10)

    test_obj_2 = DumbNode(name='test_obj_2')
    test_obj_2.get_goods(wal_a, 'rubles', qtty=60, when=5)

    test_obj_3 = DumbNode(name='test_obj_3')
    test_obj_3.get_goods(wal_a, 'rubles', qtty=60, when=5)

    # HOW-TO get values from cWallet
    logger.info(wal_a.get_item('rubles'))
    logger.info(wal_b.get_item('gold ingots'))

    # the_model.addNodes([wal_a, wal_b])
    the_model.addOtherSimObj(wal_a)
    the_model.addOtherSimObj(wal_b)

    test_objs = DumbNode.ALL_DumbNode
    # shuffle order
    shuffle(test_objs)
    for nd in test_objs:
        the_model.addOtherSimObj(nd)

    logger.info('<<<<<<< STARTING SIMULATION !!! >>>>>>>>>')
    the_model.run_sim(datetime.date(2016, 5, 2), until=25, seed=555, debug=True)
    logger.info('>>>>>>> POST SIMULATION !!! <<<<<<<<<<')

    # pprint(wal_a.res_all)
    # test_obj.get_goods(wal_a, 'rubles', qtty=25, when=5)
