"""
    The controller class does the real logic, and passes on data to the model.
    You could combine the views/controllers, but it sounds like that's what you're trying to avoid.
"""

# Pyqt5
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Utils
import math
import sys
from random import randint
from views.Main_Gui_v01 import c_MainView
from model.model import cNodeFieldModel
from open_file import open_nodes, run_sim

from model.nodes.classes.Task import cTask, make_task_from_str
from model.nodes.utils import project_parser
from model.nodes.classes.Node_func_v2 import cAgentNode, cHubNode, cFuncNode, cAgentNodeSimple, cMarketNode, \
                                            node_types_dict
from views.Node_dialog import AgentNodeWindow

import datetime
from pprint import pprint

# Workaround to get exceptions from Qt
sys._excepthook = sys.excepthook

def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


class c_BaseNodes():
    """
        Base controller class, which take a handle on both model view.
        First , its instancing Scene object from Pyqt5
        Then making signals-slots connections and starting node assembler
    """
    SIM_RUNS_TOTAL = 0

    def __init__(self, model, main_view):

        self.model = model
        self.view = main_view
        # Main node assembling logic TBH

        # Create a QGraphicsScene object, which holds nodes and others
        self.Nodegraph = c_NodeGraph()

        # Linking signals to controller
        self.view.connectSignals(self)
        self.Nodegraph.node_doubletapped.connect(self.on_double_clicked)
        # self.Nodegraph.nodegraph_rightclick.connect(self.on_right_click)


        self.set_scene(self.Nodegraph)

        self.nodes_gui = []

        # Data logic START ===========
        # current project
        self.current_proj = self.model

        # self.assembler = c_nodeAssembler(model)
        # print(self.assembler)
        # Drawing nodes on screen
        # self.assembler.draw(self.Nodegraph)
        # =============================

    def open_new_tab(self):
        focused = self.Nodegraph.focusItem()
        print(focused)
        self.view.new_tab()

    def addNode(self, nodetype=None):
        color_map = {'AgentType': 'blue', 'FuncType': 'green', 'HubType': 'orange'}
        # nodetype = 'HubType'
        if nodetype in ['AgentType', 'FuncType', 'HubType']:
            newnode = node_types_dict[nodetype](name=str(nodetype))
            # Rename with index
            newnode.name += str(newnode._nodeid)
            node_wind = self.view.open_node_window(newnode)
            self.model.addNodes([newnode])

        else:
            raise TypeError('Unknown node type!')

        newnode.gui_repr = self.Nodegraph.addNode(name=newnode.name, model_repr=newnode)
        newnode.gui_repr.set_Color(color_map[nodetype])

        print('ADDING NODE to MODEL {}'.format(newnode.gui_repr))
        self.nodes_gui += [newnode.gui_repr]

    def editNode(self, node):
        node_wind = self.view.open_node_window(node)

    def connection(self):
        self.Nodegraph.connection()

    def export_scene(self):
        # delegate nodes to model
        self.model.add_nodes_gui(self.nodes_gui)
        self.model.build_json()

    def set_scene(self, scene):
        self.scene = scene
        self.view.set_scene(self.scene)

    def openContextMenu(self, position):
        mapped_pos = self.view.mapToGlobal(QPoint(position)+QPoint(21, 62))
        menu = ContexMenu(mapped_pos)
        # setting actions
        slotAgentLambda = lambda: self.addNode('AgentType')
        menu.make_action(meth=slotAgentLambda, string='AgentNode')
        slotFuncLambda = lambda: self.addNode('HubType')
        menu.make_action(meth=slotFuncLambda, string='HubNode')
        slotAgentLambda = lambda: self.addNode('FuncType')
        menu.make_action(meth=slotAgentLambda, string='FuncNode')
        menu.run()

    def resetNodeGraph(self):
        """
        Reset NodeGraph
        """
        # TODO check if old c_NodeGraph instance deleted
        print('RESET NODEGRAPH')
        self.Nodegraph = c_NodeGraph()

        # Linking signals to controller
        self.Nodegraph.node_doubletapped.connect(self.on_double_clicked)
        self.set_scene(self.Nodegraph)
        return True

# Working with projects
# ==================================================================
    def open_project(self):
        """
        mocking file opening
        """
        self.project_model = open_nodes()
        self.current_proj = self.project_model
        self.assembler = c_nodeAssembler(self.project_model)
        self.resetNodeGraph()
        self.assembler.draw(self.Nodegraph)

    def open_file(self):
        file_string = 'new_way/proj_file_4_agents.json'
        data = project_parser.parse_json(file_string)
        Cg = project_parser.CodeGenerator(data)
        nodes = Cg.make_objects()
        Cg.connect_between(nodes)
        Cg.setup_conditions(nodes)
        Cg.convert_alias_to_nodeclass(nodes)
        Cg.color_maping(nodes)

        self.model.addNodes(nodes)

        self.current_proj = self.model
        self.assembler = c_nodeAssembler(self.current_proj)
        self.resetNodeGraph()
        self.assembler.draw(self.Nodegraph)

    def run_current_proj(self):
        # FOR TEST JSON EXPORT ONLY
        self.export_scene()

        self.SIM_RUNS_TOTAL += 1
        print('Going run simulation')
        run_sim(self.current_proj)
        print('Simulations number : {}'.format(self.SIM_RUNS_TOTAL))
        # clear task monitor from old tasks
        if cTask:
            cTask.tm.reset_task_monitor()

# ==================================================================

    # called from view class
    def change_running(self, checked):
        # put control logic here
        self.model.running = checked
        self.model.announce_update()

    @pyqtSlot()
    def on_double_clicked(self, node):
        """
            Slot which activated by doubletapping QGscene at any place
        """
        print('i managed to get signal from !!!' + str(node))
        self.editNode(node.model_repr)

    @pyqtSlot()
    def on_right_click(self, pos):
        print('RIGHT Click Pos :', pos)
        self.view.menu(pos)

# QGraphics objects/classes here
# ================================================================= #
class c_NodeGraph(QGraphicsScene):
    """
        main GraphScene
    """
    # Custom signals
    node_doubletapped = pyqtSignal(object)
    nodegraph_rightclick = pyqtSignal(object)

    def __init__(self):
        self.elements = []
        super(c_NodeGraph, self).__init__()
        # self.x_coor, self.y_coor = randint(1, 100), randint(1, 100)

    def addNode(self, name='Blank', px=100, py=100, model_repr=None):
        print('1111111111111111')
        item = c_Node(name, model_repr)
        print('2222222222222222')
        self.elements += [item]
        # Random placing
        # self.x_coor, self.y_coor = randint(1, 100), randint(1, 100)
        self.x_coor, self.y_coor = px, py

        # Place nodes
        item.my_setPos(self.x_coor, self.y_coor)
        # Make ports
        delta = (item.get_node_dim()[0])/2
        self.addPort(item, delta, 0)
        super(c_NodeGraph, self).addItem(item)

        print('placed Node in {0},{1} and port at {0},{1}'.format(self.x_coor, self.y_coor, self.x_coor+delta,
                                                                  self.y_coor))
        return item

    def addPort(self, patient, x, y):
        port = c_Port()

        port.my_setPos(x, y)
        print('adding PORT in {0},{1}'.format(x, y))
        super(c_NodeGraph, self).addItem(port)
        # Parenting to Node
        port.setParentItem(patient)

    def connection(self, node1=None, node2=None):

        for obj in self.selectedItems():
            print(obj.name)

        if node1 is not None:
            print('o.o'*25)
            Con = c_ConLine(node1, node2)
            self.addItem(Con)
            return

        if len(self.selectedItems()) < 2:
            #TODO make error handle
            print('Non enough selected nodes')
            return

        if len(self.selectedItems()) > 2:
            #TODO make error handle
            print('Too much selected nodes')
            return

        # Connect in model
        # FIXME connection between agent and hub
        self.selectedItems()[0].model_repr.connect_buddies([self.selectedItems()[1].model_repr])
        self.selectedItems()[1].model_repr.connect_buddies([self.selectedItems()[0].model_repr])

        # Connect in GUI
        Con = c_ConLine(self.selectedItems()[0], self.selectedItems()[1])
        print('made con line, going to add')
        self.addItem(Con)

    # QGraphicsSceneMouseEvent
    def mouseMoveEvent(self, event):
        # print('scenePos : ' + str([event.scenePos().x(), event.scenePos().y()]))
        # print('screenPos : ' + str([event.screenPos().x(), event.screenPos().y()]))

        super(c_NodeGraph, self).mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
            Emitting custom signal when Qscene double-tapped
        """
        self.this_node = self.focusItem()
        # send focused item
        if hasattr(self.this_node, 'setPos'):
            self.node_doubletapped.emit(self.this_node)
        else:
            print('You didnt hit a node!')

    # Right-click contex menu

    def contextMenuEvent(self, event):
        # pprint(event.__dir__())
        posx, posy = event.scenePos().x(), event.scenePos().y()
        print('Right Mouse Click @ x:{} y:{}'.format(posx, posy))

        # self.nodegraph_rightclick.emit(QPoint(posx, posy))

    def __repr__(self):
        return 'elements :  ' + str(self.elements)


class c_Node(QGraphicsRectItem):
    """
        Node base class
    """
    def __init__(self, name, model_repr=None):
        super(c_Node, self).__init__()
        self.width = 160
        self.height = 100
        self.name = name
        # class from model
        self.model_repr = model_repr

        self.ConList = []


        # Properties
        self.setFlags(self.ItemIsSelectable |
                      self.ItemIsMovable |
                      self.ItemIsFocusable |
                      self.ItemSendsScenePositionChanges
                      )

        # Cursor style
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # Label
        self.label = QGraphicsTextItem(self.name, self)
        self.label.setFont(QFont("Times", 16, QFont.Bold))

        self.setRect(0, 0, self.width, self.height)
        # self.setPos(self.width, self.height)

    # May be usefull
    # def itemChange(self, change, variant):
    #     super(c_Node, self).itemChange(change, variant)
    #     if change == QGraphicsItem.ItemScenePositionHasChanged:
    #         self.setParentItem(None)
    #     return QGraphicsItem.itemChange(self, change, variant)

    def my_setPos(self, x, y):

        self.setPos(x, y)

        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (self.width - lw) / 2
        ly = (self.height - lh) / 2
        self.label.setPos(lx, ly)

    @property
    def myPos(self):
        return self.pos()

    def get_node_dim(self):
        return self.width, self.height

    # def paint(self, painter, option, widget):
    #     try:
    #         self.setBrush(QBrush=Qt.red)
    #         super(c_Node, self).paint(self, painter, option, widget)
    #     except Exception as e:
    #         print(e)

    def set_Color(self, color):
        gradient = QLinearGradient(self.width/2, 0, self.width/2, self.height)

        if color.lower() == 'green':
            qtcolor = QColor(84, 192, 58)
        if color.lower() == 'blue':
            qtcolor = QColor(36, 80, 144)
        if color.lower() == 'orange':
            qtcolor = QColor(250, 155, 100)

        gradient.setColorAt(0, qtcolor)
        gradient.setColorAt(1, qtcolor.darker(160))
        Brush = QBrush(gradient)
        self.setBrush(Brush)

    def addCon(self, Con_nodes):
        self.ConList.append(Con_nodes)
        Con_nodes.adjust()

    # Capture node movement
    def itemChange(self, change, value):
        # print('Itemchange Callback')

        if change == QGraphicsItem.ItemPositionChange:
            for con in self.ConList:
                #print('{0} redrawing'.format(con))
                con.adjust()
        return QGraphicsItem.itemChange(self, change, value)

    def _json(self):
        attrs_to_save = ['myPos', 'name', 'model_repr']
        serializables = []

        for attr_i in attrs_to_save:
            try:
                serializables += [getattr(self, attr_i)]
            except AttributeError as e:
                print(e)
        return serializables


class c_Port(QGraphicsEllipseItem):
    """
        Port base class
    """

    def __init__(self):
        super(c_Port, self).__init__()
        self.setCursor(QCursor(Qt.ClosedHandCursor))
        self.setBrush(QBrush(Qt.blue))

        self.name = "port"

        self.dim = QRectF(0, 0, 10, 10)
        self.setRect(self.dim)

    def my_setPos(self, x, y):
        self.setPos(x, y)

    def get_port_dim(self):
        """
            getting ports
            (float)(float)(float)(float)
        """
        return self.dim.getCoords()


class c_ConLine(QGraphicsLineItem):

    Pi = math.pi
    TwoPi = 2.0 * Pi

    def __init__(self, sourceNode, destNode):
        super(c_ConLine, self).__init__()

        print('init start')
        self.arrowSize = 5.0
        self.sourcePoint = QPointF()
        self.destPoint = QPointF()

        self.setAcceptedMouseButtons(Qt.NoButton)
        self.source = sourceNode
        self.dest = destNode

        self.source.addCon(self)
        self.dest.addCon(self)

        self.adjust()
        print('arrow initlized')

    def sourceNode(self):
        return self.source

    def setSourceNode(self, node):
        self.source = node
        self.adjust()

    def destNode(self):
        return self.dest

    def setDestNode(self, node):
        self.dest = node
        self.adjust()

    def adjust(self):
        if not self.source or not self.dest:
            return

        line = QLineF(self.mapFromItem(self.source, self.source.width/2, 3),
                self.mapFromItem(self.dest, self.dest.width/2, -3))
        #print('map from {0} item : {1}'.format(self.source, self.mapFromItem(self.source, 0, 0)))
        #print('map from {0} item : {1}'.format(self.dest, self.mapFromItem(self.dest, 0, 0)))
        length = line.length()

        self.prepareGeometryChange()

        if length > 20.0:
            edgeOffset = QPointF((line.dx() * 10) / length,
                    (line.dy() * 10) / length)

            self.sourcePoint = line.p1() + edgeOffset
            self.destPoint = line.p2() - edgeOffset
        else:
            self.sourcePoint = line.p1()
            self.destPoint = line.p1()

    def boundingRect(self):
        if not self.source or not self.dest:
            return QRectF()

        penWidth = 1.0
        extra = (penWidth + self.arrowSize) / 2.0

        return QRectF(self.sourcePoint,
                QSizeF(self.destPoint.x() - self.sourcePoint.x(),
                        self.destPoint.y() - self.sourcePoint.y())).normalized().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget):
        if not self.source or not self.dest:
            return

        # Draw the line itself.
        line = QLineF(self.sourcePoint, self.destPoint)

        if line.length() == 0.0:
            return

        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap,
                            Qt.RoundJoin))
        painter.drawLine(line)


        # Draw the arrows if there's enough room.
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = c_ConLine.TwoPi - angle
        sourceArrowP1 = self.sourcePoint + QPointF(math.sin(angle + c_ConLine.Pi / 3) * self.arrowSize,
                                                   math.cos(angle + c_ConLine.Pi / 3) * self.arrowSize)
        sourceArrowP2 = self.sourcePoint + QPointF(math.sin(angle + c_ConLine.Pi - c_ConLine.Pi / 3) * self.arrowSize,
                                                   math.cos(angle + c_ConLine.Pi - c_ConLine.Pi / 3) * self.arrowSize);
        destArrowP1 = self.destPoint + QPointF(math.sin(angle - c_ConLine.Pi / 3) * self.arrowSize,
                                               math.cos(angle - c_ConLine.Pi / 3) * self.arrowSize)
        destArrowP2 = self.destPoint + QPointF(math.sin(angle - c_ConLine.Pi + c_ConLine.Pi / 3) * self.arrowSize,
                                               math.cos(angle - c_ConLine.Pi + c_ConLine.Pi / 3) * self.arrowSize)

        painter.setBrush(Qt.black)
        painter.drawPolygon(QPolygonF([line.p1(), sourceArrowP1, sourceArrowP2]))
        #painter.drawPolygon(QPolygonF([line.p2(), destArrowP1, destArrowP2]))

# ================================================================= #
# ===== Testing some Widgets here ================================= #

class NodeBaseWidget(QWidget):
    def __init__(self, node):
        super().__init__(None)
        # Got caller Node
        self.node = node

        # Setting up layout
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(2)

        label = QLabel(self.node.name)
        label.setAlignment(Qt.AlignTop)
        self.layout().addWidget(label)

        # my_splitter = QSplitter()
        # self.layout().addWidget(my_splitter)


class FactoryWidget(NodeBaseWidget):
    def __init__(self, node):
        super().__init__(node)

        capacity = QLabel('capacity')
        people = QLabel('people')
        departments = QLabel('departments')
        # getting properties from model
        fields = {}
        for key, val in node.model_repr.__dict__.items():
            if key not in ['parent', 'name']:
                fields[QLabel(key)] = val

        for label, lineedit in fields.items():
            print(label, lineedit)
            label.setAlignment(Qt.AlignTop)
            label.setMinimumWidth(100)

            second_field = QLineEdit(str(lineedit))
            second_field.setMaximumWidth(650)

            self.small_horiz_widget = QHBoxLayout()
            self.small_horiz_widget.addWidget(label)
            self.small_horiz_widget.addWidget(second_field)

            self.hor_widget = QFrame()
            self.hor_widget.setMaximumWidth(800)
            self.hor_widget.setLayout(self.small_horiz_widget)

            self.layout().addWidget(self.hor_widget)

            # self.layout().addWidget(label)
            # self.layout().addWidget(QLineEdit(str(lineedit)))


class ClientWidget(NodeBaseWidget):
    def __init__(self, node):
        super().__init__(node)
        # print('orders : {}'.format(node.model_repr.orders))
        label1 = QLabel(str(node.model_repr.orders))
        label1.setAlignment(Qt.AlignTop)
        self.layout().addWidget(label1)


# ================================================================= #
# Context Menu
class ContexMenu(QMenu):
    def __init__(self, position):
        super().__init__()
        self.position = position

    def run(self):
        self.exec_(self.position)


    def make_action(self, meth, string):
        """
        :param meth: method connected to
        :param string: text displaying in menu
        """
        print('OLA')
        self.new_action = self.addAction(string)
        self.new_action.triggered.connect(meth)





# Processing a model
# ================================================================= #
class c_nodeAssembler():

    def __init__(self, model):
        self.Tree = model

    def draw(self, Nodegraph):
        """
            Method, which grabs nodes from the model , put random positions on ones
            and draw them in the scene
        """
        # print(self.Tree.getTree())
        print('2nd method ', self.Tree.getNodes())
        # for node in self.Tree.getTree():
        # rootNode = None
        datamodel_viewmodel_dict = {}

        for node in self.Tree.getNodes():
            some_node = c_Node(node.name, node)
            # print(node.name)
            datamodel_viewmodel_dict[node.name] = some_node
            some_node.my_setPos(100+randint(-300, 300), 100+randint(2, 4)*120)
            try:
                some_node.set_Color(node.color)
            except Exception as e:
                print('!!!!!!!', e)
            Nodegraph.addItem(some_node)

        for node in self.Tree.getNodes():
            if hasattr(node, 'parent'):
                if isinstance(node.parent, list):
                    for par_i in node.parent:
                        Con = Nodegraph.connection(node2=datamodel_viewmodel_dict[par_i.name],
                                                   node1=datamodel_viewmodel_dict[node.name])
                        Nodegraph.addItem(Con)
                else:
                    try:
                        Con = Nodegraph.connection(node2=datamodel_viewmodel_dict[node.parent.name],
                                                   node1=datamodel_viewmodel_dict[node.name])
                        Nodegraph.addItem(Con)
                    except Exception as e:
                        print('[Exception] {}'.format(e))


if __name__ == '__main__':
    # Testing model w/o Gui
    file_string = 'C:/Ilua/SimNodes_git/simnodes/new_way/proj_file_4_agents.json'
    data = project_parser.parse_json(file_string)
    Cg = project_parser.CodeGenerator(data)
    nodes = Cg.make_objects()
    Cg.connect_between(nodes)
    Cg.setup_conditions(nodes)
    Cg.convert_alias_to_nodeclass(nodes)
    model = cNodeFieldModel()

    model.addNodes(nodes)

    loganddata, runner = model.run_sim(datetime.date(2016, 3, 15), until=25, seed=555, debug=True)
