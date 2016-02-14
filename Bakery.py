# Test case with farmers, millers e.t.c.

from model.nodes.classes.AbstEconNode2 import cEconNode, cItemRequestRegularGenerator
from model.nodes.econresources import cItemsNamespace, cItem

def make_bakery_items_namespace():
    wheat = cItem('wheat', None)
    fresh_wheat = cItem('fresh_wheat', wheat)
    med_wheat = cItem('med_wheat', wheat)
    old_wheat = cItem('old_wheat', wheat)
    flour = cItem('flour', None)
    average_flour = cItem('average_flour', flour)
    extra_flour = cItem('extra_flour', flour)
    bread = cItem('bread', None)
    small_bread = cItem('small_bread', bread)
    med_bread = cItem('med_bread', bread)
    large_bread = cItem('large_bread', bread)
    itemspace = cItemsNamespace()
    itemspace.add_items([fresh_wheat, med_wheat, old_wheat,
                         average_flour, extra_flour, small_bread,
                         med_bread, large_bread])
    return itemspace

class cClientNode(cEconNode):
    # demands items with some periodicity
    def __init__(self, name):
        super().__init__(name)
    
    def init_sim(self):
        super().init_sim()
    
    def add_order_line(self, item, qtty, interval):
        daemon = cItemRequestRegularGenerator(item, qtty, interval)
        # we can automate daemon plug-in mechanics
        daemon.set_output_queue(self.resource_requests_out_queue)
        self.register_daemon(daemon)

class cSellerNode(cEconNode):
    # routes client demand for items, handles deals
    def 
    
class cFarmNode(cEconNode):

    def __init__(self, name):
        super().__init__(name)

    def init_sim(self):
        super().init_sim()
        
    
        
   