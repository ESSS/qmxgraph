"""
We all love "hello world" examples =)
"""

import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMainWindow

from qmxgraph.widget import QmxGraph


class HelloWorldWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(640, 480))
        self.setWindowTitle("Qmx Hello World")

        self.graph_widget = QmxGraph(parent=self)
        # Only operate with the qmx's api after the widget has been loaded.
        self.graph_widget.loadFinished.connect(self.graph_load_handler)
        self.setCentralWidget(self.graph_widget)

    def graph_load_handler(self, is_loaded):
        assert is_loaded
        qmx = self.graph_widget.api
        v0_id = qmx.insert_vertex(x=100, y=100, width=50, height=100, label="Qmx")
        v1_id = qmx.insert_vertex(x=400, y=300, width=100, height=50, label="World")
        qmx.insert_edge(source_id=v0_id, target_id=v1_id, label="Hello")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = HelloWorldWindow()
    mainWin.show()
    sys.exit(app.exec_())
