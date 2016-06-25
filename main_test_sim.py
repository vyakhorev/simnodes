import datetime

from model.model import cNodeFieldModel
from model.nodes.classes._old.NodeEconAgent import cNodeEconAgent
# from model.nodes.classes.Node_func import cNode_func, cNode_agent, cNode_hub
from model.nodes.classes.Node_func_v2 import cAgentNode, cHubNode, cFuncNode, cAgentNodeSimple, cMarketNode
from model.nodes.classes.Task import cTask, cDelivery
from model.nodes.classes.AbstEconNode import cNodeClientSupplyLine
from model.nodes.ProcessMonitor import cProcessMonitor
from model.nodes.classes.Market_model import cClient, cAgreement, cMarketPlace

def Test1():
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

    return the_model

def Test2():
    """
    Modeling wrong use of 1to1 port
    """
    the_model = cNodeFieldModel()
    node1 = cAgentNodeSimple('Matflow')
    node2 = cAgentNodeSimple('MatEat1')
    node3 = cAgentNodeSimple('MatEat2')
    # this will cause error
    node1.connect_buddies([node2, node3])

    node2.connect_buddies([node1])
    node3.connect_buddies([node1])

    MatFlow_items = [cDelivery('matflow1', urgent=True, start_time=15), cDelivery('matflow2', start_time=11)]
    node1.set_tasks(MatFlow_items)

    the_model.addNodes([node1, node2, node3])

    return the_model

def Test3():
    the_model = cNodeFieldModel()
    node1 = cAgentNodeSimple('Matflow')
    node2 = cAgentNodeSimple('MatEat1')
    node3 = cAgentNodeSimple('MatEat2')
    node4 = cHubNode('CondNode')

    node1.connect_buddies([node4])
    node2.connect_buddies([node4])
    node3.connect_buddies([node4])
    node4.connect_nodes(inp_nodes=[node1], out_nodes=[node2, node3])

    MatFlow_items = [cDelivery('matflow1', urgent=True, start_time=15), cDelivery('matflow2', start_time=11)]
    node1.set_tasks(MatFlow_items)

    cond_dict = {node2: 'urgent = True',
                 node3: 'start_time < 12'}
    node4.condition(cond_dict)

    the_model.addNodes([node1, node2, node3, node4])

    return the_model

def Test4():
    """
    Introducing random condition to Hub node
    """
    the_model = cNodeFieldModel()
    node1 = cAgentNodeSimple('Matflow')
    node2 = cAgentNodeSimple('MatEat1')
    node3 = cAgentNodeSimple('MatEat2')
    node4 = cHubNode('CondNode')

    node1.connect_buddies([node4])
    node2.connect_buddies([node4])
    node3.connect_buddies([node4])
    node4.connect_nodes(inp_nodes=[node1], out_nodes=[node2, node3])

    MatFlow_items = [cDelivery('matflow1', urgent=True, start_time=15), cDelivery('matflow2', start_time=11),
                     cTask('UrgentInfo', urgent=True), cDelivery('matflow6', urgent=True)]
    node1.set_tasks(MatFlow_items)

    node4.condition(randomize=True)

    the_model.addNodes([node1, node2, node3, node4])

    return the_model

def Test5():
    the_model = cNodeFieldModel()
    node1 = cAgentNodeSimple('Matflow')
    node2 = cAgentNodeSimple('MatEat1')
    node3 = cAgentNodeSimple('MatEat2')
    node4 = cMarketNode('MarketNode')

    node1.connect_buddies([node4])
    node2.connect_buddies([node4])
    node3.connect_buddies([node4])
    node4.connect_nodes(inp_nodes=[node1, node2, node3], out_nodes=[node1, node2, node3])

    MatFlow_items = [cDelivery('matflow1', urgent=True, start_time=15),
                     cDelivery('matflow2', bid=True, entity='Wood', volume=12, price=80, start_time=11),
                     cDelivery('matflow99', bid=True, entity='GLASS', volume=14, price=80, start_time=11),
                     cDelivery('matflow6', urgent=True)]
    node1.set_tasks(MatFlow_items)

    MatFlow_items2 = [cTask('UrgentInfo', ask=True, entity='Wood', volume=5, price=70, urgent=True)]
    node2.set_tasks(MatFlow_items2)

    MatFlow_items3 = [cTask('UrgentInfo56', ask=True, entity='GLASS', volume=7, price=70, urgent=True)]
    node3.set_tasks(MatFlow_items3)

    the_model.addNodes([node1, node2, node3, node4])

    return the_model

def Test6():
    """
    Test, simulating Client-Agreement-Market relations.
    Client generate 2 good requests , then another 2 on callbacks.
    Market randomly deliver good to Client as answer to request.
    """
    the_model = cNodeFieldModel()
    node1 = cClient('ROZNICHNIY CLIENT')
    node2 = cAgreement('DOGOVOR')
    node3 = cMarketPlace('TORGOVAYA TOCHKA')
    node4 = cHubNode('KUDA POSILAEM')

    node1.connect_node(node2)
    node2.connect_node(node4)
    node4.connect_nodes2(inp_nodes=[node2], out_nodes=[node1, node3])
    # node3.connect_node(node4)
    node3.connect_node(node2)

    cond_dict = {node1: 'urgent = True',
                 node3: 'urgent = False'}
    node4.condition(cond_dict)

    the_model.addNodes([node1, node2, node3, node4])

    return the_model


if __name__ == '__main__':
    import lg
    #WL = ['DEVS.cClient', 'DEVS.cShop', 'DEVS.cAgreement', 'DEVS.cHubNode']
    lg.config_logging(tofile='logs/test.log',
                      whitelist = None,
                      level=lg.logging.DEBUG)
    #lg.config_logging(tofile='logs/test.log', level = lg.logging.DEBUG)
    # from model.nodes.classes.ClientShopSupplier import test1
    from model.nodes.classes.ClientShopSupplier_modernTasks import test1

    the_model = test1()
    the_model.build_json()

    loganddata, runner = the_model.run_sim(datetime.date(2016, 3, 15), until=25, seed=555, debug=True)

    # Plot processes
    # pm = cProcessMonitor(runner.system.simpy_env, until=25)
    # #print(id(runner.system.simpy_env))
    # pm.plot_procs_groups()
    # pm.plot_event_density()
    # pm.print_process()

    import matplotlib
    for obs_name, var_name in runner.sim_results.get_available_names():
        data_frame = runner.sim_results.get_dataframe_for_epochvar(obs_name, var_name)
        print(data_frame)
    #     data_frame.plot()
    # matplotlib.pyplot.show()


