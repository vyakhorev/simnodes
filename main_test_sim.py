import datetime

from model.model import cNodeFieldModel
from model.nodes.classes._old.NodeEconAgent import cNodeEconAgent
from model.nodes.classes.Node_func import cNone_func, cNone_agent, cNone_hub
from model.nodes.classes.AbstEconNode import cNodeClientSupplyLine


if __name__ == '__main__':
    # Create a model, run simulation, print log + iterate over nodes

    the_model = cNodeFieldModel()
    #
    # client1_supply_line = cNodeClientSupplyLine("client1")
    # client1_supply_line.add_supply_line("apples", 5, 10, 1)
    # client1_supply_line.add_supply_line("bread", 10, 1, 3)
    #
    # client2_supply_line = cNodeClientSupplyLine("client2")
    # client2_supply_line.add_supply_line("apples", 5, 11, 2)
    # client2_supply_line.add_supply_line("bread", 10, 1, 4)
    # client2_supply_line.add_supply_line("pizza", 50, 1, 5)

    '''
    node1 = cNodeEconAgent('node1')
    node2 = cNodeEconAgent('node2')
    node3 = cNodeEconAgent('node3')
    node1.connect_buddies([node2, node3])
    node2.connect_buddies([node3])
    # node2.send_msg()

    node1.send_msg_to(node3)
    node3.send_msg_to(node1)
    node2.send_msg_to(node3)
    the_model.addNodes([node1, node2, node3])
    '''

    # example
    # consumer = cItemConsumer('hungry_man')
    # consumer.set_cons_conv('food', 'energy', 0.5, 10, 1)
    # consumer.spawn_item('money', 100)
    # consumer.spawn_item('food', 10)
    #
    # producer = cItemGenerator('food_factory')
    # producer.set_prod_conv('money', 'food', 2, 50, 5)
    # producer.spawn_item('money', 100)
    # producer.spawn_item('food', 10)
    #
    # consumer.connect_other_node(producer)
    #
    # the_model.addNodes([consumer, producer])

    node1 = cNone_agent('MatFlow')
    node2 = cNone_hub('CondNode')
    node3 = cNone_func('ApplyPrice1')
    node4 = cNone_func('ApplyPrice2')

    node2.connect_nodes(inp_node=node1, out_nodes=[node3, node4])
    # node2.connect_buddies([node1, node3, node4])

    the_model.addNodes([node1, node2, node3, node4])

    node1.activate()
    node2.condition(urgent=node3, nonurgent=node4)
    node2.activate()
    # node1.send_msg_to(node2)
    # node2.send_msg_to(node4)
    # node2.send_msg_to(node3)

    print('********************************')
    print('********START SIMULATION********')
    print('********************************')
    loganddata, runner = the_model.run_sim(datetime.date(2016, 3, 15), until=25, seed=555)

    """
    log = loganddata['log_list']

    for obs_name, var_name in runner.sim_results.get_available_names():
        data_frame = runner.sim_results.get_dataframe_for_epochvar(obs_name, var_name)
        data_frame.plot()
        print(data_frame)
    matplotlib.pyplot.show()
    """
