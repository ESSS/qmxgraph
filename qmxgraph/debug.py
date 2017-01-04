
def set_qmxgraph_debug(enabled):
    """
    Enables/disables checks and other helpful debug features globally in
    QmxGraph.

    :param bool enabled: If enabled or not.
    """
    global _QGRAPH_DEBUG
    _QGRAPH_DEBUG = bool(enabled)


def is_qmxgraph_debug_enabled():
    """
    :rtype: bool
    :return: Are QmxGraph debug features enabled globally?
    """
    return _QGRAPH_DEBUG


_QGRAPH_DEBUG = False
