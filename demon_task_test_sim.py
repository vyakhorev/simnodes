# Testing tasks and daemons

import datetime

from model.model import cNodeFieldModel
from model.nodes.ProcessMonitor import cProcessMonitor

# BlueNides.py !

def BuildTest1():
    the_model = cNodeFieldModel()



    return the_model


def run_model(nodemodel, do_process_plot=False):

    print('********************************')
    print('********START SIMULATION********')
    print('********************************')
    loganddata, runner = the_model.run_sim(datetime.date(2016, 3, 15), until=25, seed=555, debug=True)

    # Plot processes
    if do_process_plot:
        pm = cProcessMonitor(runner.system.simpy_env, until=25)


if __name__ == '__main__':
    the_model = BuildTest1()
    run_model(the_model)
