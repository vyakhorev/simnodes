import datetime

from model.model import cNodeFieldModel

# from model.nodes.classes import cItemConsumer, cItemGenerator


if __name__ == '__main__':
    # Create a model, run simulation, print log + iterate over nodes
    the_model = cNodeFieldModel()

    consumer = cItemConsumer('hungry man')
    consumer.set_cons_conv('food', 10, 1)
    consumer.spawn_item('money', 100)
    consumer.spawn_item('food', 10)

    producer = cItemConsumer('food factory')
    producer.set_prod_conv('food', 100, 5)
    producer.spawn_item('food', 50)
    producer.spawn_item('money', 200)

    producer.connect_other_node(consumer)

    the_model.addNodes([consumer, producer])


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
