import sys
import textwrap
import weakref
from contextlib import contextmanager
from typing import Generator
from typing import List

import qmxgraph.debug
import qmxgraph.js
from qmxgraph.exceptions import InvalidJavaScriptError


class QmxGraphApi(object):
    """
    Python binding for API used to control underlying JavaScript's mxGraph
    graph drawing library.
    """

    SOURCE_TERMINAL_CELL = 'source'
    TARGET_TERMINAL_CELL = 'target'

    LAYOUT_ORGANIC = 'organic'
    LAYOUT_COMPACT = 'compact'
    LAYOUT_CIRCLE = 'circle'
    LAYOUT_COMPACT_TREE = 'compact_tree'
    LAYOUT_EDGE_LABEL = 'edge_label'
    LAYOUT_PARALLEL_EDGE = 'parallel_edge'
    LAYOUT_PARTITION = 'partition'
    LAYOUT_RADIAL_TREE = 'radial_tree'
    LAYOUT_STACK = 'stack'

    def __init__(self, graph, call_context_manager_factory):
        """
        :param qmxgraph.widget.QmxGraph graph: A graph drawing widget.
        :param call_context_manager_factory:
            A function that will be called with no arguments, that should return a context manager.
            The context manager will be entered before we call eval_js, so it can be used to do stuff before
            and after eval_js calls.
        """
        self._graph = weakref.ref(graph)
        self._call_context_manager_factory = call_context_manager_factory

    def insert_vertex(self, x, y, width, height, label, style=None, tags=None, id=None):
        """
        Inserts a new vertex in graph.

        :param int x: X coordinate in screen coordinates.
        :param int y: Y coordinate in screen coordinates.
        :param int width: Width in pixels.
        :param int height: Height in pixels.
        :param str label: Label of vertex.
        :param str|None style: Name of style to be used. Styles
            available are all default ones provided by mxGraph plus additional
            ones configured in initialization of this class.
        :param dict[str,str]|None tags: Tags are basically custom attributes
            that may be added to a cell that may be later queried (or even
            modified), with the objective of allowing better inspection and
            interaction with cells in a graph.
        :param Optional[str] id: The id of the edge. If omitted (or non
            unique) an id is generated.
        :rtype: str
        :return: Id of new vertex.
        """
        return self.call_api('insertVertex', x, y, width, height, label, style, tags, id)

    def insert_port(
        self, vertex_id, port_name, x, y, width, height, label=None, style=None, tags=None
    ):
        """
        Inserts a new port in vertex.

        :param str vertex_id: The id of the vertex to witch add this port.
        :param str port_name: The name used to refer to the new port.
        :param float x: The normalized (0-1) X coordinate for the port
            (relative to vertex bounds).
        :param float y: The normalized (0-1) Y coordinate for the port
            (relative to vertex bounds).
        :param int width: Width of port.
        :param int height: Height of port.
        :param str|None label: Label of port.
        :param str|None style: Name of style to be used. Styles
            available are all default ones provided by mxGraph plus additional
            ones configured in initialization of this class.
        :param dict[str,str]|None tags: Tags are basically custom attributes
            that may be added to a cell that may be later queried (or even
            modified), with the objective of allowing better inspection and
            interaction with cells in a graph.
        """
        return self.call_api(
            'insertPort', vertex_id, port_name, x, y, width, height, label, style, tags
        )

    def insert_edge(
        self,
        source_id,
        target_id,
        label,
        style=None,
        tags=None,
        source_port_name=None,
        target_port_name=None,
        id=None,
    ):
        """
        Inserts a new edge between two vertices in graph.

        :param str source_id: Id of source vertex in graph.
        :param str target_id: Id of target vertex in graph.
        :param str label: Label of edge.
        :param str|None style: Name of style to be used. Styles
            available are all default ones provided by mxGraph plus additional
            ones configured in initialization of this class.
        :param dict[str,str]|None tags: Tags are basically custom attributes
            that may be added to a cell that may be later queried (or even
            modified), with the objective of allowing better inspection and
            interaction with cells in a graph.
        :param str|None source_port_name: The name of the port used to connect
            to source vertex.
        :param str|None target_port_name: The name of the port used to connect
            to target vertex.
        :param Optional[str] id: The id of the edge. If omitted (or non
            unique) an id is generated.
        :rtype: str
        :return: Id of new edge.
        """
        return self.call_api(
            'insertEdge',
            source_id,
            target_id,
            label,
            style,
            tags,
            source_port_name,
            target_port_name,
            id,
        )

    def insert_decoration(self, x, y, width, height, label, style=None, tags=None, id=None):
        """
        Inserts a new decoration over an edge in graph. A decoration is
        basically an overlay object that is representing some entity over the
        path of an edge.

        Note that x and y must be inside the bounds of an edge, otherwise this
        call will raise.

        :param int x: X coordinate in screen coordinates.
        :param int y: Y coordinate in screen coordinates.
        :param int width: Width in pixels.
        :param int height: Height in pixels.
        :param str label: Label of decoration.
        :param str|None style: Name of style to be used. Styles
            available are all default ones provided by mxGraph plus additional
            ones configured in initialization of this class.
        :param dict[str,str]|None tags: Tags are basically custom attributes
            that may be added to a cell that may be later queried (or even
            modified), with the objective of allowing better inspection and
            interaction with cells in a graph.
        :param Optional[str] id: The id of the decoration. If omitted (or non
            unique) an id is generated.
        :rtype: str
        :return: Id of new decoration.
        """
        return self.call_api('insertDecoration', x, y, width, height, label, style, tags, id)

    def insert_decoration_on_edge(
        self, edge_id, position, width, height, label, style=None, tags=None, id=None
    ):
        """
        Inserts a new decoration over an edge in graph. A decoration is
        basically an overlay object that is representing some entity over the
        path of an edge.

        Note that x and y must be inside the bounds of an edge, otherwise this
        call will raise.

        :param str edge_id: Id of an edge in graph.
        :param float position: The normalized position in the edge.
        :param int width: Width in pixels.
        :param int height: Height in pixels.
        :param str label: Label of decoration.
        :param str|None style: Name of style to be used. Styles
            available are all default ones provided by mxGraph plus additional
            ones configured in initialization of this class.
        :param dict[str,str]|None tags: Tags are basically custom attributes
            that may be added to a cell that may be later queried (or even
            modified), with the objective of allowing better inspection and
            interaction with cells in a graph.
        :param Optional[str] id: The id of the decoration. If omitted (or non
            unique) an id is generated.
        :rtype: str
        :return: Id of new decoration.
        """
        return self.call_api(
            'insertDecorationOnEdge', edge_id, position, width, height, label, style, tags, id
        )

    def insert_table(
        self, x, y, width, contents, title, tags=None, style=None, parent_id=None, id=None
    ):
        """
        Inserts a new table in graph. A table is an object that can be used
        in graph to display tabular information about other cells, for
        instance. Tables can't be connected to other cells like vertices,
        edges nor decorations.

        :param int x: X coordinate in screen coordinates.
        :param int y: Y coordinate in screen coordinates.
        :param int width: Width in pixels.
        :param qmxgraph.decoration_contents.Table contents:
            The table contents.
        :param str title: Title of table.
        :param dict[str,str]|None tags: Tags are basically custom attributes
            that may be added to a cell that may be later queried (or even
            modified), with the objective of allowing better inspection and
            interaction with cells in a graph.
        :param str|None style: Name of style to be used (Note that the
            `'table'` style is always used, options configured with this style
            have greater precedence). Styles available are all default ones
            provided by mxGraph plus additional ones configured in
            initialization of this class.
        :param str|None parent_id: If not `None` the created table is placed
            in a relative position to the cell with id `parent_id`.
        :param Optional[str] id: The id of the table. If omitted (or non
            unique) an id is generated.
        :rtype: str
        :return: Id of new table.
        """
        from . import decoration_contents

        contents = decoration_contents.asdict(contents)
        return self.call_api(
            'insertTable', x, y, width, contents, title, tags, style, parent_id, id
        )

    def update_table(self, table_id, contents, title):
        """
        Update contents and title of a table in graph.

        :param str table_id: Id of a table in graph.
        :param qmxgraph.decoration_contents.Table contents:
            The table contents.
        :param str title: Title of table.
        """
        from . import decoration_contents

        contents = decoration_contents.asdict(contents)
        self.call_api('updateTable', table_id, contents, title, sync=False)

    def update_port(
        self,
        vertex_id,
        port_name,
        x=None,
        y=None,
        width=None,
        height=None,
        label=None,
        style=None,
        tags=None,
    ):
        self.call_api(
            'updatePort', vertex_id, port_name, x, y, width, height, label, style, tags, sync=False
        )

    def get_port_names(self, vertex_id):
        return self.call_api('getPortNames', vertex_id)

    def group(self):
        """
        Create a group with currently selected cells in graph. Edges connected
        between selected vertices are automatically also included in group.
        """
        return self.call_api('group')

    def ungroup(self):
        """
        Ungroup currently selected group.
        """
        return self.call_api('ungroup')

    def toggle_outline(self):
        """
        Outline is a small window that shows an overview of graph. It usually
        starts disabled and can be shown on demand.
        """
        self.call_api('toggleOutline', sync=False)

    def toggle_grid(self):
        """
        The grid in background of graph helps aligning cells inside graph. It
        usually starts enabled and can be hidden on demand.
        """
        self.call_api('toggleGrid', sync=False)

    def toggle_snap(self):
        """
        Snap feature forces vertices to be moved in a way its bounds match
        grid. It usually starts enabled and can be disabled on demand.

        Note that if grid is hidden this feature is also disabled.
        """
        self.call_api('toggleSnap', sync=False)

    def get_cell_id_at(self, x, y):
        """
        Gets the id of cell at given coordinates.

        :param int x: X coordinate in screen coordinates.
        :param int y: Y coordinate in screen coordinates.
        :rtype: str|None
        :return: Id of cell if any given position, otherwise returns None.
        """
        return self.call_api('getCellIdAt', x, y)

    def get_decoration_parent_cell_id(self, cell_id):
        """
        Get the id of the edge that contains the decoration with the given
        cell id.

        :param str cell_id: THe decoration's id.
        :rtype: str
        :return: Id of the edge containg the given decoration.
        """
        return self.call_api('getDecorationParentCellId', cell_id)

    def has_cell(self, cell_id):
        """
        Indicates if cell exists.

        :param str cell_id: Id of a cell in graph.
        :rtype: bool
        :return: True if cell exists.
        """
        return self.call_api('hasCell', cell_id)

    def has_port(self, cell_id, port_name):
        """
        Indicates if the port exists.

        :param str cell_id: Id of a cell in graph.
        :param str port_name: Name of the expected port.
        :rtype: bool
        :return: True if the port exists.
        """
        return self.call_api('hasPort', cell_id, port_name)

    def get_cell_type(self, cell_id):
        """
        :param str cell_id: Id of a cell in graph.
        :rtype: str
        :return: Possible returns are:

            - :data:`qmxgraph.constants.CELL_TYPE_VERTEX` for vertices;
            - :data:`qmxgraph.constants.CELL_TYPE_EDGE` for edges;
            - :data:`qmxgraph.constants.CELL_TYPE_DECORATION` for decorations;
            - :data:`qmxgraph.constants.CELL_TYPE_TABLE` for tables;

            It raises if none of these types are a match.
        """
        return self.call_api('getCellType', cell_id)

    def get_geometry(self, cell_id):
        """
        Gets the geometry of cell in screen coordinates.

        :param str cell_id: Id of a cell in graph.
        :rtype: list
        :return: A list with 4 items:

            - x;
            - y;
            - width;
            - height;

        """
        return self.call_api('getGeometry', cell_id)

    def get_terminal_points(self, cell_id):
        """
        Gets the terminal points of an edge;

        :param str cell_id: Id of a edge in graph.
        :rtype: list
        :return: 2 lists with 2 items each:

            - - the source x coordinate;
              - the source y coordinate;

            - - the target x coordinate;
              - the target y coordinate;

        """
        return self.call_api('getEdgeTerminalPoints', cell_id)

    def get_decoration_position(self, cell_id):
        """
        Gets the decoration's relative position.

        :param str cell_id: Id of a decoration in graph.
        :rtype: float
        :return: Returns an a normalized number between [0, 1] representing
            the position of the decoration along the parent edge.
        """
        return self.call_api('getDecorationPosition', cell_id)

    def set_decoration_position(self, cell_id, position):
        """
        Gets the decoration's relative position.

        :param str cell_id: Id of a decoration in graph.
        :param float position: A normalized number between [0, 1] representing
            the position of the decoration along the parent edge.
        """
        return self.call_api('setDecorationPosition', cell_id, position)

    def set_visible(self, cell_id, visible):
        """
        Change visibility state of cell.

        :param str cell_id: Id of a cell in graph.
        :param bool visible: If visible or not.
        """
        return self.call_api('setVisible', cell_id, visible)

    def is_visible(self, cell_id):
        """
        Indicates the cell's visibility.

        :param str cell_id: Id of a cell in graph.
        """
        return self.call_api('isVisible', cell_id)

    def set_port_visible(self, cell_id, port_name, visible):
        """
        Change visibility state of cell's port.

        :param str cell_id: Id of a cell in graph.
        :param str port_name: Name of a port in the cell.
        :param bool visible: If visible or not.
        """
        return self.call_api('setPortVisible', cell_id, port_name, visible)

    def is_port_visible(self, cell_id, port_name):
        """
        Indicates the cell's visibility.

        :param str cell_id: Id of a cell in graph.
        :param bool port_name: Name of a port in the cell.
        """
        return self.call_api('isPortVisible', cell_id, port_name)

    def set_connectable(self, cell_id, connectable):
        """
        Change connectable state of a cell.

        :param str cell_id: Id of a cell in graph.
        :param bool connectable: If connectable or not.
        """
        self.call_api('setConnectable', cell_id, connectable)

    def is_connectable(self, cell_id):
        """
        Indicates the cell's connectivity.

        :param str cell_id: Id of a cell in graph.
        """
        return self.call_api('isConnectable', cell_id)

    def zoom_in(self):
        """
        Zoom in the graph.
        """
        self.call_api('zoomIn', sync=False)

    def zoom_out(self):
        """
        Zoom out the graph.
        """
        self.call_api('zoomOut', sync=False)

    def reset_zoom(self):
        """
        Reset graph's zoom.
        """
        self.call_api('resetZoom', sync=False)

    def fit(self):
        """
        Rescale the graph to fit in the container.
        """
        self.call_api('fit', sync=False)

    def get_zoom_scale(self):
        """
        Return the current scale (zoom).

        :rtype: float
        """
        return self.call_api('getZoomScale')

    def get_scale_and_translation(self):
        """
        Get the current scale and translation.

        :rtype: Tuple[float, float, float]
        :return: The values represent:

            - graph scale;
            - translation along the x axis;
            - translation along the y axis;

            The three values returned by this function is suitable to be
            supplied to :func:`QmxGraphApi.set_scale_and_translation` to
            set the scale and translation to a previous value.
        """
        return tuple(self.call_api('getScaleAndTranslation'))

    def set_scale_and_translation(self, scale, x, y):
        """
        Set the scale and translation.

        :param float scale: The new graph's scale (1 = 100%).
        :param float x: The new graph's translation along the X axis
            (0 = origin).
        :param float y: The new graph's scale along the Y axis (0 = origin}.
        """
        return self.call_api('setScaleAndTranslation', scale, x, y)

    def set_selected_cells(self, cell_ids):
        """
        Select the cells with the given ids.

        :param list[str] cell_ids:
        """
        return self.call_api('setSelectedCells', cell_ids)

    def get_selected_cells(self):
        """
        Get the selected cells ids.

        :rtype: list[str]
        """
        return self.call_api('getSelectedCells')

    def remove_cells(self, cell_ids, ignore_missing_cells=False):
        """
        Remove cells from graph.

        :param list cell_ids: Ids of cells that must be removed.
        :param bool ignore_missing_cells: Ids of non existent cells are
            ignored instead raising an error.
        """
        return self.call_api('removeCells', cell_ids, ignore_missing_cells)

    def remove_port(self, vertex_id, port_name):
        """
        Remove an existing port from a vertex. Any edge connected to the
        vertex through the port is also removed.

        :param str vertex_id: The id of the parent vertex.
        :param str port_name: The port's name to remove.
        """
        return self.call_api('removePort', vertex_id, port_name)

    def register_double_click_handler(self, handler, *, check_api=True):
        """
        Set the handler used for double click in cells of graph.

        Unlike other event handlers, double click is exclusive to a single
        handler. This follows underlying mxGraph implementation that works in
        this manner, with the likely intention of enforcing a single
        side-effect happening when a cell is double clicked.

        Requires that a bridge object is first added to JavaScript to work.

        :param handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives a
            str with double clicked cell id as only argument.
        """
        return self.call_api(
            'registerDoubleClickHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def register_popup_menu_handler(self, handler, *, check_api=True):
        """
        Set the handler used for popup menu (i.e. menu triggered by right
        click) in cells of graph.

        Unlike other event handlers, popup menu is exclusive to a single
        handler. This follows underlying mxGraph implementation that works in
        this manner, with the likely intention of enforcing a single
        side-effect happening when a cell is right-clicked.

        Requires that a bridge object is first added to JavaScript to work.

        :param handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives,
            respectively, id of cell that was right-clicked, X coordinate in
            screen coordinates and Y coordinate in screen coordinates as its
            three arguments.
        """
        return self.call_api(
            'registerPopupMenuHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def register_label_changed_handler(self, handler, *, check_api=True):
        """
        Register a handler to event when label of a cell changes in graph.

        Requires that a bridge object is first added to JavaScript to work.

        :param str handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives,
            respectively, cell id, new label and old label as arguments.
        """
        return self.call_api(
            'registerLabelChangedHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def register_cells_added_handler(self, handler, *, check_api=True):
        """
        Register a handler to event when cells are added from graph.

        Requires that a bridge object is first added to JavaScript to work.

        :param str handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives a
            `QVariantList` of added cell ids as only argument.
        """
        return self.call_api(
            'registerCellsAddedHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def register_cells_removed_handler(self, handler, *, check_api=True):
        """
        Register a handler to event when cells are removed from graph.

        Requires that a bridge object is first added to JavaScript to work.

        :param str handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives a
            `QVariantList` of removed cell ids as only argument.
        """
        return self.call_api(
            'registerCellsRemovedHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def register_selection_changed_handler(self, handler, *, check_api=True):
        """
        Add function to handle selection change events in the graph.

        :param handler: Name of signal bound to JavaScript by a bridge object
            that is going to be used as callback to event. Receives an list of
            str with selected cells ids as only argument.
        """
        return self.call_api(
            'registerSelectionChangedHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def register_terminal_changed_handler(self, handler, *, check_api=True):
        """
        Add function to handle terminal change events in the graph.

        :param handler: Name of signal bound to JavaScript by a bridge object
            that is going to be used as callback to event. Receives,
            respectively, cell id, boolean indicating if the changed terminal
            is the source (or target), id of the net terminal, id of the old
            terminal.
        """
        return self.call_api(
            'registerTerminalChangedHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def register_terminal_with_port_changed_handler(self, handler, *, check_api=True):
        """
        Add function to handle terminal change with port info events in
        the graph.

        :param handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives,
            respectively, cell id, boolean indicating if the changed
            terminal is the source (or target), id of the new terminal,
            id of the old terminal.
        """
        return self.call_api(
            'registerTerminalWithPortChangedHandler',
            qmxgraph.js.Variable(handler),
            check_api=check_api,
        )

    def register_view_update_handler(self, handler, *, check_api=True):
        """
        Add function to handle updates in the graph view.
        :param handler: Name of signal bound to JavaScript by a bridge object
            that is going to be used as callback to event. Receives,
            respectively, graph dump and graph scale and translation.
        """
        return self.call_api(
            'registerViewUpdateHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def register_cells_bounds_changed_handler(self, handler, *, check_api=True):
        """
        Add function to handle updates in the graph view.
        :param handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives
            a map of cell id to a map describing the cell bounds.

        """
        return self.call_api(
            'registerBoundsChangedHandler', qmxgraph.js.Variable(handler), check_api=check_api
        )

    def resize_container(self, width, height, *, check_api=True):
        """
        Resizes the container of graph drawing widget.

        Note that new dimensions have lesser priority than keeping graph big
        enough to contain all existing vertices and edges. So if new dimensions
        are too small to contain all parts of graph it will be only resized
        down to dimensions enough to contain all parts.

        :param int width: New width.
        :param int height: New height.
        """
        self.call_api('resizeContainer', width, height, sync=False, check_api=check_api)

    def get_label(self, cell_id):
        """
        Gets the label of cell.

        :param str cell_id: Id of a cell in graph.
        :rtype: str
        :return: Label of cell.
        """
        return self.call_api('getLabel', cell_id)

    def set_label(self, cell_id, label):
        """
        Sets the label of a cell.

        :param str cell_id: Id of a cell in graph.
        :param str label: New label.
        """
        return self.call_api('setLabel', cell_id, label)

    def set_style(self, cell_id, style):
        """
        Sets a cell's style.

        :param str cell_id: Id of a cell in graph.
        :param str style: Name of a style or an inline style.
        """
        return self.call_api('setStyle', cell_id, style)

    def get_style(self, cell_id):
        """
        Gets a cell's style.

        :param str cell_id: Id of a cell in graph.
        :rtype: str
        :return: Name of a style or an inline style.
        """
        return self.call_api('getStyle', cell_id)

    def set_tag(self, cell_id, tag_name, tag_value):
        """
        Sets a tag in cell.

        :param str cell_id: Id of a cell in graph.
        :param str tag_name: Name of tag.
        :param str tag_value: Value of tag.
        """
        return self.call_api('setTag', cell_id, tag_name, tag_value)

    def get_tag(self, cell_id, tag_name):
        """
        Gets value of a value in cell.

        :param str cell_id: Id of a cell in graph.
        :param str tag_name: Name of tag.
        :rtype: str
        :return: Value of tag.
        """
        return self.call_api('getTag', cell_id, tag_name)

    def has_tag(self, cell_id, tag_name):
        """
        If cell has tag.

        :param str cell_id: Id of a cell in graph.
        :param str tag_name: Name of tag.
        :rtype: bool
        :return: True if tag exists in cell.
        """
        return self.call_api('hasTag', cell_id, tag_name)

    def get_edge_terminals(self, edge_id):
        """
        Gets the ids of endpoint vertices of an edge.

        :param str edge_id: Id of an edge in graph.
        :rtype: list[str]
        :return: A list with 2 items, first the source vertex id and second
            the target vertex id.
        """
        return self.call_api('getEdgeTerminals', edge_id)

    def get_edge_terminals_with_ports(self, edge_id):
        """
        Gets the ids of endpoint vertices of an edge and the ports used in the
        connection.

        :param str edge_id: Id of an edge in graph.
        :rtype: list[list[str|None]]
        :return: 2 lists with 2 items each:

            - - the source vertex id;
              - the port's name used on the source (can be `None`);

            - - the target vertex id;
              - the port's name used on the target (can be `None`);

        """
        return self.call_api('getEdgeTerminalsWithPorts', edge_id)

    def set_edge_terminal(self, edge_id, terminal_type, new_terminal_cell_id, port_name=None):
        """
        Set an edge's terminal.

        :param str edge_id: The id of a edge in graph.
        :param str terminal_type: Indicates if the affect terminal is the
            source or target for the edge. The valid values are:
            - `QmxGraphApi.SOURCE_TERMINAL_CELL`;
            - `QmxGraphApi.TARGET_TERMINAL_CELL`;
        :param new_terminal_cell_id: The if of the new terminal for the edge.
        :param str port_name: The of the port to use in the connection.
        """
        valid_terminal_types = {
            self.SOURCE_TERMINAL_CELL,
            self.TARGET_TERMINAL_CELL,
        }
        if terminal_type not in valid_terminal_types:
            err_msg = '%s is not a valid value for `terminal_type`'
            raise ValueError(err_msg % (terminal_type,))

        return self.call_api(
            'setEdgeTerminal', edge_id, terminal_type, new_terminal_cell_id, port_name
        )

    def get_cell_bounds(self, cell_id):
        """
        Set an cell's geometry. If some argument is omitted (or `None`) that
        geometry's characteristic is not affected.

        :param str cell_id: The id of a cell in graph.
        :rtype: qmxgraph.cell_bounds.CellBounds
        """
        from qmxgraph.cell_bounds import CellBounds

        cell_bounds = self.call_api('getCellBounds', cell_id)
        return CellBounds(**cell_bounds)

    def set_cell_bounds(self, cell_id, cell_bounds):
        """
        Set an cell's geometry. If some argument is omitted (or `None`) that
        geometry's characteristic is not affected.

        :param str cell_id: The id of a cell in graph.
        :param qmxgraph.cell_bounds.CellBounds cell_bounds: The cell bounds to apply.
        """
        from qmxgraph.cell_bounds import asdict

        return self.call_api('setCellBounds', cell_id, asdict(cell_bounds))

    def dump(self):
        """
        Obtain a representation of the current state of the graph as an XML
        string. The state can be restored calling :func:`QmxGraphApi.restore`.

        :rtype: str
        :return: A xml string.
        """
        return self.call_api('dump')

    def restore(self, state):
        """
        Restore the graph's state to one saved with `dump`.

        :param str state: A xml string previously obtained with `dump`.
        """
        return self.call_api('restore', state)

    def set_interaction_enabled(self, enabled):
        self.call_api('setInteractionEnabled', enabled)

    def set_cells_deletable(self, enabled):
        self.call_api('setCellsDeletable', enabled)

    def is_cells_deletable(self):
        return self.call_api('isCellsDeletable')

    def set_cells_disconnectable(self, enabled):
        self.call_api('setCellsDisconnectable', enabled)

    def is_cells_disconnectable(self):
        return self.call_api('isCellsDisconnectable')

    def set_cells_editable(self, enabled):
        self.call_api('setCellsEditable', enabled)

    def is_cells_editable(self):
        return self.call_api('isCellsEditable')

    def set_cells_movable(self, enabled):
        self.call_api('setCellsMovable', enabled)

    def is_cells_movable(self):
        return self.call_api('isCellsMovable')

    def set_cells_connectable(self, enabled):
        self.call_api('setCellsConnectable', enabled)

    def is_cells_connectable(self):
        return self.call_api('isCellsConnectable')

    def run_layout(self, layout_name):
        return self.call_api('runLayout', layout_name)

    def call_api(self, fn: str, *args, sync=True, check_api=True):
        """
        Call a function in underlying API provided by JavaScript graph.

        :param fn: A function call available in API.
        :param args: Positional arguments passed to graph's
            JavaScript API call (unfortunately can't use named arguments
            with JavaScript). All object passed must be JSON encodable or
            Variable instances.
        :rtype: object
        :return: Return of API call.
        """
        with self._call_context_manager_factory():
            return self._call_api(fn, *args, sync=sync, check_api=check_api)

    def _call_api(self, fn: str, *args, sync, check_api: bool = True):
        graph = self._graph()
        eval_js = graph.inner_web_view().eval_js
        call = f'api.{qmxgraph.js.prepare_js_call(fn, *args)}'

        if qmxgraph.debug.is_qmxgraph_debug_enabled():
            call = textwrap.dedent(
                f'''
                if (
                    (typeof graphs === "undefined")
                    || !graphs.isRunning()
                ) {{
                    throw Error(
                        '[QmxGraph] `graphs` must be loaded and running'
                    );
                }}
                if (typeof api === "undefined") {{
                    throw Error('[QmxGraph] `api` must be loaded');
                }}
                if (!api.{fn}) {{
                    throw Error(
                        '[QmxGraph] unable to find function "{fn}"'
                        + ' in javascript api'
                    );
                }}
                {call};
                '''
            )
            # Capture all warning messages from Qt.
            capture_context = _capture_critical_log_messages()
        else:
            capture_context = nullcontext([])

        with capture_context as messages:
            result = eval_js(call, sync=sync, check_api=check_api)

        # Raise an error if we captured any critical messages.
        # Capturing will only happen if debugging is enabled,
        # so we don't need to check it again here.
        if messages:
            raise InvalidJavaScriptError("\n".join(messages))

        return result


@contextmanager
def _capture_critical_log_messages() -> Generator[List[str], None, None]:
    """
    Installs a handler for the internal Qt warnings system capturing messages
    of type QtCriticalMsg. The context manager returns a list of captured messages,
    which can be inspected after the context manager ends.
    """
    from PyQt5.QtCore import QtCriticalMsg
    from PyQt5.QtCore import qInstallMessageHandler

    messages = []

    def handle_message(msg_type, context, message):
        if msg_type == QtCriticalMsg:
            messages.append(message)

    previous_handler = qInstallMessageHandler(handle_message)
    try:
        yield messages
    finally:
        qInstallMessageHandler(previous_handler)


if sys.version_info[:] < (3, 7):

    @contextmanager
    def nullcontext(enter_result=None):
        yield enter_result


else:
    from contextlib import nullcontext
