"""
Display drag from the app into the graph widget and the event bridge.
This is similar to the hello world sample.
"""
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

import qmxgraph.mime
from qmxgraph.widget import EventsBridge
from qmxgraph.widget import QmxGraph


def create_drag_button(text, qmx_style, parent=None):
    button = DragButton(parent)
    button.setText(text)
    # # You can set an icon to the button with:
    # button.setIcon(...)
    button.setProperty('qmx_style', qmx_style)
    button.setToolTip("Drag me into the graph widget")
    return button


class DragButton(QPushButton):
    """
    Start a drag even with custom data.
    """

    def mousePressEvent(self, event):
        mime_data = qmxgraph.mime.create_qt_mime_data(
            {
                'vertices': [
                    {
                        'dx': 0,
                        'dy': 0,
                        'width': 120,
                        'height': 40,
                        'label': self.text(),
                        'style': self.property('qmx_style'),
                    }
                ]
            }
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        # # You can set icons like the following:
        # w, h = self.property('component_size')
        # # Image displayed while dragging.
        # drag.setPixmap(self.icon().pixmap(w, h))
        # # Position of the image where the mouse is centered.
        # drag.setHotSpot(QPoint(w // 2, h // 2)
        drag.exec_()


class DragAndDropWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setProperty('name', 'adas')
        self.setMinimumSize(QSize(640, 480))
        self.setWindowTitle("Drag&Drop Styles")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.button_pane = QWidget(self)
        self.button_pane.setEnabled(False)
        red_button = create_drag_button('RED', 'fillColor=#D88', self.button_pane)
        green_button = create_drag_button('GREEN', 'fillColor=#8D8', self.button_pane)
        blue_button = create_drag_button('BLUE', 'fillColor=#88D', self.button_pane)

        self.graph_widget = QmxGraph(parent=central_widget)
        self.events_bridge = self.create_events_bridge()
        self.graph_widget.loadFinished.connect(self.graph_load_handler)

        main_layout = QGridLayout(self)
        central_widget.setLayout(main_layout)
        main_layout.addWidget(self.graph_widget, 0, 0)
        main_layout.addWidget(self.button_pane, 0, 1)

        buttons_layout = QVBoxLayout(self.button_pane)
        self.button_pane.setLayout(buttons_layout)
        buttons_layout.addWidget(red_button)
        buttons_layout.addWidget(green_button)
        buttons_layout.addWidget(blue_button)

    def create_events_bridge(self):
        ##################################
        # Based in `EventsBridge` docstring.

        def on_cells_added_handler(cell_ids):
            print(f'added {cell_ids}')
            qmx = widget.api
            for cid in cell_ids:
                label = qmx.get_label(cid)
                qmx.set_label(cid, f'{label} ({cid})')

        def on_terminal_changed_handler(cell_id, terminal_type, new_terminal_id, old_terminal_id):
            print(
                f'{terminal_type} of {cell_id} changed from'
                f' {old_terminal_id} to {new_terminal_id}'
            )

        def on_cells_removed_handler(cell_ids):
            print(f'removed {cell_ids}')

        def on_cells_bounds_changed_handler(changed_cell_bounds):
            print(f'cells bounds changed {changed_cell_bounds}')

        events_bridge = EventsBridge()
        widget = self.graph_widget
        widget.set_events_bridge(events_bridge)

        events_bridge.on_cells_added.connect(on_cells_added_handler)
        events_bridge.on_cells_removed.connect(on_cells_removed_handler)
        events_bridge.on_terminal_changed.connect(on_terminal_changed_handler)
        events_bridge.on_cells_bounds_changed.connect(on_cells_bounds_changed_handler)

        #
        ##################################
        return events_bridge

    def graph_load_handler(self, is_loaded):
        self.button_pane.setEnabled(is_loaded)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = DragAndDropWindow()
    mainWin.show()
    sys.exit(app.exec_())
