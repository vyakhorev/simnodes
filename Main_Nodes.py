"""
    Would be responsible for instantiating each of the views, controllers,
    and the model (and passing the references between them).
"""
# Pyqt5
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Utils
import sys
# Mine
from model.model import cNodeFieldModel
from contrls.main_cntrl import c_BaseNodes
from views.Main_Gui_v01 import c_MainView


class c_App(QApplication):

    def __init__(self, sys_argv, model):
        super(c_App, self).__init__(sys_argv)
        if model:
            self.model = model
        else:
            self.model = cNodeFieldModel()
        self.main_view = c_MainView(self.model)
        self.main_cntrl = c_BaseNodes(self.model, self.main_view)

        self.main_view.show()


def run(model=None):
    app = c_App(sys.argv, model)
    sys.exit(app.exec_())

if __name__ == "__main__":

    app = c_App(sys.argv)
    sys.exit(app.exec_())


    #
    # app = QApplication(sys.argv)
    #
    # # Create a QGraphicsScene object, which holds nodes and others
    # Nodegraph = c_NodeGraph()
    #
    # # Create a main application window with buttons
    # view = c_Baseview()
    #
    # # Setting a scene to sceneviewer
    # view.set_scene(Nodegraph)
    #
    # # Making signals
    # view.butAddnode.clicked.connect(Nodegraph.addNode)
    # view.butConnect.clicked.connect(Nodegraph.connection)
    # #view.butConnect.clicked.connect(Nodegraph.addPort)
    #
    # # SHOW
    # view.show()
    #
    # sys.exit(app.exec_())