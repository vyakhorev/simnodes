from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from model.nodes.utils.TaskDispenser import cTaskDispenser
from pprint import pprint

# Workaround to get exceptions from Qt
sys._excepthook = sys.excepthook

def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


class TaskManager(QtWidgets.QWidget):
    """
    Main window for holding populated tasks
    """
    def __init__(self):
        super().__init__()
        self.build_ui()
        self.show()

    def build_ui(self):
        # Main Layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_frame = QtWidgets.QFrame()
        self.main_layout.addWidget(self.main_frame)
        self.setLayout(self.main_layout)
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(0)
        self.resize(600, 400)
        self.setWindowTitle('TaskManager')

        # Tasks plus table layout
        self.tsk_and_table_layout = QtWidgets.QVBoxLayout()
        self.tasks_menu_widget = QtWidgets.QWidget(self)
        self.tasks_table_widget = TaskTableWidget(self)
        self.tsk_and_table_layout.addWidget(self.tasks_menu_widget)
        self.tsk_and_table_layout.addWidget(self.tasks_table_widget)

        # adding to main
        self.main_frame.setLayout(self.tsk_and_table_layout)

        # fill up self.tasks_menu_widget
        self.tsk_group_layout = QtWidgets.QGridLayout()
        # for i in range(3):
        #     for j in range(4):
        #         draggable_mini_frame = DragableTaskFrame(self)
        #         self.tsk_group_layout.addWidget(draggable_mini_frame, i, j)
        self.tasks_menu_widget.setLayout(self.tsk_group_layout)

        td = cTaskDispenser()
        self.fill_tasks_frames(td.items())


    def fill_tasks_frames(self, adict):
        for label, kls in adict.items():
            draggable_mini_frame = DragableTaskFrame(self, label=label, kls_ref=kls)
            draggable_mini_frame.frame_clicked_sig.connect(self.add_task_to_table)
            self.tsk_group_layout.addWidget(draggable_mini_frame)

    @QtCore.pyqtSlot(object)
    def add_task_to_table(self, data):
        label, kls_ref = data
        print('HOLA', kls_ref)
        an_item = QtWidgets.QTableWidgetItem(label)
        self.tasks_table_widget.setItem(0, 0, an_item)
        self.tasks_table_widget.insertRow(0)

class DragableTaskFrame(QtWidgets.QFrame):
    """
    These guys will be drag to table
    """
    frame_clicked_sig = QtCore.pyqtSignal(object)

    def __init__(self, parent, label=None, kls_ref=None):
        super().__init__(parent)

        self.mylabel = label
        self.my_klass_ref = kls_ref
        self.resize(30, 40)

        self.setStyleSheet("background-color: lightgreen; ")
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel(self.mylabel))

    def mousePressEvent(self, event):
        print('Adding ', self.my_klass_ref)
        self.frame_clicked_sig.emit([self.mylabel, self.my_klass_ref])


class TaskTableWidget(QtWidgets.QTableWidget):
    """
    Here tasks leaving
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.setRowCount(1)
        self.setColumnCount(4)
        self.setStyleSheet("background-color: lightgray; ")

        self.build_ui()
        # self.resizeColumnsToContents()
        # self.resizeRowsToContents()


    def build_ui(self):
        horHeaders = ['task', 'quantity', 'time', 'misc']
        self.setHorizontalHeaderLabels(horHeaders)


if __name__ == '__main__':
    td = cTaskDispenser()

    app = QtWidgets.QApplication(sys.argv)
    ex = TaskManager()
    ex.fill_tasks_frames(td.items())
    sys.exit(app.exec_())