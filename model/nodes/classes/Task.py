__author__ = 'User'
from collections import Counter
from random import randint, choice
import model.nodes.simulengin.simulengin as simulengin
import simpy


class StateMachine:
    def __init__(self):
        self.handlers = {}
        self.startState = None
        self.endStates = []
        self.curState = self.startState

    def add_state(self, name, handler, end_state=0):
        name = name.upper()
        self.handlers[name] = handler
        if end_state:
            self.endStates.append(name)

    def set_state(self, state):
        self.curState = state

    def set_start(self, name):
        print(self, 'START STATE', 'name : ', name)
        self.startState = name.upper()
        self.curState = name.upper()

    def run(self, cargo):
        try:
            handler = self.handlers[self.startState]
        except:
            raise RuntimeError("must call .set_start() before .run()")
        if not self.endStates:
            raise RuntimeError("at least one state must be an end_state")

        while True:
            (newState, cargo) = handler(cargo)
            self.curState = newState
            if newState.upper() in self.endStates:
                print("State reached ", newState)
                break
            else:
                handler = self.handlers[newState.upper()]

        return newState


class TaskMonitor:
    def __init__(self):
        self.task_dict = []

    def reset_task_monitor(self):
        self.task_dict = []

    def add_task(self, rec):
        self.task_dict.append(rec)

    def status(self):
        while True:
            print('---------------------------------------------------------------')
            print('TASKS IN SYSTEM {} : '.format(len(self.task_dict)))

            if len(self.task_dict) > 0:
                count_dict = Counter({None: 0, 'Other': 0})
                num = int(len(self.task_dict))

                states = [n.curState for n in self.task_dict]
                nones = states.count(None)
                dones = states.count('DONE')
                percent_nones = ((len(states) - nones)/len(states))*100
                percent_dones = (dones/len(states))*100

                shkala = '...................'
                shkala_nones = shkala.replace('.', 'X', 2 * (int(percent_nones)//10))
                shkala_dones = shkala.replace('.', 'X', 2 * (int(percent_dones)//10))

                print('   Started tasks : [{0:>6.2f}%] {1:>34}'.format(percent_nones, shkala_nones))
                print('   Done tasks    : [{0:>6.2f}%] {1:>34}'.format(percent_dones, shkala_dones))
                for i in range(0, num, 2):
                    if i + 2 > num:
                        print('   {:<18}tags{:>25} | {:>10} '.format(str(self.task_dict[i]),
                                                                       str(self.task_dict[i].tags),
                                                                       str(self.task_dict[i].curState)))
                    else:
                        print('   {:<18}tags{:>25} | {:>10} || {:>17} tags{:>25} | {:>10} '.format(
                                                                                str(self.task_dict[i]),
                                                                                str(self.task_dict[i].tags),
                                                                                str(self.task_dict[i].curState),
                                                                                str(self.task_dict[i+1]),
                                                                                str(self.task_dict[i+1].tags),
                                                                                str(self.task_dict[i+1].curState)))

                print('---------------------------------------------------------------')

            return True


class cTask(StateMachine):
    """
        Task class
    """
    # Task monitor
    tm = TaskMonitor()

    def __init__(self, name='Task Base Class', **kwargs):
        self.name = name
        self.start_time = 0
        super().__init__()

        self.wrong = ''

        for key, val in kwargs.items():
            setattr(self, key, val)

        self.add_state('PENDING', self.pending, 0)
        self.add_state('CRAFTING', self.craft, 0)
        self.add_state('CANCELLED', None, end_state=1)
        self.add_state('DONE', None, end_state=1)
        self.set_start('PENDING')

        self.tm.add_task(self)
        # list of node which handle me
        # self.registry = []
        self._tags = []

        self.accepted = True

    def pending(self, cargo):
        if self.accepted:
            newState = 'CRAFTING'
        else:
            newState = 'CANCELLED'
        return newState, cargo

    def craft(self, cargo):
        self.crafted = choice([True, False])
        print('{} is {} to craft'.format(self, self.crafted))
        if self.crafted:
            newState = 'DONE'
        else:
            newState = 'CANCELLED'
        return newState, cargo

    def set_task_to_wrong(self):
        # self.wrong = 'WRONG '
        self.set_state('WRONG DEST')

    def set_tag(self, tag):
        self.tags.append(tag)

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, a_tag):
        self._tags.append(a_tag)
        print('Tag added {}'.format(a_tag))

    def __repr__(self):
        return '{}Task : {}'.format(self.wrong, self.name)


class cDelivery(cTask):
    def __init__(self, name, urgent=False, **kwargs):
        super().__init__(name, **kwargs)
        self.urgent = urgent


class cMarketTask(cTask):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)


# Simple Task create function
# cTask_name
def make_task_from_str(a_string):
    kls, name = a_string.split('_')
    if kls == 'cTask':
        a_task = cTask(name)
        print('made', a_task)

    return a_task
