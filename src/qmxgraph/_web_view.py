# Dynamic dependency that may mess freezing tools if not included
from enum import auto
from enum import Enum
from typing import Any

from oop_ext.foundation.callback import Callback
from PyQt5 import QtPrintSupport  # noqa
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView

from qmxgraph.configuration import GraphOptions
from qmxgraph.configuration import GraphStyles
from qmxgraph.waiting import wait_callback_called


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

    def setWebChannel(self, web_channel: QWebChannel) -> None:
        self.page().setWebChannel(web_channel)
        self._block_web_channel()

    def _on_load_finished(self, ok):
        if not ok:
            self._view_state = ViewState.LoadingError
        elif self._view_state is ViewState.LoadingBlank:
            self._view_state = ViewState.Blank
            self._block_web_channel()
            self.on_finalize_blank()
        elif self._view_state is ViewState.LoadingGraph:
            self._view_state = ViewState.GraphLoaded
            self._unblock_web_channel()
            self.on_finalize_graph_load()
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
        self._block_web_channel()
        super().closeEvent(event)

    def _block_web_channel(self) -> None:
        """Blocks updates and signals from the webchannel."""
        self.page().webChannel().setBlockUpdates(True)
        self.page().webChannel().blockSignals(True)

    def _unblock_web_channel(self) -> None:
        """Unblocks updates and signals from the webchannel."""
        self.page().webChannel().setBlockUpdates(False)
        self.page().webChannel().blockSignals(False)

    def eval_js(self, script, *, timeout_ms: int = 10_000) -> Any:
        """
        Evaluate a JavaScript script using this web view frame as context, and
        return the value of its last statement.

        :param script:
            A JavaScript script.
        :param timeout_ms:
            Timeout to wait for a result, raising TimeoutError if
            the engine doesn't respond in time.

        :return:
            The result of the last executed JS statement.
        """
        self._check_valid_eval_state()
        with wait_callback_called(timeout_ms=timeout_ms) as callback:
            self.page().runJavaScript(script, callback)
        assert callback.args is not None
        return callback.args[0]

    def eval_js_async(self, script: str) -> None:
        """
        Evaluate a JavaScript statement using this web view frame as context asynchronously.

        This will send the JS statement over to the Engine, which will be evaluated at some point in
        the future, and returns immediately.

        There's no way to obtain the result of the statement, use ``eval_js`` instead if that's
        required (there's no way currently to call JS statements asynchronously and also obtain the
        result).

        :param script: A JavaScript statement.
        """
        self._check_valid_eval_state()
        self.page().runJavaScript(script)

    def _check_valid_eval_state(self) -> None:
        """Check the view is in a valid state to evaluate JS commands."""
        if self.view_state is not ViewState.GraphLoaded:
            raise RuntimeError(f"Invalid view state ({self.view_state}), graph not loaded")

    # Overridden Events -------------------------------------------------------

    def dragEnterEvent(self, event):
        self.on_drag_enter_event.emit(event)

    def dragMoveEvent(self, event):
        self.on_drag_move_event.emit(event)

    def dropEvent(self, event):
        self.on_drop_event.emit(event)
