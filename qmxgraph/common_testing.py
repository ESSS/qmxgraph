"""
Those are helper tools that could help in applications' tests.
"""
from contextlib import ExitStack, contextmanager
from typing import Iterator, List, cast

from PyQt5.QtCore import pyqtSignal

from qmxgraph.callback_blocker import CallbackBlocker, silent_disconnect
from qmxgraph.widget import QmxGraph


def get_cell_count(widget: QmxGraph, filter_function: str) -> int:
    """
    :param widget: The widget used to display the graph.
    :param filter_function: A javascript function used to filter the cells.
        This function will receive one argument of the type mxCell and should
        return a boolean (`true` select the cell, `false` ignore the cell).
    :return: The number of selected cells.
    """
    return len(get_cell_ids(widget, filter_function))


def get_cell_ids(widget: QmxGraph, filter_function: str) -> List[str]:
    """
    :param widget: The widget used to display the graph.
    :param filter_function: A javascript function used to filter the cells.
        This function will receive one argument of the type mxCell and should
        return a boolean (`true` select the cell, `false` ignore the cell).
    :return: A list with the id's of the selected cells.
    """
    cells_ids = widget.inner_web_view().eval_js(
        f'''
        (function(){{
            var all_cells = api._graphEditor.graph.model.cells;
            var cells = Object.keys(all_cells).map(
                function(id){{ return all_cells[id]; }}
            );

            cells = cells.filter({filter_function});
            return cells.map(function(aCell){{ return aCell.getId(); }});
        }})()'''
    )
    return cast(List[str], cells_ids)


@contextmanager
def wait_signals(
    *signals: pyqtSignal,
    timeout: int = CallbackBlocker.DEFAULT_TIMEOUT,
) -> Iterator[List[CallbackBlocker]]:
    """
    Attach one callback blocker to each signal blocking the execution
    until every one is called once (and only once).

    :param signals: The list of bridge signals.
    :param timeout: This argument is forwarded when instantiating
        the `CallbackBlocker`'s.
    """
    connected_callback_blockers = []
    try:
        with ExitStack() as stack:
            for signal_instance in signals:
                cb = CallbackBlocker(timeout=timeout)
                signal_instance.connect(cb)
                connected_callback_blockers.append((signal_instance, cb))
                stack.enter_context(cb)

            yield [cb for _, cb in connected_callback_blockers]

    finally:
        for signal_instance, cb in reversed(connected_callback_blockers):
            silent_disconnect(signal_instance, cb)
