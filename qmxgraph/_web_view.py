import functools
import weakref

# Dynamic dependency of QWebView that may mess freezing tools if not included
from PyQt5 import QtPrintSupport  # noqa
from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtWebKitWidgets import QWebView


class QWebViewWithDragDrop(QWebView):
    """
    Specialization of QWebView able to handle drag&drop of objects.
    """

    on_drag_enter_event = pyqtSignal(QEvent)
    on_drag_move_event = pyqtSignal(QEvent)
    on_drop_event = pyqtSignal(QEvent)

    def __init__(self, *args, **kwargs):
        QWebView.__init__(self, *args, **kwargs)

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
        self.setHtml('')
        self._loaded = False

    def eval_js(self, statement):
        """
        Evaluate a JavaScript statement using this web view frame as context.

        :param str statement: A JavaScript statement.
        :rtype: object
        :return: Return of statement.
        """
        # WebKit sadly doesn't provide error object on `on_error` global event,
        # preventing traceback from reaching Python side. To aid with that
        # issue, every statement is surrounded by a block that explicitly
        # includes traceback to error message.
        traceback_block = """\
try {{
    {statement};
}} catch (e) {{
    e.message = 'message: ' + e.message + '\\nstack:\\n' + e.stack;
    throw e;
}}"""
        block = traceback_block.format(statement=statement)
        return self.page().mainFrame().evaluateJavaScript(block)

    def add_to_js_window(self, name, bridge):
        """
        Bridge is an object that allows two-way communication between Python
        and JS side.

        :param str name: Name of variable in `window` object on JS side
            that is going to keep reference to bridge object.
        :param qt_traits.QObject bridge: A Qt object that respects Qt-JS
            two way serialization protocol. To learn more about this
            interaction see
            [QtWebKit bridge](http://doc.qt.io/qt-4.8/qtwebkit-bridge.html).
        """
        self.page().mainFrame().addToJavaScriptWindowObject(name, bridge)

    # Overridden Events -------------------------------------------------------

    def dragEnterEvent(self, event):
        self.on_drag_enter_event.emit(event)

    def dragMoveEvent(self, event):
        self.on_drag_move_event.emit(event)

    def dropEvent(self, event):
        self.on_drop_event.emit(event)
