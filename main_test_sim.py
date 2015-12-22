import datetime

from model.model import cNodeFieldModel

from model.nodes.classes.AbstEconNode import cItemConsumer, cItemGenerator
# from model.nodes.classes._old.NodeEconAgent import cNodeEconAgent


if __name__ == '__main__':
    # Create a model, run simulation, print log + iterate over nodes
    the_model = cNodeFieldModel()

    # Variant 2
    consumer = cItemConsumer('hungry_man')
    consumer.set_cons_conv('food', 'energy', 0.5, 10, 1)
    consumer.spawn_item('money', 100)
    consumer.spawn_item('food', 10)

    producer = cItemGenerator('food_factory')
    producer.set_prod_conv('money', 'food', 2, 50, 5)
    producer.spawn_item('money', 100)
    producer.spawn_item('food', 10)

    consumer.connect_other_node(producer)

    the_model.addNodes([consumer, producer])

    # # Variant 1
    # ea1 = cNodeEconAgent('econagent1')
    # ea2 = cNodeEconAgent('econagent2')
    # ea1.connect_buddies([ea2])
    # ea1.send_msg()
    # the_model.addNodes([ea1, ea2])

    print('********************************')
    print('********START SIMULATION********')
    print('********************************')
    loganddata, runner = the_model.run_sim(datetime.date(2015, 11, 15), until=100, seed=555)

    """
    log = loganddata['log_list']

    for obs_name, var_name in runner.sim_results.get_available_names():
        data_frame = runner.sim_results.get_dataframe_for_epochvar(obs_name, var_name)
        data_frame.plot()
        print(data_frame)
    matplotlib.pyplot.show()
    """
