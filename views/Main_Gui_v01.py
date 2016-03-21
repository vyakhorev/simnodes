"""
    The view class(es) should contain the minimal logic required to connect to the signals coming from the widgets in your layout.
    View events can call and pass basic information to a method in the view class and onto a method in a controller class,
    where the heavier logic will be.
"""

# Pyqt5
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Utils
import sys
import math
from random import randint
# generated views
from views.gen.Main_Gui_v02_draft import Ui_MainWindow
from views.Node_dialog import AgentNodeWindow, HubNodeWindow, FuncNodeWindow


class c_MainView(QMainWindow):
    i = 0

    # properties to read/write widget value
    # Kinda this:
    # @property
    # def running(self):
    #     return self.ui.pushButton_running.isChecked()
    # @running.setter
    # def running(self, value):
    #     self.ui.pushButton_running.setChecked(value)

    def __init__(self, model):

        # instance of model
        self.model = model

        # Gui constructor
        super(c_MainView, self).__init__()

        # building windows
        self.build_ui()

        # register func with model for future model update announcements
        # if you have complicated logic, not simple Qabstract model
        # self.model.subscribe_update_func(self.update_ui_from_model)

    def build_ui(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Create a main application window with buttons
        # view = c_Baseview()

        # connect signal to method
        self.ui.butQuit.clicked.connect(self.close)

        # self.ui.pushButton_running.clicked.connect(self.on_running)

    def set_scene(self, scene):
        self.ui.mainView.setScene(scene)

    def new_tab(self, nodename, WGtype=QWidget):
        # todo Make tabs container, make tab singleton ?
        self.tab1 = WGtype

        self.ui.wgMain.addTab(self.tab1, nodename)

    def open_node_window(self, node):
        if node.node_id.startswith('cHubNode'):
            new_modal = HubNodeWindow(self, node)
        elif node.node_id.startswith('cAgentNode'):
            new_modal = AgentNodeWindow(self, node)
        elif node.node_id.startswith('cFuncNode'):
            new_modal = FuncNodeWindow(self, node)

        new_modal.setWindowFlags(Qt.Window)
        new_modal.setWindowModality(Qt.WindowModal)
        new_modal.open_node()
        return new_modal

    def connectSignals(self, main_ctrl):
        self.i += 1
        if self.i >= 2:
            print('Cant connecnt many times! {}'.format(self.i))
        self.ui.butAddnode.clicked.connect(lambda: main_ctrl.addNode('AgentType'))
        self.ui.butConnect.clicked.connect(main_ctrl.connection)
        # FIXME will raise error
        self.ui.butParam.setObjectName('Export')
        self.ui.butParam.clicked.connect(main_ctrl.export_scene)
        self.ui.butOpen.clicked.connect(main_ctrl.open_file)

        self.ui.butRunSim.clicked.connect(main_ctrl.run_current_proj)

        # setting up context menu
        self.ui.mainView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.mainView.customContextMenuRequested.connect(main_ctrl.openContextMenu)

    def wheelEvent(self, event):
        """
            managing Viewer zooming in and out
        """
        print('Wheel acting !!!  x: {0},  y: {1}'.format(event.angleDelta().x(), event.angleDelta().y()))
        delta = event.angleDelta().y()
        factor = 1.35 ** (delta / 240.0)
        self.ui.mainView.scale(factor, factor)

    # =====================================================

    def on_running(self):
        self.main_ctrl.change_running(self.running)

    def update_ui_from_model(self):
        self.running = self.model.running


