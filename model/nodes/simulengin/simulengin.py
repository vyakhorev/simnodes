# -*- coding: utf-8 -*-

__author__ = 'Alexey'

import simpy
import datetime
import random
import sys
import model.nodes.simulengin.statkeeper as statkeeper
import model.nodes.meta

class cDiscreteEventSystem(object):
    # TODO: implement methods to cope with node structure during simulation
    """
        During simulation this class helps to maintain:
        1. Link to global system vars (random generator with preset seed, logger and so on)
        2. Nodes structure.
    """
    def __init__(self, simpy_env, real_world_datetime_start):
        self.simpy_env = simpy_env
        self.logging_on = True
        self.random_generator = None
        self.__real_world_datetime_start = real_world_datetime_start
        self.log_printers = []
        self.nodes = []
        self.ports = []
        self.others = [] #test purposes

    def register_node(self, a_node):
        a_node.s_set_devs(self)
        self.nodes += [a_node]
        for port_i in a_node.ports.values():
            port_i.s_set_devs(self)
            self.ports += [port_i]

    def register_other(self, other_obj):
        other_obj.s_set_devs(self)
        self.others += [other_obj]

    def convert_datetime_to_simtime(self, a_real_date):
        if not(a_real_date is None):
            return (a_real_date - self.__real_world_datetime_start).days

    def convert_simtime_to_datetime(self, simul_time_days):
        return self.__real_world_datetime_start + datetime.timedelta(days = simul_time_days)

    def nowsimtime(self):
        return self.simpy_env.now

    def set_seed(self, seed = None):
        if seed is None:
            #seed = random.randint(0, sys.maxint)  #Обрати внимание, когда на разных 32/64 запускаешь!
            seed = random.randint(0, 10000)
        self.random_generator = random.Random(seed)

    def my_generator(self):
        #Это самый первый генератор, куда мы заходим
        self.build_system()
        for n_i in self.nodes:
            n_i.init_sim()
            self.simpy_env.process(n_i.my_generator())
            for port_i in n_i.ports.values():
                port_i.init_sim()
                self.simpy_env.process(port_i.my_generator())
        for oth_i in self.others:
            oth_i.init_sim()
            self.simpy_env.process(oth_i.my_generator())
        yield empty_event(self.simpy_env) #Formality

    def add_node_during_simulation(self, a_node, do_register = 1):
        if do_register:
            self.register_node(a_node)
        else:
            a_node.s_set_devs(self)
        a_node.init_sim()
        self.simpy_env.process(a_node.my_generator())

    def build_system(self):
        pass

    def sent_log(self, sender_instance, msg_text):
        if self.logging_on:
            sender_name = sender_instance.log_repr()
            timestamp = self.nowsimtime()
            for a_pr in self.log_printers:
                a_pr.pr(timestamp, sender_name, msg_text)

    def add_printer(self, a_printer):
        self.log_printers += [a_printer]

def empty_event(simpy_env):
    return simpy_env.timeout(0)

class cContainerPart(simpy.Container):
    def __init__(self, env, capacity=float('inf'), init=0):
        self.filled = simpy.Resource(env, capacity=1)
        self.filled.request() # Будет отпущен, когда вызовут put
        super(cContainerPart, self).__init__(env, capacity=float('inf'), init=0)

    def get_available(self, qtty):
        if self.level >= qtty:
            yield self.get(qtty)
        else:
            if self.level > 0:
                yield self._env.process(self.get_available(self.level))
            remains_to_take = qtty - self.level
            yield self.filled.request()
            yield self._env.process(self.get_available(remains_to_take))

    def put(self, amount):
        super(cContainerPart, self).put(amount)
        if len(self.filled.users) > 0:
            self.filled.release(self.filled.users[0])

class cConnToDEVS(model.nodes.meta.MetaStruct):
    def log_repr(self):
        return self.__repr__()

    def s_set_devs(self, discrete_event_system):
        self.devs = discrete_event_system
        self.simpy_env = self.devs.simpy_env

    def sent_log(self, a_msg):
        self.devs.sent_log(self, a_msg)

    def as_process(self, new_process):
        self.simpy_env.process(new_process)

    def timeout(self, T):
        return self.simpy_env.timeout(T)

    def empty_event(self):
        return self.timeout(0)

    def my_generator(self):
        raise NotImplementedError()

    def init_sim(self):
        # There is simpy environment already available here
        self.convert_to_simulatables(self.simpy_env)

    def convert_to_simulatables(self, simpy_env):
        for attr, val in self.__dict__.items():
            if hasattr(val, '_simulatable'):
                new_val = val.give_sim_analog(simpy_env)
                #setattr(self, "_nosim_", new_val) # delete ??
                setattr(self, attr, new_val)

class cSimulRunner(object):
    # TODO: revive multiple runs method
    def __init__(self, the_devs):
        self.observers = []
        self.sim_results = statkeeper.c_simulation_results_container()
        self.system = the_devs

    def run_and_return_log(self, sim_until, print_console = True, print_to_list = None):
        self.system.simpy_env.process(self.system.my_generator())
        for obs_i in self.observers:
            obs_i.activate_in_env()
        if print_console:
            self.system.add_printer(console_log_printer())
        if print_to_list is not None:
            self.system.add_printer(list_log_printer(print_to_list))
        # Система собрана - запускаем!
        self.system.simpy_env.run(until = sim_until)
        return dict(log_list=print_to_list, dataframes=self.sim_results)

    #def add_observer(self, observer_class, obs_name, freq):
    #    self.observers += [observer_class(obs_name, self.system, self.sim_results, freq)]

    def add_sim_observer(self, new_observer):
        new_observer.set_system(self.system, self.sim_results)
        self.observers += [new_observer]

class console_log_printer(object):
    def pr(self, timestamp, sender_name, msg_text):
        # msg = ("@[%d] #[%s] : %s"% (timestamp, sender_name, msg_text))

        # table-wise print
        msg = ("@{:<3} {:<75} : {:<15}".format(timestamp, sender_name, msg_text))
        print(msg)

class list_log_printer(object):
    def __init__(self, log_list):
        self.log_list = log_list

    def pr(self, timestamp, sender_name, msg_text):
        msg = [0, 0, 0]
        msg[0] = timestamp
        msg[1] = sender_name
        msg[2] = msg_text
        self.log_list += [msg]

class cAbstObserver():
    # Helps to observe and record statistics from the system

    def __init__(self, obs_name, period = 1):
        self.period = period
        self.obs_name = obs_name

    def full_obs_name(self):
        return "[each %d days] %s"% (self.period, self.obs_name)

    def set_system(self, system, sim_results):
        self.system = system
        self.sim_results = sim_results

    def my_generator(self):
        while True:
            self.cur_date = self.system.simpy_env.now
            self.observe_data()
            yield self.system.simpy_env.timeout(self.period)

    def observe_data(self):
        # Reimplement - you may record multiple ts
        ts_name = "abstract"
        ts_value = 0
        self.record_data(ts_name, ts_value)
        raise NotImplementedError("implement please")

    def record_data(self, ts_name, ts_value):
        # Do not record the same data twice - they are aggregated in pandas, though.. Never tested.
        self.sim_results.add_ts_point(self.full_obs_name(), ts_name, self.cur_date, ts_value)

    def activate_in_env(self):
        self.system.simpy_env.process(self.my_generator())


class old_cAbstObserver():
    # Helps to observe and record statistics from the system
    def __init__(self, obs_name, system, sim_results, period = 1):
        self.obs_name = obs_name
        self.system = system
        self.sim_results = sim_results
        self.period = period

    def full_obs_name(self):
        return "[each %d days] %s"% (self.period, self.obs_name)

    def my_generator(self):
        while True:
            self.cur_date = self.system.simpy_env.now
            self.observe_data()
            yield self.system.simpy_env.timeout(self.period)

    def observe_data(self):
        # Reimplement - you may record multiple ts
        ts_name = "abstract"
        ts_value = 0
        self.record_data(ts_name, ts_value)
        raise NotImplementedError("implement please")

    def record_data(self, ts_name, ts_value):
        # Do not record the same data twice - they are aggregated in pandas, though.. Never tested.
        self.sim_results.add_ts_point(self.full_obs_name(), ts_name, self.cur_date, ts_value)

    def activate_in_env(self):
        self.system.simpy_env.process(self.my_generator())