import os

# This import is placed on the qmxgraph's `__init__` module to make it
# less likely users to stumble into the "ImportError: QtWebEngineWidgets
# must be imported before a QCoreApplication instance is created" error.
#
# Some ugliness to successfully build the doc on ReadTheDocs...
on_rtd = os.environ.get('READTHEDOCS') == 'True'
if not on_rtd:
    import PyQt5.QtWebEngineWidgets  # noqa
