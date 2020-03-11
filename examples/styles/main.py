"""
Display the use of styles. This is similar to the hello world sample.
"""

import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMainWindow

from qmxgraph.configuration import GraphStyles
from qmxgraph.widget import QmxGraph


class StyleWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(640, 480))
        self.setWindowTitle("Qmx Styles")

        styles_cfg = {
            'round_node': {
                'shape': 'ellipse',
                'fill_color': '#D88',
                'vertical_label_position': 'bottom',
                'vertical_align': 'top',
            },
            'bold_edge': {
                'end_arrow': 'classic',
                'shape': 'connector',
                'stroke_width': 5.0,
            },
        }

        self.graph_widget = QmxGraph(
            styles=GraphStyles(styles_cfg), parent=self
        )
        # Only operate with the qmx's api after the widget has been loaded.
        self.graph_widget.loadFinished.connect(self.graph_load_handler)
        self.setCentralWidget(self.graph_widget)

    def graph_load_handler(self, is_loaded):
        assert is_loaded
        qmx = self.graph_widget.api
        v0_id = qmx.insert_vertex(
            x=100, y=100, width=50, height=50, label="AAA"
        )
        # Style by configured style name.
        v1_id = qmx.insert_vertex(
            x=400,
            y=100,
            width=100,
            height=50,
            label="BBB",
            style='round_node',
        )
        # Style by explicit values.
        v2_id = qmx.insert_vertex(
            x=200,
            y=300,
            width=50,
            height=100,
            label="CCC",
            style='fillColor=#8D8',
        )

        qmx.insert_edge(source_id=v0_id, target_id=v1_id, label='normal')
        qmx.insert_edge(
            source_id=v1_id, target_id=v2_id, label='bold', style='bold_edge'
        )


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = StyleWindow()
    mainWin.show()
    sys.exit(app.exec_())
