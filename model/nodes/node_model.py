"""
    Here we use meta-structure to create a structure for our discret-event system.
    Then we use this structure with an instance of simpy.Environment to deploy
    a simulation process.
"""

from model.nodes.simulengin.simulengin import cDiscreteEventSystem, cSimulRunner
from model.nodes.ProcessMonitor import cProcessMonitor, EnvPatched

import simpy

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

    def run_sim(self, start_date, sim_until=100, seed=None, debug=False):
        # Build a devs system
        # simpyenv = simpy.Environment()
        simpyenv = EnvPatched(debug)
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

        sim_results = sim_manager.run_and_return_log(sim_until, print_console=False, print_to_list=None)

        # Monitor results
        # pm = cProcessMonitor(simpyenv, sim_until)
        # pm.print_process()
        # pm.plot_procs_groups()
        # pm.plot_event_density()
        # -----------------
        return [sim_results, sim_manager]









