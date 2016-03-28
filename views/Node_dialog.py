__author__ = 'User'
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from model.nodes.classes.Task import cTask, make_task_from_str

from pprint import pprint

# Workaround to get exceptions from Qt
sys._excepthook = sys.excepthook

def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


class MyLineEdit(QtWidgets.QLineEdit):
    textModified = QtCore.pyqtSignal(str, str) # (before, after)

    def __init__(self, contents='', parent=None):
        super(MyLineEdit, self).__init__(contents, parent)
        self.editingFinished.connect(self.checkText)
        self.textChanged.connect(lambda: self.checkText())
        self.returnPressed.connect(lambda: self.checkText(True))
        self._before = contents
        self.changed = False

    def checkText(self, _return=False):
        if (not self.hasFocus() or _return) and self._before != self.text():
            self.textModified.emit(self._before, self.text())
            self.changed = True
            self._before = self.text()

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
    def __init__(self, parent, node=None):
        super().__init__(parent)
        # adding more tabs
        self.node = node
        name = self.node.name

        if name:
            self.setWindowTitle(name)

        self.tab_widget_add = TabPropitiesWidget()
        # Grab self.nodes attributes
        for attr_i, val_i in sorted(self.node.__dict__.items()):
            if attr_i in node.attrs_to_save:
                if attr_i in node.read_only_attrs:
                    print('adding readonly to widget', attr_i, val_i)
                    self.tab_widget_add.add_attribute(attr_i, val_i, readonly=True)
                else:
                    print('adding  to widget', attr_i, val_i)
                    self.tab_widget_add.add_attribute(attr_i, val_i)

        # TODO dunno how to change widget on the fly...
        self.tab_menu.removeTab(0)
        self.tab_menu.addTab(self.tab_widget_add, 'Agent Properties')

    def accept(self):
        # apply changed attributes
        attributes = self.tab_widget_add.get_values_iter()
        print('Set attributes : ')
        for label_i, linedit_i in attributes:
            print(label_i.text(), linedit_i.text())
            # TODO name changing -> change in Gui
            if linedit_i.changed:
                if label_i.text() == 'items':
                    # enter tasking
                    value = linedit_i.text()
                    item_list = value.split(' ')
                    tasks = []
                    for item in item_list:
                        tasks += [make_task_from_str(item)]
                    self.node.set_tasks(tasks)
                else:
                    print('CHANGING {}'.format(label_i.text()))
                    setattr(self.node, label_i.text(), linedit_i.text())
                    linedit_i.changed = False
        self.deleteLater()
        self.close()

    def reject(self):
        self.deleteLater()
        self.close()

# TODO implement proper accept
class HubNodeWindow(NodeWindow):
    def __init__(self, parent, node=None):
        super().__init__(parent)
        # adding more tabs
        self.node = node
        name = self.node.name

        if name:
            self.setWindowTitle(name)

        self.tab_widget_add = TabPropitiesWidget()
        # Grab self.nodes attributes
        for attr_i, val_i in sorted(self.node.__dict__.items()):
            if attr_i in node.attrs_to_save:
                if attr_i in node.read_only_attrs:
                    print('adding readonly to widget', attr_i, val_i)
                    self.tab_widget_add.add_attribute(attr_i, val_i, readonly=True)
                else:
                    print('adding  to widget', attr_i, val_i)
                    self.tab_widget_add.add_attribute(attr_i, val_i)

        # TODO dunno how to change widget on the fly...
        self.tab_menu.removeTab(0)
        self.tab_menu.addTab(self.tab_widget_add, 'Agent Properties')

    def accept(self):
        # apply changed attributes
        attributes = self.tab_widget_add.get_values_iter()
        print('Set attributes : ')
        for label_i, linedit_i in attributes:
            print(label_i.text(), linedit_i.text())
            # TODO name changing -> change in Gui
            if linedit_i.changed:
                if label_i.text() == 'conditions_dict':
                    # enter conditions
                    print('****** SETTING CONDITIONS ')
                    value = linedit_i.text()
                    #FIXME EVAL EXPLOIT !!!
                    # cond_dict = eval("dict(%s)"%value.replace(" ", ","))
                    cond_dict = eval("dict(%s)" % value)
                    self.node.condition(**cond_dict)
                else:
                    print('CHANGING {}'.format(label_i.text()))
                    setattr(self.node, label_i.text(), linedit_i.text())
                    linedit_i.changed = False
        self.deleteLater()
        self.close()

    def reject(self):
        self.deleteLater()
        self.close()

# TODO implement proper accept
class FuncNodeWindow(NodeWindow):
    def __init__(self, parent, node=None):
        super().__init__(parent)
        # adding more tabs
        self.node = node
        name = self.node.name

        if name:
            self.setWindowTitle(name)

        self.tab_widget_add = TabPropitiesWidget()
        # Grab self.nodes attributes
        for attr_i, val_i in sorted(self.node.__dict__.items()):
            if attr_i in node.attrs_to_save:
                if attr_i in node.read_only_attrs:
                    print('adding readonly to widget', attr_i, val_i)
                    self.tab_widget_add.add_attribute(attr_i, val_i, readonly=True)
                else:
                    print('adding  to widget', attr_i, val_i)
                    self.tab_widget_add.add_attribute(attr_i, val_i)

        # TODO dunno how to change widget on the fly...
        self.tab_menu.removeTab(0)
        self.tab_menu.addTab(self.tab_widget_add, 'Agent Properties')

    def accept(self):
        # apply changed attributes
        attributes = self.tab_widget_add.get_values_iter()
        print('Set attributes : ')
        for label_i, linedit_i in attributes:
            print(label_i.text(), linedit_i.text())
            # TODO name changing -> change in Gui
            if linedit_i.changed:
                if label_i.text() == 'items':
                    # enter tasking
                    value = linedit_i.text()
                    task = make_task_from_str(value)
                    self.node.set_tasks([task])
                else:
                    print('CHANGING {}'.format(label_i.text()))
                    setattr(self.node, label_i.text(), linedit_i.text())
                    linedit_i.changed = False
        self.deleteLater()
        self.close()

    def reject(self):
        self.deleteLater()
        self.close()


class TabPropitiesWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.attributes = {}

        self.initUI()

    def initUI(self):
        self.setLayout(QtWidgets.QVBoxLayout())

        self.my_frame = QtWidgets.QFrame(self)

        self.tab_vert_layout = QtWidgets.QVBoxLayout()
        self.tab_vert_layout.setAlignment(QtCore.Qt.AlignTop)
        self.my_frame.setLayout(self.tab_vert_layout)

        self.layout().addWidget(self.my_frame)

    def add_attribute(self, label, value=None, readonly=False):
        """
        Adding pair label-value to widget
        :param label: str| attr name
        :param value: attr value
        :param readonly: if true, lineedit will be disabled to change
        """
        attributes_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label)
        lineedit = MyLineEdit()
        if value:
            lineedit.setText(str(value))
            lineedit.changed = False
        if readonly:
            lineedit.setReadOnly(True)
            lineedit.setDisabled(True)
        attributes_layout.addWidget(label)
        attributes_layout.addWidget(lineedit)
        # self.attributes.append((label, lineedit, 0))
        self.attributes[label] = lineedit

        self.tab_vert_layout.addLayout(attributes_layout)

    def get_values_iter(self):
        # for label_i, linedit_i in self.attributes:

        return self.attributes.items()


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    ex = AgentNodeWindow(None, name='Agent')
    ex.open_node()
    sys.exit(app.exec_())