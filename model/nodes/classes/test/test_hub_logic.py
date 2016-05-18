from model.nodes.classes.ClientShopSupplier import cClient, cHubNode, cAgreement, RequestGoods, BaseTask
import datetime
import pytest


@pytest.fixture
def the_model():
    from model.model import cNodeFieldModel
    the_model = cNodeFieldModel()
    return the_model


@pytest.fixture
def nodes():
    # nodes
    node1 = cClient('Retail client')
    node2 = cHubNode('Filter hub')
    node3 = cClient('test_receiver')
    node4 = cAgreement('agr1')
    node5 = cAgreement('agr2')
    # connections
    node1.connect_node(node4)
    node4.connect_node(node2)
    node2.connect_nodes(inp_nodes=[node4, node5], out_nodes=[node1, node3])
    node5.connect_node(node2)
    node3.connect_node(node5)

    return [node1, node2, node3, node4, node5]


@pytest.fixture
def lg():
    import lg
    WL = ['DEVS.cClient', 'DEVS.cShop', 'DEVS.cAgreement', 'DEVS.cHubNode']
    lg.config_logging(whitelist=[WL[3]],
                      level=lg.logging.DEBUG)
    return lg


def test_hub1(the_model, nodes, lg):

    # set conditions to hub
    cond_dict = {nodes[0]: 'party = Client',
                 nodes[2]: 'party = Store'}

    nodes[1].condition(cond_dict)

    the_model.addNodes(nodes)

    # run
    loganddata, runner = the_model.run_sim(datetime.date(2016, 5, 16), until=25, seed=555, debug=True)

    # nodes[0].list_of_unknown_req.append(BaseTask('sss', runner.system.simpy_env))
    # print(node1.list_of_unknown_req)
    # print(node3.list_of_unknown_req)

    # check each element to be RequestGoods type
    assert all(isinstance(el, RequestGoods) for el in nodes[0].list_of_unknown_req)
    assert len(nodes[0].list_of_unknown_req) == 12


def test_hub2(the_model, nodes, lg):
    # set conditions to hub
    cond_dict = {nodes[0]: 'party = Store',
                 nodes[2]: 'party = Client'}

    nodes[1].condition(cond_dict)

    the_model.addNodes(nodes)

    # run
    loganddata, runner = the_model.run_sim(datetime.date(2016, 5, 16), until=25, seed=555, debug=True)

    # check each element to be RequestGoods type
    assert all(isinstance(el, RequestGoods) for el in nodes[2].list_of_unknown_req)
    assert len(nodes[2].list_of_unknown_req) == 12


def test_hub3(the_model, nodes, lg):
    # set conditions to hub
    cond_dict = {nodes[0]: 'party = 0',
                 nodes[2]: 'party = 1'}

    nodes[1].condition(cond_dict)

    the_model.addNodes(nodes)

    # run
    loganddata, runner = the_model.run_sim(datetime.date(2016, 5, 16), until=25, seed=555, debug=True)

    assert len(nodes[2].list_of_unknown_req) == 0


def test_hub4(the_model, nodes, lg):
    # set conditions to hub
    cond_dict = {nodes[0]: 'is_client = True',
                 nodes[2]: 'is_client = False'}

    nodes[1].condition(cond_dict)

    the_model.addNodes(nodes)

    # run
    loganddata, runner = the_model.run_sim(datetime.date(2016, 5, 16), until=25, seed=555, debug=True)

    # check each element to be RequestGoods type
    assert all(isinstance(el, RequestGoods) for el in nodes[0].list_of_unknown_req)
    assert len(nodes[0].list_of_unknown_req) == 12

# if __name__ == '__main__':
   # test_hub1(the_model, nodes, lg)
   # pytest.main('-v')