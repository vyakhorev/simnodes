"""
    The model class basically just holds a bunch of data variables and some minimal logic
    for exposing and announcing changes to this data.
    This model shouldn't be confused with the Qt model
"""

import datetime

from model.nodes.node_model import cNodeModel

class cNodeFieldModel():
    # TODO: all interaction with nodes creation / managing / coordinates / color is here
    """
        Facade for devs - connecting it to gui, making it easy to handle, automating creation of new nodes.
    """

    def __init__(self):
        self.NodeSystem = cNodeModel()  # the structure itself is there, not the coordinates

    def addNodes(self, nodes):
        self.NodeSystem.addNodes(nodes)

    def addObserver(self, new_oberver):
        self.NodeSystem.addObserver(new_oberver)

    def addOtherSimObj(self, new_obj):
        # test purposes
        self.NodeSystem.addOtherSimObj(new_obj)

    def run_sim(self, start_date=None, until=100, seed = None, debug=False):
        # There may be more logic here
        if start_date is None:
            start_date = datetime.date.today()
        sim_results = self.NodeSystem.run_sim(start_date=start_date, sim_until=until, seed=seed, debug=debug)
        return sim_results

    def getNodes(self):
        # TODO: make it iterable, do not copy the list with return
        # TODO: '.parent' is gone, we need a new structure
        """
            Method, called by controller sending list of nodes
        """
        print(self.NodeSystem.getNodesList())
        return self.NodeSystem.getNodesList()

    def build_json(self):
        # grabbing json from two nodes representations
        # for nd in getNodes:
        #     nd._json()
        #
        pass
