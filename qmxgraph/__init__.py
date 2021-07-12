# This import is placed on the qmxgraph's `__init__` module to make it
# less likely users to stumble into the "ImportError: QtWebEngineWidgets
# must be imported before a QCoreApplication instance is created" error.
import PyQt5.QtWebEngineWidgets  # noqa
