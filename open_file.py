import datetime

from model.model import cNodeFieldModel
from model.nodes.classes.Node_func_v2 import cAgentNode, cHubNode, cFuncNode
from model.nodes.classes.Task import cTask, cDelivery

from model.nodes.ProcessMonitor import cProcessMonitor


def open_nodes():
    the_model = cNodeFieldModel()
    node1 = cAgentNode('MatFlow')
    node2 = cHubNode('CondNode')
    node3 = cFuncNode('ApplyPrice1')
    node4 = cFuncNode('ApplyPrice2')
    node5 = cFuncNode('ApplyPrice3')
    node6 = cAgentNode('Consumer')
    node7 = cFuncNode('Tagger')

    # Set some tasks to start-up
    MatFlow_items = [cDelivery('matflow1', urgent=True, start_time=15), cDelivery('matflow2', start_time=11),
                     cDelivery('matflow3', True), cDelivery('matflow4'), cTask('Unusual'),
                     cDelivery('matflow5', late=True, start_time=8), cDelivery('matflow6', urgent=True),
                     cDelivery('matflow7'), cDelivery('matflow8'),
                     cTask('UrgentInfo', urgent=True), cDelivery('Gold', expertise=True),
                     cTask('Copper', expertise=True)]
    node1.set_tasks(MatFlow_items)
    node2.connect_nodes(inp_nodes=[node1], out_nodes=[node3, node4, node5])

    Consumer_items = [cDelivery('Wanna_Drink', urgent=True, start_time=5, direct_address=node7)]
    node6.set_tasks(Consumer_items)
    node6.connect_buddies([node3, node4, node5])
    node7.connect_nodes(inp_node=node6, out_node=node1)

    def _action(task):
        task.tags = 'TROLOLOOLO'
        return True

    node7._action = _action

    cond_dict = {node3: 'urgent = True',
                 node4: 'expertise = True',
                 node5: 'start_time > 7'}
    node2.condition(cond_dict)

    the_model.addNodes([node1, node2, node3, node4, node5, node6, node7])

    # temporary parenting
    node2.parent = node1
    node3.parent = node2
    node4.parent = node2
    node5.parent = node2
    node7.parent = node6
    node1.parent = node7
    node6.parent = [node3, node4, node5]

    return the_model


def run_sim(the_model):
    print('********************************')
    print('********START SIMULATION********')
    print('********************************')
    loganddata, runner = the_model.run_sim(datetime.date(2016, 3, 15), until=25, seed=555, debug=True)
    pm = cProcessMonitor(runner.system.simpy_env, until=25)
    print(id(runner.system.simpy_env))
    # pm.plot_procs_groups()
    pm.plot_event_density()

