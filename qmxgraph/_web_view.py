import functools
import weakref

# Dynamic dependency that may mess freezing tools if not included
from PyQt5 import QtPrintSupport  # noqa
from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView


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
        self._loaded = False
        self._loading = False

        # It is common to use drag&drop with this widget
        self.setAcceptDrops(True)

        self_ref = weakref.ref(self)

        def post_load(ok):
            self_ = self_ref()
            if not self_ or not ok:
                return

            self_._loaded = True
            self_._loading = False

        def during_load():
            self_ = self_ref()
            if not self_:
                return

            self_.loading = True

        self.loadFinished.connect(functools.partial(post_load))
        self.loadStarted.connect(during_load)

    def is_loaded(self):
        """
        :rtype: bool
        :return: Is page already loaded?
        """
        return self._loaded

    def is_loading(self):
        """
        :rtype: bool
        :return: Is page currently loading?
        """
        return self._loading

    def blank(self):
        """
        Blanks web view page, effectively clearing/unloading currently
        content.
        """
        self._loaded = False
        self.setHtml('')

    def eval_js(self, statement):
        """
        Evaluate a JavaScript statement using this web view frame as context.

        :param str statement: A JavaScript statement.
        :rtype: object
        :return: Return of statement.
        """
        from qmxgraph.callback_blocker import CallbackBlocker

        with CallbackBlocker(timeout=5000) as cb:
            self.page().runJavaScript(statement, cb)

        return cb.args[0]

    # Overridden Events -------------------------------------------------------

    def dragEnterEvent(self, event):
        self.on_drag_enter_event.emit(event)

    def dragMoveEvent(self, event):
        self.on_drag_move_event.emit(event)

    def dropEvent(self, event):
        self.on_drop_event.emit(event)
