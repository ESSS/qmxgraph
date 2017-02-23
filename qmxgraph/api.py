import weakref

import qmxgraph.debug
import qmxgraph.js


class QmxGraphApi(object):
    """
    Python binding for API used to control underlying JavaScript's mxGraph
    graph drawing library.
    """

    def __init__(self, graph):
        """
        :param qmxgraph.widget.QmxGraph graph: A graph drawing widget.
        """
        self._graph = weakref.ref(graph)

    def insert_vertex(self, x, y, width, height, label, style=None, tags=None):
        """
        Inserts a new vertex in graph.

        :param int x: X coordinate in screen coordinates.
        :param int y: Y coordinate in screen coordinates.
        :param int width: Width in pixels.
        :param int height: Height in pixels.
        :param str|None label: Label of vertex, can be omitted.
        :param str|None style: Name of style to be used. Styles
            available are all default ones provided by mxGraph plus additional
            ones configured in initialization of this class.
        :param dict[str, str]|None tags: Tags are basically custom
            attributes that may be added to a cell that may be later queried
            (or even modified), with the objective of allowing better
            inspection and interaction with cells in a graph.
        :rtype: str
        :return: Id of new vertex.
        """
        return self.call_api(
            'insertVertex', x, y, width, height, label, style, tags)

    def insert_edge(self, source_id, target_id, label, style=None, tags=None):
        """
        Inserts a new edge between two vertices in graph.

        :param str source_id: Id of source vertex in graph.
        :param str target_id: Id of target vertex in graph.
        :param str|None label: Label of edge, can be omitted.
        :param str|None style: Name of style to be used. Styles
            available are all default ones provided by mxGraph plus additional
            ones configured in initialization of this class.
        :param dict[str, str]|None tags: Tags are basically custom
            attributes that may be added to a cell that may be later queried
            (or even modified), with the objective of allowing better
            inspection and interaction with cells in a graph.
        :rtype: str
        :return: Id of new edge.
        """
        return self.call_api(
            'insertEdge', source_id, target_id, label, style, tags)

    def insert_decoration(
            self, x, y, width, height, label, style=None, tags=None):
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
        :param str|None style: Name of style to be used. Styles
            available are all default ones provided by mxGraph plus additional
            ones configured in initialization of this class.
        :param dict[str, str]|None tags: Tags are basically custom
            attributes that may be added to a cell that may be later queried
            (or even modified), with the objective of allowing better
            inspection and interaction with cells in a graph.
        :rtype: str
        :return: Id of new decoration.
        """
        return self.call_api(
            'insertDecoration', x, y, width, height, label, style, tags)

    def insert_table(self, x, y, width, contents, title, tags=None):
        """
        Inserts a new table in graph. A table is an object that can be used
        in graph to display tabular information about other cells, for
        instance. Tables can't be connected to other cells like vertices,
        edges nor decorations.

        :param int x: X coordinate in screen coordinates.
        :param int y: Y coordinate in screen coordinates.
        :param int width: Width in pixels.
        :param list[list[str]] contents: A list of lists. The 1st level lists
            correspond to rows. The 2nd level lists correspond to columns of
            each row.
        :param str title: Title of table.
        :param dict[str, str]|None tags: Tags are basically custom
            attributes that may be added to a cell that may be later queried
            (or even modified), with the objective of allowing better
            inspection and interaction with cells in a graph.
        :rtype: str
        :return: Id of new table.
        """
        return self.call_api('insertTable', x, y, width, contents, title, tags)

    def update_table(self, table_id, contents, title):
        """
        Update contents and title of a table in graph.

        :param str table_id: Id of a table in graph.
        :param list contents: A list of lists. The 1st level lists correspond
            to rows. The 2nd level lists correspond to columns of each row.
        :param str title: Title of table.
        """
        return self.call_api('updateTable', table_id, contents, title)

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
        return self.call_api('toggleOutline')

    def toggle_grid(self):
        """
        The grid in background of graph helps aligning cells inside graph. It
        usually starts enabled and can be hidden on demand.
        """
        return self.call_api('toggleGrid')

    def toggle_snap(self):
        """
        Snap feature forces vertices to be moved in a way its bounds match
        grid. It usually starts enabled and can be disabled on demand.

        Note that if grid is hidden this feature is also disabled.
        """
        return self.call_api('toggleSnap')

    def get_cell_id_at(self, x, y):
        """
        Gets the id of cell at given coordinates.

        :param int x: X coordinate in screen coordinates.
        :param int y: Y coordinate in screen coordinates.
        :rtype: str|None
        :return: Id of cell if any given position, otherwise returns None.
        """
        return self.call_api('getCellIdAt', x, y)

    def has_cell(self, cell_id):
        """
        Indicates if cell exists.

        :param str cell_id: Id of a cell in graph.
        :rtype: bool
        :return: True if cell exists.
        """
        return self.call_api('hasCell', cell_id)

    def get_cell_type(self, cell_id):
        """
        :param str cell_id: Id of a cell in graph.
        :rtype: str
        :return: Possible returns are:
            * qmxgraph.constants.CELL_TYPE_VERTEX for vertices
            * qmxgraph.constants.CELL_TYPE_EDGE for edges
            * qmxgraph.constants.CELL_TYPE_DECORATION for decorations
            * qmxgraph.constants.CELL_TYPE_TABLE for tables

            It raises if none of these types are a match.
        """
        return self.call_api('getCellType', cell_id)

    def get_geometry(self, cell_id):
        """
        Gets the geometry of cell in screen coordinates.

        :param str cell_id: Id of a cell in graph.
        :rtype: list
        :return: List composed, respectively, by x, y, width and height.
        """
        return self.call_api('getGeometry', cell_id)

    def set_visible(self, cell_id, visible):
        """
        Change visibility state of cell.

        :param str cell_id: Id of a cell in graph.
        :param bool visible: If visible or not.
        """
        return self.call_api('setVisible', cell_id, visible)

    def remove_cells(self, cell_ids):
        """
        Remove cells from graph.

        :param list cell_ids: Ids of cells that must be removed.
        """
        return self.call_api('removeCells', cell_ids)

    def set_double_click_handler(self, handler):
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
            'setDoubleClickHandler', qmxgraph.js.Variable(handler))

    def set_popup_menu_handler(self, handler):
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
            'setPopupMenuHandler', qmxgraph.js.Variable(handler))

    def on_label_changed(self, handler):
        """
        Register a handler to event when label of a cell changes in graph.

        Requires that a bridge object is first added to JavaScript to work.

        :param str handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives,
            respectively, cell id, new label and old label as arguments.
        """
        return self.call_api(
            'onLabelChanged', qmxgraph.js.Variable(handler))

    def on_cells_added(self, handler):
        """
        Register a handler to event when cells are added from graph.

        Requires that a bridge object is first added to JavaScript to work.

        :param str handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives a
            `QVariantList` of added cell ids as only argument.
        """
        return self.call_api('onCellsAdded', qmxgraph.js.Variable(handler))

    def on_cells_removed(self, handler):
        """
        Register a handler to event when cells are removed from graph.

        Requires that a bridge object is first added to JavaScript to work.

        :param str handler: Name of signal bound to JavaScript by a bridge
            object that is going to be used as callback to event. Receives a
            `QVariantList` of removed cell ids as only argument.
        """
        return self.call_api('onCellsRemoved', qmxgraph.js.Variable(handler))

    def resize_container(self, width, height):
        """
        Resizes the container of graph drawing widget.

        Note that new dimensions have lesser priority than keeping graph big
        enough to contain all existing vertices and edges. So if new dimensions
        are too small to contain all parts of graph it will be only resized
        down to dimensions enough to contain all parts.

        :param int width: New width.
        :param int height: New height.
        """
        return self.call_api('resizeContainer', width, height)

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

    def dump(self):
        """
        Obtain a representation of the current state of the graph as an XML
        string. The state can be restored calling `restore`.

        :rtype: str
        :return: A xml string.
        """
        return self.call_api('dump')

    def restore(self, state):
        """
        Restore the graph's state to one saved with `dump`.

        :param str state: A xml string previously obtained with `bump`.
        """
        return self.call_api('restore', state)

    def call_api(self, fn, *args):
        """
        Call a function in underlying API provided by JavaScript graph.

        :param str|Variable fn: A function call available in API.
        :param list args: Positional arguments passed to graph's JavaScript API
            call (unfortunately can't use named arguments with JavaScript).
        :rtype: object
        :return: Return of API call.
        """
        eval_js = self._graph().inner_web_view().eval_js
        if qmxgraph.debug.is_qmxgraph_debug_enabled():
            # Healthy check as if function didn't exist it just returns None,
            # giving the impression that might have worked
            if eval_js("!api.{}".format(fn)):
                raise qmxgraph.js.InvalidJavaScriptError(
                    'Unable to find function "{}" in QmxGraph '
                    'JavaScript API'.format(fn))

        call = qmxgraph.js.prepare_js_call(fn, *args)
        return eval_js("api.{}".format(call))
