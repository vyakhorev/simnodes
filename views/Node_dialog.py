__author__ = 'User'
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from pprint import pprint

# Workaround to get exceptions from Qt
sys._excepthook = sys.excepthook


def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook



class NodeWindow(QtWidgets.QWidget):
    """
    Base window for node properties
    """

    def __init__(self, parent,  name='BaseNode'):
        super().__init__(parent)
        self.name = name

        self.initUI()

    def initUI(self):
        print('Initializating {}'.format(self))
        # Core layout
        self.widget_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.widget_layout)
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(0)
        self.resize(600, 400)
        self.setWindowTitle('Agent')

        # Main Frame
        self.main_frame = QtWidgets.QFrame(self)
        self.main_frame.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
        self.widget_layout.addWidget(self.main_frame)
        self.main_verticall_layout = QtWidgets.QVBoxLayout()
        self.main_verticall_layout.setContentsMargins(1, 1, 1, 1)
        self.main_verticall_layout.setSpacing(0)
        self.main_frame.setLayout(self.main_verticall_layout)

        # Sub layouts
        self.tab_layout = QtWidgets.QVBoxLayout()
        self.tab_layout.setContentsMargins(1, 1, 1, 1)
        self.tab_layout.setSpacing(0)
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.setContentsMargins(1, 1, 1, 1)
        self.buttons_layout.setSpacing(0)
        self.buttons_layout.setAlignment(QtCore.Qt.AlignRight)
        self.main_verticall_layout.addLayout(self.tab_layout)
        self.main_verticall_layout.addLayout(self.buttons_layout)

        # Properties tabs
        self.tab_menu = QtWidgets.QTabWidget(self)
        self.tab_layout.addWidget(self.tab_menu)
        # Create tab widget
        self.tab_widget = QtWidgets.QWidget(self)
        # TODO remove when styling will done
        # self.tab_menu.setStyleSheet("background-color: lightgrey; ")
        self.tab_menu.addTab(self.tab_widget, 'Properties')

        # Buttons
        buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)
        self.buttons_layout.addWidget(buttonbox)

    def __repr__(self):
        return '<{}> type of {}'.format(self.name, str(super().__repr__()))

    def open_node(self):
        # self.setWindowModality(QtCore.Qt.WindowModal)
        self.show()

    def accept(self):
        print('Ok pressed')
        self.close()
        raise NotImplementedError('accept method should implemented in child')

    def reject(self):
        print('Cancel pressed')
        self.close()
        raise NotImplementedError('reject method should implemented in child')

    def closeEvent(self, event):
        print('Close event!!')
        # pprint(dir(event))
        super().closeEvent(event)


class AgentNodeWindow(NodeWindow):
    def __init__(self, parent, name=None):
        super().__init__(parent)
        # adding more tabs

        if name:
            self.setWindowTitle(name)

        self.tab_widget_add = TabPropitiesWidget()
        # TODO dunno how to change widget on the fly...
        self.tab_menu.removeTab(0)
        self.tab_menu.addTab(self.tab_widget_add, 'Agent Properties')

    def load_attributes(self):
        pass

    def accept(self):
        attributes = self.tab_widget_add.get_values_iter()
        print('Set attributes : ')
        for label_i, linedit_i in attributes:
            print(label_i, linedit_i)
        self.close()

    def reject(self):
        self.close()


class TabPropitiesWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.attributes = []

        self.initUI()

    def initUI(self):
        self.setLayout(QtWidgets.QVBoxLayout())

        self.my_frame = QtWidgets.QFrame(self)

        # Generating label - textedit for attributes
        self.attributes_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel('Name')
        self.lineedit = QtWidgets.QLineEdit()
        self.attributes_layout.addWidget(self.label)
        self.attributes_layout.addWidget(self.lineedit)
        self.attributes.append((self.label, self.lineedit))

        self.attributes_layout2 = QtWidgets.QHBoxLayout()
        self.label2 = QtWidgets.QLabel('connected_buddies')
        self.lineedit2 = QtWidgets.QLineEdit()
        self.attributes_layout2.addWidget(self.label2)
        self.attributes_layout2.addWidget(self.lineedit2)
        self.attributes.append((self.label2, self.lineedit2))

        self.tab_vert_layout = QtWidgets.QVBoxLayout()
        self.tab_vert_layout.setAlignment(QtCore.Qt.AlignTop)
        self.my_frame.setLayout(self.tab_vert_layout)

        self.tab_vert_layout.addLayout(self.attributes_layout)
        self.tab_vert_layout.addLayout(self.attributes_layout2)

        self.layout().addWidget(self.my_frame)

    def get_values_iter(self):
        # for label_i, linedit_i in self.attributes:

        return ((label_i.text(), linedit_i.text()) for (label_i, linedit_i) in self.attributes)

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    ex = AgentNodeWindow(None, name='Agent')
    ex.open_node()
    sys.exit(app.exec_())