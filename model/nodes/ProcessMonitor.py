__author__ = 'User'
import simpy
from collections import namedtuple
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import matplotlib.patheffects as path_effects
from functools import wraps
from itertools import cycle

class OtherObject:
    pass

class EnvPatched(simpy.Environment):
    """
        Monkey-patched simpy environment to track all events and related objects
    """
    def __init__(self, debug):
        super().__init__()
        self.event_set = set([])
        self.class_proc = set([])
        self.debug = debug

    def step(self):
        super().step()
        if self.debug:
            for ev_tup in self._queue:
                # Map objects to generators
                for cb in ev_tup[3].callbacks:
                    if hasattr(cb.__self__, '_generator'):
                        current_process = cb.__self__
                        parent_obj = current_process._generator.gi_frame.f_locals['self']
                        temp_tuple = (current_process, parent_obj)
                        self.class_proc.update([temp_tuple])
                    else:
                        current_process = cb.__self__
                        # check if object has parent node
                        if hasattr(current_process, 'parent'):
                            temp_tuple = (current_process, current_process.parent)
                            self.class_proc.update([temp_tuple])
                        else:
                            temp_tuple = (current_process, OtherObject)
                            self.class_proc.update([temp_tuple])

                large_ev_tup = ev_tup + tuple(ev_tup[3].callbacks)
                self.event_set.update([large_ev_tup])


class cProcessMonitor:
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

        self._map_events_to_tuple()
        self._map_event_tuple_to_proc_dict(self.events)
        self._map_process_to_object()

    def _with_check(f):
        """
        Disable methods call if debug mode if off
        """
        @wraps(f)
        def wrapped(inst, *args, **kwargs):
            if inst.env.debug:
                # print('DEBUG')
                return f(inst, *args, **kwargs)
            else:
                print('[WARNING] Turn on debug attribute to call {}'.format(f))
                return
        return wrapped

    @_with_check
    def _map_events_to_tuple(self):
        for an_event in sorted(self.env.event_set, key=lambda x: x[2]):
            self.events += [self.event_tuple(an_event[0], an_event[1], an_event[2], an_event[3], an_event[4:])]
        print('<<NUMBER OF EVENTS>> :', len(self.events))

    @_with_check
    def _map_event_tuple_to_proc_dict(self, ev_tuple):
        for ev in ev_tuple:
            for cb in ev[4]:
                self.proc_dict.setdefault(cb.__self__, [])
                self.proc_dict[cb.__self__].append(ev)

    @_with_check
    def _map_process_to_object(self):
        for proc, obj in self.env.class_proc:
            self.obj_proc_dict.setdefault(obj, [])
            self.obj_proc_dict[obj].append(proc)

    @_with_check
    def print_process(self, long=False):
        """
        Print local dictionaries in nice form
        """
        for k, v in self.proc_dict.items():
            print('Process : {} \n Events :'.format(k))
            for ev in v:
                print(ev.start_time, ev.event)
            print('---------------------------------------')

        for obj, proc in sorted(self.obj_proc_dict.items(), key=lambda t: len(str(t[0]))):
            print('=========='*5)
            print('Object : {} \n processes : {}'.format(obj, proc))
            print('----------'*5)
            for item in proc:
                if long:
                    print(self.proc_dict[item])
                else:
                    print('{:<65} :  {:<3} Events'.format(str(item), len(self.proc_dict[item])))
            print('=========='*5)

    @_with_check
    def plot_event_density(self):
        """
        Draw plot with event number/ environment time  on axes
        """
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

    @_with_check
    def plot_procs_groups(self):
        """
        Draw event bar-plot on time axis, with grouping by parent objects.
        ^ Obj1|ev ev     ev             |Process instance
        |     | ev ev     ev            |Process instance
        | Obj2| ev      ev    ev        |Process instance
        |     |ev      ev    ev         |Process instance
        | Objn|     ev     ev       ev  |Process instance
        o---------------------------------------------->Time
        """
        import textwrap
        colors = 'rgcmykwrgcmykwrgcmykwrgcmykw'

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
        pos_cont_green = set([])
        pos_cont_red = set([])
        # Sorted by object repr length
        for obj, procs in sorted(self.obj_proc_dict.items(), key=lambda t: len(str(t[0]))):
            old_i = i
            for proc in procs:
                for ev in self.proc_dict[proc]:

                    plt.barh(proc_line_y[i], width=1, height=8, left=ev.start_time, align='center', alpha=0.4,
                             color=colors[c])
                    plt.text(ev.start_time, proc_line_y[i]-6, str(ev.event_num),  va='center', color='purple', size=8)
                    label = str(ev.event).split(' ')[0]
                    # plt.text(ev.start_time, proc_line_y[i]+6, label,  va='center', color='r', size=9, rotation=60)
                    # Draw process label
                    plt.text(self.until+self.until/15, proc_line_y[i], str(proc).split(' ')[0],  va='center',
                             color='black', size=10)

                    # Draw Store arrows
                    y_pos = proc_line_y[i]
                    x_pos = ev.start_time+0.5
                    iterrator = cycle([-1, 1])
                    n = 0
                    iterrator2 = cycle([-1, 1])
                    m = 0
                    if isinstance(ev.event, simpy.resources.store.StorePut):
                        # Check if arrow already draw in that place, then ,make step in both directions
                        while (x_pos, y_pos) in pos_cont_green:
                            n += 1
                            x_pos += 0.1*iterrator.__next__()*n
                        axes.arrow(x_pos, y_pos, dx=0, dy=4, head_width=0.1, head_length=1,
                                   color='lightgreen', width=0.02,
                                   path_effects=[path_effects.Stroke(linewidth=0.1, foreground='black')])
                        pos_cont_green.add((x_pos, y_pos))

                    elif isinstance(ev.event, simpy.resources.store.StoreGet):
                        while (x_pos, y_pos) in pos_cont_red:
                            m += 1
                            x_pos += 0.1*iterrator2.__next__()*m
                        axes.arrow(x_pos, y_pos, dx=0, dy=-4, head_width=0.1, head_length=1,
                                   color='red', width=0.02,
                                   path_effects=[path_effects.Stroke(linewidth=0.1, foreground='black')])
                        pos_cont_red.add((x_pos, y_pos))

                i += 1

            # Create side labels - objects name's
            obj_label = textwrap.fill(str(obj), 25)
            text_altitude_index = i-int((i-old_i)/2.)

            plt.text(-int(self.until/8), proc_line_y[text_altitude_index-1], obj_label,  va='center',
                     color='black', size=12)
            c += 1
        # this locator puts ticks at regular intervals
        loc = plticker.MultipleLocator(base=self.until//20)
        axes.xaxis.set_major_locator(loc)
        plt.show()

    @_with_check
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