import pytest
from model.nodes.wallet2 import DumbNode, cWallet

def test_1(env):
    assert 1 == 1

def test_random_actions_to_wallet():
    import datetime
    from model.model import cNodeFieldModel

    the_model = cNodeFieldModel()
    wal_a = cWallet('wal_a')
    wal_a.spawn_pile('rubles', 100)

    test_obj = DumbNode(name='test_obj')
    assert wal_a.res_all['rubles'].value.proxyLevel == 100
    test_obj.get_goods(wal_a, 'rubles', qtty=60, when=5)
    test_obj.get_goods(wal_a, 'rubles', qtty=80, when=7)
    test_obj.place_goods(wal_a, 'plumbum_ingots', qtty=130, when=14)

    # the_model.addNodes([wal_a, wal_b])
    the_model.addOtherSimObj(wal_a)

    test_objs = DumbNode.ALL_DumbNode
    # shuffle order
    for nd in test_objs:
        the_model.addOtherSimObj(nd)

    the_model.run_sim(datetime.date(2016, 5, 2), until=25, seed=555, debug=True)

    assert len(wal_a.res_all) == 2
    assert wal_a.res_all['rubles'].value.level == 40
    print(wal_a.res_all['plumbum_ingots'].items_store.items)
    assert len(wal_a.res_all['plumbum_ingots'].items_store.items) == 130

def test_pile_add_and_consume():
    import datetime
    from model.model import cNodeFieldModel

    the_model = cNodeFieldModel()
    wal_a = cWallet('wal_a')
    wal_a.spawn_pile('rubles', 100)

    test_obj = DumbNode(name='test_obj')

    test_obj.get_goods(wal_a, 'rubles', qtty=60, when=5)
    test_obj.get_goods(wal_a, 'rubles', qtty=80, when=7)
    test_obj.place_to_pile(wal_a, 'rubles', qtty=70, when=9)
    test_obj.get_goods(wal_a, 'rubles', qtty=90, when=9)
    test_obj.place_to_pile(wal_a, 'rubles', qtty=70, when=9)
    assert wal_a.res_all['rubles'].value.proxyLevel == 100

    the_model.addOtherSimObj(wal_a)

    test_objs = DumbNode.ALL_DumbNode
    # shuffle order
    for nd in test_objs:
        the_model.addOtherSimObj(nd)

    the_model.run_sim(datetime.date(2016, 5, 2), until=25, seed=555, debug=True)

    assert wal_a.res_all['rubles'].value.level == 10

# if you want run manually
# modes :
#   -v  verbose
#   -rw read pytest warnings
#   -x stop after 1st failture
#   -l show local variables

# if __name__ == '__main__':
#    pytest.main('-v')