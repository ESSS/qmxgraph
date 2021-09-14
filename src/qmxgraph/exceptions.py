class QmxGraphError(Exception):
    """
    Base exception for all exceptions raised by qmxgraph.
    """


class InvalidJavaScriptError(QmxGraphError):
    """
    Raised when call to invalid JavaScript (for instance, non-existing
    function) is made by Python code.
    """


class ViewStateError(QmxGraphError):
    """
    Raised when QmxGraph cannot change states.
    """
