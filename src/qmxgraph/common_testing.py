"""
Those are helper tools that could help in applications' tests.
"""
from typing import cast
from typing import List

from qmxgraph.widget import QmxGraph


RETURN_ALL_CELLS_FILTER = "function(cell) { return true }"


def get_cell_count(widget: QmxGraph, filter_function: str = RETURN_ALL_CELLS_FILTER) -> int:
    """
    :param widget: The widget used to display the graph.
    :param filter_function: A javascript function used to filter the cells.
        This function will receive one argument of the type mxCell and should
        return a boolean (`true` select the cell, `false` ignore the cell).
    :return: The number of selected cells.
    """
    return len(get_cell_ids(widget, filter_function))


def get_cell_ids(widget: QmxGraph, filter_function: str = RETURN_ALL_CELLS_FILTER) -> List[str]:
    """
    :param widget: The widget used to display the graph.
    :param filter_function: A javascript function used to filter the cells.
        This function will receive one argument of the type mxCell and should
        return a boolean (`true` select the cell, `false` ignore the cell).
    :return: A list with the id's of the selected cells.
    """
    cells_ids = widget.inner_web_view().eval_js(
        f"""
        (function(){{
            var all_cells = api._graphEditor.graph.model.cells;
            var cells = Object.keys(all_cells).map(
                function(id){{ return all_cells[id]; }}
            );

            cells = cells.filter({filter_function});
            return cells.map(function(aCell){{ return aCell.getId(); }});
        }})()"""
    )
    return cast(List[str], cells_ids)
