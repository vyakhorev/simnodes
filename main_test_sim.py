import datetime

from model.model import cNodeFieldModel
# from model.nodes.classes._old.NodeEconAgent import cNodeEconAgent
#from model.nodes.classes.AbstEconNode import cNodeClientSupplyLine


if __name__ == '__main__':
  
    the_model = cNodeFieldModel()
    
    # client1_supply_line = cNodeClientSupplyLine("client1")
    # client1_supply_line.add_supply_line("apples", 5, 10, 1)
    # client1_supply_line.add_supply_line("bread", 10, 1, 3)
    
    # client2_supply_line = cNodeClientSupplyLine("client2")
    # client2_supply_line.add_supply_line("apples", 5, 11, 2)
    # client2_supply_line.add_supply_line("bread", 10, 1, 4)
    # client2_supply_line.add_supply_line("pizza", 50, 1, 5)
    
    # client1_supply_line.connect_other_node(client2_supply_line)

    # the_model.addNodes([client1_supply_line, client2_supply_line])

    print('********************************')
    print('********START SIMULATION********')
    print('********************************')
    loganddata, runner = the_model.run_sim(datetime.date(2015, 11, 15), until=100, seed=555)


    # log = loganddata['log_list']

    # for obs_name, var_name in runner.sim_results.get_available_names():
        # data_frame = runner.sim_results.get_dataframe_for_epochvar(obs_name, var_name)
        # data_frame.plot()
        # print(data_frame)
    # matplotlib.pyplot.show()

