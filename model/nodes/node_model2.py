"""
    Here we use meta-structure to create a structure for our discret-event system.
    Then we use this structure with an instance of simpy.Environment to deploy
    a simulation process.
"""

from model.nodes.simulengin.simulengin import cDiscreteEventSystem, cSimulRunner

import simpy

from collections import namedtuple
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker

class OtherObject:
    pass

class EnvPatched(simpy.Environment):
    """
        Monkey-patched simpy environment to track all events and related objects
    """
    def __init__(self):
        super().__init__()
        self.event_set = set([])
        self.class_proc = set([])

    def step(self):
        super().step()
        for ev_tup in self._queue:
            # Map objects to generators
            try:
                for cb in ev_tup[3].callbacks:
                    current_process = cb.__self__
                    parent_obj = current_process._generator.gi_frame.f_locals['self']
                    temp_tuple = (current_process, parent_obj)
                    self.class_proc.update([temp_tuple])
            except AttributeError as e:
                for cb in ev_tup[3].callbacks:
                    current_process = cb.__self__
                    # Todo add parent to objects
                    # print(cb)
                    # try:
                    #     print(current_process.parent)
                    # except:
                    #     pass
                    # print(dir(current_process))
                    temp_tuple = (current_process, OtherObject)
                    self.class_proc.update([temp_tuple])

            large_ev_tup = ev_tup + tuple(ev_tup[3].callbacks)
            self.event_set.update([large_ev_tup])


class ProcessMonitor:
    """
        This class produce some mapping from environment statistics,
        and draw object-process-event relation plot

        :param env: 'cls' | patched simpy environment
        :param until: 'int'| simpy environment simulation time
    """
    def __init__(self, env, until):
        self.env = env
        self.until = until

        self.event_tuple = namedtuple('event_tuple', 'start_time priority event_num event callbacks')
        # all events captured during simulation
        self.events = []
        # all processes with related events
        self.proc_dict = {}
        # objects with processes
        self.obj_proc_dict = {}

        self.map_events_to_tuple()
        self.map_event_tuple_to_proc_dict(self.events)
        self.map_process_to_object()

    def map_events_to_tuple(self):
        for an_event in sorted(self.env.event_set, key=lambda x: x[2]):
            self.events += [self.event_tuple(an_event[0], an_event[1], an_event[2], an_event[3], an_event[4:])]
        print('<<NUMBER OF EVENTS>> :', len(self.events))

    def map_event_tuple_to_proc_dict(self, ev_tuple):
        for ev in ev_tuple:
            for cb in ev[4]:
                self.proc_dict.setdefault(cb.__self__, [])
                self.proc_dict[cb.__self__].append(ev)

    def map_process_to_object(self):
        for proc, obj in self.env.class_proc:
            self.obj_proc_dict.setdefault(obj, [])
            self.obj_proc_dict[obj].append(proc)

    def print_process(self):
        """
        Print local dictionaries in nice form
        """
        for k, v in self.proc_dict.items():
            print('Process : {} \n Events :'.format(k))
            for ev in v:
                print(ev.start_time, ev.event)
            print('---------------------------------------')

        for obj, proc in sorted(self.obj_proc_dict.items(), key=lambda t: len(str(t[0]))):
            print('Object : {} \n processes : {}'.format(obj, proc))
            for item in proc:
                print(self.proc_dict[item])

    def plot_event_density(self):
        event_time = {}
        for event in sorted(self.events, key=lambda x: x.start_time):
            event_time.setdefault(event.start_time, 0)
            event_time[event.start_time] += 1

        plt.xlabel('time ')
        plt.ylabel('Events number ')
        plt.grid(True)
        axes = plt.axes()
        loc = plticker.MultipleLocator(base=2.)
        axes.xaxis.set_major_locator(loc)
        plt.plot(list(event_time.keys()), list(event_time.values()))
        plt.show()

    def plot_procs_groups(self):
        import textwrap
        colors = 'rgbcmykwrgbcmykwrgbcmykw'

        height = len(self.proc_dict.keys())*10
        width = self.until
        axes = plt.axes()
        axes.set_xlim([0, self.until+self.until/15])
        axes.set_ylim([0, height])

        proc_line_y = [n+5 for n in range(0, height, 10)]
        proc_labels = []

        plt.yticks(proc_line_y, proc_labels)

        c = 0
        i, old_i = 0, 0
        for obj, procs in sorted(self.obj_proc_dict.items(), key=lambda t: len(str(t[0]))):
            old_i = i
            for proc in procs:
                for ev in self.proc_dict[proc]:
                    plt.barh(proc_line_y[i], width=1, height=8, left=ev.start_time, align='center', alpha=0.4,
                             color=colors[c])
                    plt.text(ev.start_time, proc_line_y[i]-6, str(ev.event_num),  va='center', color='purple', size=8)
                    label = str(ev.event).split(' ')[0]
                    plt.text(ev.start_time, proc_line_y[i]+6, label,  va='center', color='r', size=9, rotation=60)
                    # Draw process label
                    plt.text(self.until, proc_line_y[i], str(proc).split(' ')[0],  va='center', color='black', size=10)

                i += 1

            # Create side labels - objects name's
            obj_label = textwrap.fill(str(obj), 25)
            text_altitude_index = i-int((i-old_i)/2.)

            plt.text(-12, proc_line_y[text_altitude_index-1], obj_label,  va='center', color='black', size=12)
            c += 1
        # this locator puts ticks at regular intervals
        loc = plticker.MultipleLocator(base=5.)
        axes.xaxis.set_major_locator(loc)
        plt.show()

    def plot_procs(self):
        """
        old-version of plot
        :return: None
        """
        height = len(self.proc_dict.keys())*10
        width = self.until
        axes = plt.axes()
        axes.set_xlim([0, self.until+self.until/15])
        axes.set_ylim([0, height])
        proc_line_y = [n+5 for n in range(0, height, 10)]
        proc_labels = []

        for item in self.proc_dict.keys():
            try:
                proc_labels += [item.__repr__().split(' ')[0]]
            except:
                proc_labels += [str(item).split('.')[-1:]]

        plt.yticks(proc_line_y, proc_labels)
        i = 0
        for k, v in self.proc_dict.items():
            for ev in v:
                # print(k, ev.start_time, ev.event)
                plt.barh(proc_line_y[i], width=5, height=8, left=ev.start_time, align='center', alpha=0.4)
                plt.text(ev.start_time, proc_line_y[i]-6, str(ev.event_num),  va='center', color='g', size=8)
                label = str(ev.event).split(' ')[0]
                plt.text(ev.start_time, proc_line_y[i]+6, label,  va='center', color='r', size=7)
            i += 1
        plt.show()

class cNodeModel(object):
    # TODO: make it serializable as well (xml read / write)
    """
        This class maintains node structure during the period before simulation
        and governs simulation itself (there should be no links to this class
        during the simulation process).
    """
    def __init__(self):
        self.nodes = []  #TODO: ordered dict here?
        self.observers = []
        self.others = [] #test purposes

    def addNode(self, newNode):
        self.nodes += [newNode]

    def addOtherSimObj(self, otherObj):
        self.others += [otherObj]

    def addNodes(self, nodesList):
        for n_i in nodesList:
            self.nodes += [n_i]

    def getNodesList(self):
        return self.nodes

    def iterNodesList(self):
        for n_i in self.nodes:
            yield n_i

    def addObserver(self, new_observer):
        self.observers += [new_observer]

    def run_sim(self, start_date, sim_until=100, seed=None):
        # Build a devs system
        # simpyenv = simpy.Environment()
        simpyenv = EnvPatched()
        running_devs = cDiscreteEventSystem(simpyenv, start_date)
        running_devs.set_seed(seed)
        # TODO: clone devs between each run
        for n_i in self.nodes:
            # nothing interesting in there
            running_devs.register_node(n_i)
        for oth_i in self.others:
            running_devs.register_other(oth_i)
        # Run the devs with simul_runner
        sim_manager = cSimulRunner(running_devs)
        for obs_i in self.observers:
            sim_manager.add_sim_observer(obs_i)

        sim_results = sim_manager.run_and_return_log(sim_until, print_console=True, print_to_list=None)

        pm = ProcessMonitor(simpyenv, sim_until)
        # pm.print_process()
        pm.plot_procs_groups()
        # pm.plot_event_density()

        return [sim_results, sim_manager]










