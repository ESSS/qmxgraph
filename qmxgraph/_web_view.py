import functools
import weakref

# Dynamic dependency that may mess freezing tools if not included
from enum import Enum, auto
from typing import Any, Optional
from PyQt5.QtCore import QUrl
from PyQt5 import QtPrintSupport  # noqa
from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication
from oop_ext.foundation.callback import Callback
from qmxgraph.configuration import GraphStyles, GraphOptions
from qmxgraph.waiting import wait_until, wait_callback_called


class ViewState(Enum):
    Blank = auto()
    GraphLoaded = auto()
    LoadingGraph = auto()
    LoadingBlank = auto()
    LoadingError = auto()
    Closing = auto()

class QWebViewWithDragDrop(QWebEngineView):
    """
    Specialization of QWebView able to handle drag&drop of objects.
    """

    on_drag_enter_event = pyqtSignal(QEvent)
    on_drag_move_event = pyqtSignal(QEvent)
    on_drop_event = pyqtSignal(QEvent)

    def __init__(self, *args, **kwargs):
        QWebEngineView.__init__(self, *args, **kwargs)

        self._drag_drop_handler = None

        self.on_finalize_graph_load = Callback()
        self.on_finalize_blank = Callback()

        self._view_state = ViewState.Blank

        # It is common to use drag&drop with this widget
        self.setAcceptDrops(True)

        self.loadFinished.connect(self._on_load_finished)

    @property
    def view_state(self) -> ViewState:
        return self._view_state

    def _on_load_finished(self, ok):
        if not ok:
            self._view_state = ViewState.LoadingError
        elif self._view_state is ViewState.LoadingBlank:
            self._block_updates()
            self.on_finalize_blank()
            self._view_state = ViewState.Blank
        elif self._view_state is ViewState.LoadingGraph:
            self._unblock_updates()
            self.on_finalize_graph_load()
            self._view_state = ViewState.GraphLoaded
        # We ignore other view states as they don't interest us after
        # a successful loadFinished signal (for example
        # ViewState.LoadingError should remain a loading error).

    def load_graph(self, options: GraphOptions, styles: GraphStyles, stencils):
        """
        Load graph drawing page with the given options, if not yet loaded or still loading.
        """
        if self.view_state in (ViewState.GraphLoaded, ViewState.LoadingGraph):
            return

        from qmxgraph import render

        html = render.render_embedded_html(
            options=options,
            styles=styles,
            stencils=stencils,
            mxgraph_path=':/mxgraph',
            own_path=':/qmxgraph',
        )
        self._view_state = ViewState.LoadingGraph
        self.setHtml(html, baseUrl=QUrl('qrc:/'))

    def blank(self):
        """
        Blanks web view page, effectively clearing/unloading current
        content.
        """
        self._view_state = ViewState.LoadingBlank
        self.setHtml('')

    def closeEvent(self, event: QCloseEvent) -> None:
        self.stop()
        self._view_state = ViewState.Closing
        self._block_updates()
        super().closeEvent(event)

    def _block_updates(self) -> None:
        # TODO[ASIM-4283]: Add tests.
        self.page().webChannel().setBlockUpdates(True)
        self.page().webChannel().blockSignals(True)

    def _unblock_updates(self) -> None:
        # TODO[ASIM-4283]: Add tests.
        self.page().webChannel().setBlockUpdates(False)
        self.page().webChannel().blockSignals(False)

    def eval_js(self, statement, *, timeout_ms: int=10_000, sync=True, check_api=True) -> Any:
        """
        Evaluate a JavaScript statement using this web view frame as context.

        :param str statement: A JavaScript statement.
        :rtype: object
        :return: Return of statement.
        """

        # TODO[ASIM-4289]: remove 'sync' argument, create 'eval_js_sync' instead.
        if check_api and self.view_state is not ViewState.GraphLoaded:
            raise RuntimeError(f"Invalid view state ({self.view_state}), graph not loaded")

        if sync:
            with wait_callback_called(timeout_ms=timeout_ms) as callback:
                self.page().runJavaScript(statement, callback)
            return callback.args[0]
        else:
            def c(*a, **aa): pass
            self.page().runJavaScript(statement, c)
            return

    # Overridden Events -------------------------------------------------------

    def dragEnterEvent(self, event):
        self.on_drag_enter_event.emit(event)

    def dragMoveEvent(self, event):
        self.on_drag_move_event.emit(event)

    def dropEvent(self, event):
        self.on_drop_event.emit(event)
