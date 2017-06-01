/**
 * The actual javascript implementation
 */

/*global mxConstants */
/*global mxEvent */
/*global mxGraph */
/*global mxPoint */
/*global mxUtils */

/*global graphs */

/*global namespace */

namespace('graphs');

/**
 * A public API made available so other clients can communicate with graph
 * drawing widget, aiming to streamline and standardize some actions over graph.
 *
 * @param {mxEditor} graphEditor A graph drawing widget.
 * @constructor
 */
graphs.Api = function Api (graphEditor) {
    "use strict";

    this._graphEditor = graphEditor;
};

/**
 * Inserts a new vertex in an arbitrary position in graph.
 *
 * @param {number} x X coordinate in screen coordinates
 * @param {number} y Y coordinate in screen coordinates
 * @param {number} width Width of vertex.
 * @param {number} height Height of vertex.
 * @param {string} [label] Label of vertex.
 * @param {string} [style] Name of a style or an inline style.
 * @param {Object} [tags] A dict-like object, with string keys and values. Tags are basically custom
 * attributes that may be added to a cell that may be later queried (or even modified), with the
 * objective of allowing better inspection and interaction with cells in a graph.
 * @returns {number} Id of new vertex.
 */
graphs.Api.prototype.insertVertex = function insertVertex (
    x, y, width, height, label, style, tags) {
    "use strict";

    var graph = this._graphEditor.graph;
    var coords = graphs.utils.adjustCoordinates(graph, x, y);

    var value = this._prepareCellValue(label, tags);
    var parent = graph.getDefaultParent();
    var vertex = graph.insertVertex(
        parent,
        null,
        value,
        coords.x,
        coords.y,
        width,
        height,
        style
    );

    graphs.utils.resizeContainerOnDemand(graph, vertex);

    return vertex.getId();
};

graphs.Api.prototype._getPortId = function _getPortId (vertexId, name) {
    return mxCell._PORT_ID_PREFIX + vertexId + '-' + name;
};

/**
 * Inserts a new port in vertex.
 *
 * @param {number} vertexId The id of the vertex to witch add this port.
 * @param {string} portName The name used to refer to the new port.
 * @param {number} x The normalized (0-1) X coordinate for the port (relative to vertex bounds).
 * @param {number} y The normalized (0-1) Y coordinate for the port (relative to vertex bounds).
 * @param {number} width Width of port.
 * @param {number} height Height of port.
 * @param {string} [label] Label of port.
 * @param {string} [style] Name of a style or an inline style.
 * @param {Object} [tags] A dict-like object, with string keys and values. Tags are basically custom
 * attributes that may be added to a cell that may be later queried (or even modified), with the
 * objective of allowing better inspection and interaction with cells in a graph.
 * @throws {Error} If vertex isn't found in graph.
 * @throws {Error} If a port with the same name is already present for the given vertex.
 */
graphs.Api.prototype.insertPort = function insertPort (
    vertexId, portName, x, y, width, height, label, style, tags) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var parent = this._findCell(model, vertexId);
    this._findPort(model, vertexId, portName, false);
    var portId = this._getPortId(vertexId, portName);

    var value = this._prepareCellValue(label, tags);
    model.beginUpdate();
    try {
        var port = graph.insertVertex(
            parent,
            portId,
            value,
            x,
            y,
            width,
            height,
            style,
            true
        );
        // Center port on given (x,y) coordinates.
        port.geometry.offset = new mxPoint(-width / 2, -height / 2);
    } finally {
        model.endUpdate();
    }
    graphs.utils.resizeContainerOnDemand(graph, port);
};

/**
 * Inserts a new edge between two vertices in graph.
 *
 * @param {number} sourceId Id of a source vertex in graph.
 * @param {number} targetId Id of a source vertex in graph.
 * @param {string} [label] Label of edge.
 * @param {string} [style] Name of a style or an inline style.
 * @param {Object} [tags] A dict-like object, with string keys and values. Tags are basically custom
 * attributes that may be added to a cell that may be later queried (or even modified), with the
 * objective of allowing better inspection and interaction with cells in a graph.
 * @param {string} [sourcePortName] The name of the port used to connect on the source vertex. If a
 * falsy value is used no port is used.
 * @param {string} [targetPortName] The name of the port used to connect on the target vertex. If a
 * falsy value is used no port is used.
 * @returns {number} Id of new edge.
 * @throws {Error} If source or target aren't found in graph.
 * @throws {Error} If the source or target ports aren't found in the respective vertices.
 */
graphs.Api.prototype.insertEdge = function insertEdge (
    sourceId, targetId, label, style, tags, sourcePortName, targetPortName) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();

    var parent = graph.getDefaultParent();
    var value = this._prepareCellValue(label, tags);

    var source = this._findCell(model, sourceId);
    if (sourcePortName) {
        source = this._findPort(model, sourceId, sourcePortName, true);
    }
    var target = this._findCell(model, targetId);
    if (targetPortName) {
        source = this._findPort(model, targetId, targetPortName, true);
    }

    var edge = graph.insertEdge(parent, null, value, source, target, style);

    return edge.getId();
};

/**
 * Inserts a decoration over an edge in graph. A decoration is basically an
 * object used as overlay in edges, to show objects present along its path.
 *
 * If given position doesn't match any edges, it will throw, as every decoration
 * must have an edge as its parent.
 *
 * @param {number} x X coordinate in screen coordinates
 * @param {number} y Y coordinate in screen coordinates
 * @param {number} width Width of decoration.
 * @param {number} height Height of decoration.
 * @param {string} label Label of decoration.
 * @param {string} [style] Name of a style or an inline style.
 * @param {Object} [tags] A dict-like object, with string keys and values. Tags are basically custom
 * attributes that may be added to a cell that may be later queried (or even modified), with the
 * objective of allowing better inspection and interaction with cells in a graph.
 * @returns {number} Id of new decoration.
 */
graphs.Api.prototype.insertDecoration = function insertDecoration (
    x, y, width, height, label, style, tags) {
    "use strict";

    var graph = this._graphEditor.graph;
    var parent = graph.getDefaultParent();
    var edge = graph.getCellAt(x, y, parent, false, true);

    if (edge === null) {
        throw Error("Could not find an edge at position and can only add a " +
            "decoration over an edge.");
    }

    // Need terminal positions to be able to determine correct relative position
    // of decoration in relation to its parent edge.
    var view = graph.view;
    var sourcePort = view.getTerminalPort(
        view.getState(edge), view.getState(edge.getTerminal(true)), true);
    var targetPort = view.getTerminalPort(
        view.getState(edge), view.getState(edge.getTerminal(false)), false);

    var sourcePoint = view.getPerimeterPoint(
        sourcePort, new mxPoint(x, y), false);
    var targetPoint = view.getPerimeterPoint(
        targetPort, new mxPoint(x, y), false);

    var distance = function(a, b) {
        return Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2));
    };

    var total = distance(targetPoint, sourcePoint);
    var current = distance(sourcePoint, {x: x, y: y});

    // Relative position in edge
    var position = -1 + 2 * (current / total);

    style = graphs.utils.setStyleKey(style, 'labelPosition', 'left');
    style = graphs.utils.setStyleKey(style, 'align', 'right');

    var decorationStyle = graphs.utils.obtainDecorationStyle(graph, edge, style);

    var value = this._prepareCellValue(label, tags);

    var model = graph.getModel();
    model.beginUpdate();
    try {
        var decoration = graph.insertVertex(
            edge, null, value, position, 0, width, height, decorationStyle, true);
        decoration.geometry.offset = new mxPoint(-width / 2, -height / 2);
        decoration.connectable = false;
        decoration.__decoration__ = true;
    } finally {
        model.endUpdate();
    }

    return decoration.getId();
};

/**
 * Inserts a table in graph. A table is in general terms a vertex-like object
 * in graph that displays contents as a HTML table. A table is not connectable
 * to other vertices.
 *
 * The size of table is adjusted to its contents.
 *
 * @param {number} x X coordinate in screen coordinates
 * @param {number} y Y coordinate in screen coordinates
 * @param {number} width Width of table, may still be expanded because of contents though.
 * @param {(string|SpannedCellDesc)[][]} contents An array of arrays. The 1st level arrays
 * correspond to rows. The 2nd level arrays correspond to columns of each row.
 * @param {string} title Title of table.
 * @param {Object} [tags] A dict-like object, with string keys and values. Tags are basically custom
 * attributes that may be added to a cell that may be later queried (or even modified), with the
 * objective of allowing better inspection and interaction with cells in a graph.
 * @param {string} [style] An style name or inline style. The `'table'` style is always used but
 * options defined with this value will overwrite the option defined on the `'table'` style.
 * @param {number} [parentId] If supplied this makes the table position relative to this cell
 * @returns {number} Id of new table.
 * @throws {Error} If parentId  is supplied but isn't found in graph.
 */
graphs.Api.prototype.insertTable = function insertTable (
    x, y, width, contents, title, tags, style, parentId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var isRelative = parentId != null;
    var parent = null;
    if (isRelative) {
        parent = this._findCell(model, parentId);
    } else {
        parent = graph.getDefaultParent();
    }
    var coords = graphs.utils.adjustCoordinates(graph, x, y);

    var tableStyle = 'table';
    if (style != null) {
        tableStyle += ';' + style;
    }
    tableStyle = graphs.utils.setStyleKey(tableStyle, mxConstants.STYLE_OVERFLOW, 'fill');
    tableStyle = graphs.utils.setStyleKey(tableStyle, mxConstants.STYLE_CLONEABLE, false);

    var label = graphs.utils.createTableElement(contents, title);
    var value = this._prepareCellValue(label, tags);

    model.beginUpdate();
    var table = null;
    try {
        table = graph.insertVertex(
            parent,
            null,
            value,
            coords.x,
            coords.y,
            0,
            0,
            tableStyle,
            isRelative
        );
        table.__table__ = true;
        table.connectable = false;

        // Updates the height of the cell (override width
        // for table width is set to 100%)
        graph.updateCellSize(table);
    } finally {
        model.endUpdate();
    }

    graphs.utils.resizeContainerOnDemand(graph, table);
    return table.getId();
};

/**
 * Updates the contents and title of a table.
 *
 * @param {number} tableId Id of a table.
 * @param {Array} contents See {@linkcode graphs.Api.prototype.insertTable}.
 * @param {string} title See {@linkcode graphs.Api.prototype.insertTable}.
 * @throws {Error} Unable to find table or cell is not a table.
 */
graphs.Api.prototype.updateTable = function updateTable (tableId, contents, title) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var table = this._findCell(model, tableId);
    if (!table.isTable()) {
        throw Error("Cell is not a table");
    }

    var label = graphs.utils.createTableElement(contents, title);
    var value = table.cloneValue();
    value.setAttribute('label', label);
    model.beginUpdate();
    try {
        model.setValue(table, value);
        graph.updateCellSize(table);
    } finally {
        model.endUpdate();
    }
};

graphs.Api.prototype.setCollapsed = function setCollapsed (cellId, collapsed) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cell = this._findCell(model, cellId);
    model.beginUpdate();
    try {
        model.setCollapsed(cell, collapsed);
        graph.updateCellSize(cell);
    } finally {
        model.endUpdate();
    }
};

/**
 * Get type of cell by id.
 *
 * @param {number} cellId Id of a cell in graph.
 * @returns {"vertex"|"edge"|"table"|"decoration"} Type of cell.
 * @throws {Error} Cell not found.
 * @throws {Error} Could not determine type of cell.
 */
graphs.Api.prototype.getCellType = function getCellType (cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    if (!!cell) {
        var kind = null;
        if (cell.isDecoration()) {
            kind = "decoration";
        } else if (cell.isTable()) {
            kind = "table";
        } else if (cell.isVertex()) {
            kind = "vertex";
        } else if (cell.isEdge()) {
            kind = "edge";
        } else {
            throw Error("Unknown type of cell.");
        }
        return kind;
    }
    throw Error("Unable to find cell with id " + cellId);
};

/**
 * Gets the id of cell at given coordinates.
 *
 * @param {number} x X coordinate in screen coordinates
 * @param {number} y Y coordinate in screen coordinates
 * @returns {number|null} Id of cell if any given position, otherwise returns
 * null.
 */
graphs.Api.prototype.getCellIdAt = function getCellIdAt (x, y) {
    "use strict";

    var graph = this._graphEditor.graph;
    var parent = graph.getDefaultParent();
    var ignoreFn = function(state) {
        return state.cell.isPort();
    };
    var cell = graph.getCellAt(x, y, parent, true, true, ignoreFn);
    return !!cell? cell.getId() : null;
};


/**
 * Indicates if cell exists.
 *
 * @param {number} cellId Id of a cell in graph.
 * @returns {boolean} True if cell exists.
 */
graphs.Api.prototype.hasCell = function hasCell (cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    return !!graph.getModel().getCell(cellId);
};


/**
 * Gets the geometry of a cell.
 *
 * @param {number} cellId Id of a cell in graph.
 * @returns {Array} Returns an array with, respectively,
 * x in screen coordinates, y in screen coordinates, width and height.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.getGeometry = function getGeometry (cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    var bb = null;
    if (cell) {
        var state = graph.view.getState(cell);
        var x = state.x;
        var y = state.y;
        // TODO: further review if width and height need to use graph.view.scale
        bb = [x, y, state.width, state.height];
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }

    return bb;
};

/**
 * Show/hide a cell in graph.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {boolean} visible Visibility state.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.setVisible = function setVisible (cellId, visible) {
    "use strict";

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    if (cell) {
        graph.getModel().setVisible(cell, visible);
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }
};

/**
 * Indicates a cell's visibility.
 *
 * @param {number} cellId Id of a cell in graph.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.isVisible = function isVisible (cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cell = this._findCell(model, cellId);
    return model.isVisible(cell);
};

/**
 * Select the cells with the given ids.
 *
 * @param {number[]} cellIds An array with the ids of the cells to select.
 */
graphs.Api.prototype.setSelectedCells = function setSelectedCells (cellIds) {
    "use strict";

    var cellsToSelect = [];
    var model = api._graphEditor.graph.getModel();
    var cell = null;
    for (var i = cellIds.length; i--;) {
        cell = model.getCell(cellIds[i]);
        cellsToSelect.push(cell)
    }

    var selectionModel = this._graphEditor.graph.getSelectionModel();
    selectionModel.setCells(cellsToSelect);
};

/**
 * Get the ids of the selected cells.
 */
graphs.Api.prototype.getSelectedCells = function getSelectedCells () {
    "use strict";

    var selectionModel = this._graphEditor.graph.getSelectionModel();
    var cells = selectionModel.cells;
    var cellIds = [];
    for (var i = cells.length; i--;) {
        cellIds.push(cells[i].getId())
    }
    return cellIds;
};

/**
 * Groups the currently selected cells in graph.
 */
graphs.Api.prototype.group = function group () {
    "use strict";

    this._graphEditor.execute("group");
};

/**
 * Ungroups the currently selected group in graph.
 */
graphs.Api.prototype.ungroup = function ungroup () {
    "use strict";

    this._graphEditor.execute("ungroup");
};

/**
 * Shows/hides outline window of graph.
 */
graphs.Api.prototype.toggleOutline = function toggleOutline () {
    "use strict";

    this._graphEditor.execute("toggleOutline");
};

/**
 * Shows/hides grid in background of graph.
 */
graphs.Api.prototype.toggleGrid = function toggleGrid () {
    "use strict";

    this._graphEditor.execute("toggleGrid");
};

/**
 * Enables/disables snapping to grid of graph.
 */
graphs.Api.prototype.toggleSnap = function toggleSnap () {
    "use strict";

    this._graphEditor.execute("toggleSnap");
};

/**
 * Resizes the container of graph drawing widget.
 *
 * Note that new dimensions have lesser priority than keeping graph big enough
 * to contain all existing vertices and edges. So if new dimensions are
 * too small to contain all parts of graph it will be only resized down to
 * dimensions enough to contain all parts.
 *
 * @param {number} width New width.
 * @param {number} height New height.
 */
graphs.Api.prototype.resizeContainer = function resizeContainer (width, height) {
    "use strict";

    var parent = this._graphEditor.graph.getDefaultParent();
    var cells = this._graphEditor.graph.getChildCells(parent);

    // Graph dimensions must contain enough space for existing cells
    if (cells.length > 0) {
        var bbox = this._graphEditor.graph.getBoundingBox(cells);
        width = Math.max(width, bbox.x + bbox.width);
        height = Math.max(height, bbox.y + bbox.height);
    }

    this._graphEditor.graph.doResizeContainer(width, height);
};

/**
 * Remove cells from graph.
 *
 * @param {number[]} cellIds Ids of cells that must be removed.
 */
graphs.Api.prototype.removeCells = function removeCells (cellIds) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cells = cellIds.map(function(cellId) {
        return this._findCell(model, cellId);
    }, this);
    graph.removeCells(cells);
};

/**
 *
 * @param {number} vertexId The id of the vertex containing the port to remove.
 * @param {string} portName The name of the port to remove.
 * @throws {Error} If vertex isn't found in graph.
 * @throws {Error} If a port with the given name is not present in the vertex.
 */
graphs.Api.prototype.removePort = function removePort (vertexId, portName) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var parent = this._findCell(model, vertexId);

    var port = this._findPort(model, vertexId, portName, true);

    // This array will contain the port and edges connected on the parent vertex using the port.
    var cellsToRemove = [port];
    var edges = graph.getEdges(parent);
    for (var i = edges.length; i--;) {
        var terminals = this._getMxEdgeTerminalsWithPorts(edges[i]);
        if (
            (terminals[0] == vertexId && terminals[1] == portName)
            || (terminals[2] == vertexId && terminals[3] == portName)
        ){
            cellsToRemove.push(edges[i]);
        }
    }
    graph.removeCells(cellsToRemove);
};

/**
 * Register a handler to event when cells are removed from graph.
 *
 * @param {function} handler Callback that handles event. Receives an
 * {@linkCode Array} of removed cell ids as only argument.
 */
graphs.Api.prototype.onCellsRemoved = function onCellRemoved (handler) {
    "use strict";

    var graph = this._graphEditor.graph;

    var removeHandler = function(sender, evt) {
        var cells = evt.getProperty('cells');
        var cellIds = [];

        var findCellIds = function(cells) {
            for (var i = 0; i < cells.length; i++) {
                var cell = cells[i];
                if (cell.isPort()) {
                    // On qmxgraph ports are not considered cells.
                    // Cells are how they are modeled by the underling mxgraph library.
                    continue;
                }

                cellIds.push(cell.getId());

                // Decorations for instance are children of other cells
                // instead of default parent of graph. When remove event
                // comes from a cell with default parent, the original event
                // omits children cells that were also removed.
                findCellIds(graph.getModel().getChildCells(cell));
            }
        };
        findCellIds(cells);
        if (cellIds.length) {
            handler(cellIds);
        }
    };

    graph.addListener(mxEvent.CELLS_REMOVED, removeHandler);
};

/**
 * Register a handler to event when cells are added to graph.
 *
 * @param {function} handler Callback that handles event. Receives an
 * {@linkCode Array} of added cell ids as only argument.
 */
graphs.Api.prototype.onCellsAdded = function onCellsAdded (handler) {
    "use strict";

    var graph = this._graphEditor.graph;

    var addHandler = function(sender, evt) {
        var cells = evt.getProperty('cells');
        var cellIds = [];
        for (var i = 0; i < cells.length; i++) {
            var cell = cells[i];
            if (cell.isPort()) {
                // See comment about ports on `graphs.Api#onCellsRemoved`.
                continue;
            }
            cellIds.push(cell.getId());
        }
        if (cellIds.length) {
            handler(cellIds);
        }
    };

    graph.addListener(mxEvent.CELLS_ADDED, addHandler);
};

/**
 * Add function to handle selection change events in the graph.
 *
 * @param {function} handler Callback that handles event. Receives an array with the id of cells
 * that are selected as only argument.
 */
graphs.Api.prototype.onSelectionChanged = function onSelectionChanged (handler) {
    "use strict";

    var selectionHandler = function(source, event) {
        var selectedCells = source.cells;
        var selectedCellsIds = [];
        for (var i = selectedCells.length; i--;) {
            selectedCellsIds.push(selectedCells[i].getId());
        }
        handler(selectedCellsIds);
    };

    var selectionModel = this._graphEditor.graph.getSelectionModel();
    selectionModel.addListener(mxEvent.CHANGE, selectionHandler);
};


/**
 * Register a handler to event when cells have their label changed.
 *
 * @param {function} handler Callback that handles event. Receives, respectively, id of cell
 * that was renamed, its new label and its old label.
 */
graphs.Api.prototype.onLabelChanged = function onLabelChanged (handler) {
    "use strict";

    var graph = this._graphEditor.graph;

    var labelChangedHandler = function(sender, evt) {
        var cell = evt.getProperty('cell');
        var cellId = cell.getId();
        var newValue = evt.getProperty('value');
        var oldValue = evt.getProperty('old');
        handler(cellId, newValue, oldValue);
    };

    graph.addListener(mxEvent.LABEL_CHANGED, labelChangedHandler);
};

/**
 * Gets the label of a cell.
 *
 * @param {number} cellId Id of a cell in graph.
 * @returns {string} Label of cell.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.getLabel = function getLabel (cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    if (cell) {
        return graph.convertValueToString(cell) || '';
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }
};

/**
 * Sets the label of a cell.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {string} label New label.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.setLabel = function setLabel (cellId, label) {
    "use strict";

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    if (cell) {
        // `labelChanged` ensures that `mxEvent.LABEL_CHANGED` event is fired.
        graph.labelChanged(cell, label);
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }
};

/**
 * Sets the style of a cell.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {string} [style] Name of a style or an inline style.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.setStyle = function setStyle(cellId, style) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cell = this._findCell(model, cellId);
    model.setStyle(cell, style);  // Use the model to trigger mxStyleChange as needed.
};

/**
 *
 * @param cellId
 * @returns {string} Name of a style or an inline style.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.getStyle = function getStyle(cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cell = this._findCell(model, cellId);
    return cell.getStyle();
};

/**
 * Sets a tag in cell.
 *
 * Note that tag values are always coerced to string.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {string} tagName Name of tag.
 * @param {string} tagValue Value of tag.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.setTag = function setTag (cellId, tagName, tagValue) {
    "use strict";

    this._checkTagValue(tagName, tagValue);

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    if (cell) {
        if (!mxUtils.isNode(cell.value)) {
            var value = this._prepareCellValue(cell.value, null);
            cell.setValue(value);
        }
        var internalTagName = this._getInternalTag(tagName);
        cell.setAttribute(internalTagName, tagValue);
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }
};

/**
 * Gets value of a value in cell.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {string} tagName Name of a tag.
 * @returns {string} Value of tag.
 * @throws {Error} Unable to find cell.
 * @throws {Error} Unable to find tag.
 */
graphs.Api.prototype.getTag = function getTag (cellId, tagName) {
    "use strict";

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    if (cell) {
        if (mxUtils.isNode(cell.value)) {
            var internalTagName = this._getInternalTag(tagName);
            if (cell.hasAttribute(internalTagName)) {
                return cell.getAttribute(internalTagName, '');
            }
        }
        throw Error("Tag '" + tagName + "' not found in cell with id " + cellId);
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }
};

/**
 * If cell has tag.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {string} tagName Name of a tag.
 * @returns {boolean} True if tag exists in cell.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.hasTag = function hasTag (cellId, tagName) {
    "use strict";

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    if (cell) {
        if (mxUtils.isNode(cell.value)) {
            var internalTagName = this._getInternalTag(tagName);
            return cell.hasAttribute(internalTagName);
        } else {
            return false;
        }
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }
};

/**
 * Set the handler used for double click in cells of graph.
 *
 * Unlike other event handlers, double click is exclusive to a single handler. This follows
 * underlying mxGraph implementation that works in this manner, with the likely intention of
 * enforcing a single side-effect happening when a cell is double clicked.
 *
 * @param {function} handler Callback that handles event. Receives a id of cell that was double
 * clicked as only argument.
 */
graphs.Api.prototype.setDoubleClickHandler = function setDoubleClickHandler (handler) {
    "use strict";

    var doubleClickHandler = function(editor, cell) {
        var cellId = cell.getId();
        handler(cellId);
    };

    // We need to associate our action with a name in mxEditor's adapter action list to be able to
    // connect our action to mxEditor double click handler, as can be seem below.
    this._graphEditor.addAction('doubleClick', doubleClickHandler);

    // From http://jgraph.github.io/mxgraph/docs/js-api/files/editor/mxEditor-js.html#mxEditor.dblClickAction:
    // Specifies the name of the action to be executed when a cell is double clicked
    this._graphEditor.dblClickAction = 'doubleClick';
};

/**
 * Set the handler used for popup menu (i.e. menu triggered by right click) in cells of graph.
 *
 * Unlike other event handlers, popup menu is exclusive to a single handler. This follows
 * underlying mxGraph implementation that works in this manner, with the likely intention of
 * enforcing a single side-effect happening when a cell is right-clicked.
 *
 * @param {function} handler Callback that handles event. Receives, respectively, id of cell that
 * was right-clicked, X coordinate in screen coordinates and Y coordinate in screen coordinates as
 * its three arguments.
 */
graphs.Api.prototype.setPopupMenuHandler = function setPopupMenuHandler (handler) {
    "use strict";

    var popupMenuHandler = function(editor, cell, x, y) {
        var cellId = cell? cell.getId() : null;
        handler(cellId, x, y);
    };

    this._graphEditor.addAction('popupMenu', popupMenuHandler);

    // Installs a popupmenu handler using local function (see below).
    var graph = this._graphEditor.graph;
    mxEvent.disableContextMenu(graph.container);
    graph.popupMenuHandler.factoryMethod = function(menu, cell, evt)
    {
        handler(cell? cell.getId() : null, evt.clientX, evt.clientY);
    };
};

/**
 * Obtain a representation of the current state of the graph as an XML string.
 * The state can be restored calling `restore`.
 *
 * @returns {string} A xml string.
 */
graphs.Api.prototype.dump = function dump() {
    "use strict";
    return this._graphEditor.writeGraphModel()
};

/**
 * Restore the graph's state to one saved with `dump`.
 *
 * @param {string} state A xml string previously obtained with `bump`.
 */
graphs.Api.prototype.restore = function restore(state) {
    "use strict";
    var doc = mxUtils.parseXml(state);
    var node = doc.documentElement;
    this._graphEditor.readGraphModel(node);
};

/**
 * Gets the ids of endpoint vertices of an edge.
 *
 * @param {number} edgeId Id of an edge in graph.
 * @returns {number[]} An array with two values, first the source vertex id and second the target
 * vertex id.
 * @throws {Error} Unable to find edge.
 * @throws {Error} Given cell isn't an edge.
 */
graphs.Api.prototype.getEdgeTerminals = function getEdgeTerminals (edgeId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var edge = graph.getModel().getCell(edgeId);
    if (!edge) {
        throw Error("Unable to find edge with id " + edgeId);
    }

    if (!edge.isEdge()) {
        throw Error("Cell with id " + edgeId + " is not an edge");
    }

    var sourceId = edge.getTerminal(true).getId();
    var targetId = edge.getTerminal(false).getId();

    return [sourceId, targetId];
};

/**
 * This is the core implementation of {@link graphs.Api#getEdgeTerminalsWithPorts} (see for a deeper
 * description of return value).
 *
 * @param {mxCell} edge The edge object (the type of cell is not checked).
 * @returns {[number, string, number, string]}
 * @private
 */
graphs.Api.prototype._getMxEdgeTerminalsWithPorts = function _getMxEdgeTerminalsWithPorts (edge) {
    "use strict";

    var sourceId = edge.getTerminal(true).getId();
    var targetId = edge.getTerminal(false).getId();

    var style = edge.getStyle() || '';

    if (!this._qmxgraphSourcePortNameExtractionRegex){
        this._qmxgraphTargetPortNameExtractionRegex = new RegExp(
            '(?:^|;)targetPort=' + mxCell._PORT_ID_PREFIX + '\\d+-([^;$]+)(?:;|$)');
        this._qmxgraphSourcePortNameExtractionRegex = new RegExp(
            '(?:^|;)sourcePort=' + mxCell._PORT_ID_PREFIX + '\\d+-([^;$]+)(?:;|$)');
    }

    var sourcePortName = this._qmxgraphSourcePortNameExtractionRegex.exec(style);
    if (sourcePortName !== null) {
        sourcePortName = sourcePortName[1];
    }
    var targetPortName = this._qmxgraphTargetPortNameExtractionRegex.exec(style);
    if (targetPortName !== null) {
        targetPortName = targetPortName[1];
    }

    return [sourceId, sourcePortName, targetId, targetPortName];
};

/**
 * Gets the ids of endpoint vertices of an edge and the ports used.
 *
 * @param {number} edgeId Id of an edge in graph.
 * @returns {[number, string, number, string]} An array with four values: source vertex id, port id
 * on source, target vertex id, and port id on target. The port ids can be null if not used for the
 * connection.
 * @throws {Error} Unable to find edge.
 * @throws {Error} Given cell isn't an edge.
 */
graphs.Api.prototype.getEdgeTerminalsWithPorts = function getEdgeTerminals (edgeId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var edge = graph.getModel().getCell(edgeId);
    if (!edge) {
        throw Error("Unable to find edge with id " + edgeId);
    }

    if (!edge.isEdge()) {
        throw Error("Cell with id " + edgeId + " is not an edge");
    }

    return this._getMxEdgeTerminalsWithPorts(edge);
};

/**
 * Helper method to customize value of nodes. Values are formated according to suggestion in
 * https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxCell-js.html, to be able to associate
 * custom attributes (known as "tags" in QmxGraph context) to a cell.
 *
 * Values are a node in XML document, where 'label' is a protected tag which is always used to
 * store the label of a cell.
 *
 * @param {string} label Label of a cell.
 * @param {Object} tags A dict-like object containing tags that should be set in a cell.
 * @returns {Element} XML node that should be used as value by a cell.
 * @private
 */
graphs.Api.prototype._prepareCellValue = function _prepareCellValue(label, tags) {
    "use strict";

    var doc = mxUtils.createXmlDocument();
    var value = doc.createElement('data');
    value.setAttribute('label', label);

    tags = tags || {};
    var hop = Object.prototype.hasOwnProperty;
    for (var tagName in tags) {
        if (!hop.call(tags, tagName)) {
            continue;
        }

        var tagValue = tags[tagName];
        this._checkTagValue(tagName, tagValue);

        var internalTagName = this._getInternalTag(tagName);
        value.setAttribute(internalTagName, tagValue);
    }

    return value;
};

/**
 * @param {string} tag A tag.
 * @returns {string} Internal name used for tag.
 * @private
 */
graphs.Api.prototype._getInternalTag = function _getInternalTag(tag) {
    "use strict";

    return 'data-qgraph-tag-' + tag;
};

/**
 * @param {string} tag A tag.
 * @param {string} value Value of tag.
 * @throws {Error} If value is not a string.
 * @private
 */
graphs.Api.prototype._checkTagValue = function _checkTagValue(tag, value) {
    "use strict";

    if (Object.prototype.toString.call(value) !== "[object String]") {
        throw Error("Tag '" + tag + "' is not a string");
    }
};

/**
 * @param {mxGraphModel} model The graph's model.
 * @param {number} cellId Id of a cell in graph.
 * @returns {mxCell} The mxGraph's cell object.
 * @private
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype._findCell = function _findCell(model, cellId) {
    "use strict";

    var cell = model.getCell(cellId);
    if (!cell) {
        throw Error("Unable to find cell with id " + cellId);
    }
    return cell
};

/**
 * @param {mxGraphModel} model The graph's model.
 * @param {number} cellId Id of a cell in graph.
 * @param {string} portName The name of the port.
 * @param {boolean] alreadyExits Indicates if the port is expected to already exist in the cell.
 * @returns {mxCell} The mxGraph's port object.
 * @private
 * @throws {Error} If the port exist when it is not expected or is missing when expected.
 */
graphs.Api.prototype._findPort = function _findPort (model, cellId, portName, alreadyExits) {
    "use strict";

    var portId = this._getPortId(cellId, portName);
    var port = model.getCell(portId);
    var portFound = !!port;

    if (portFound && !alreadyExits) {
        throw Error("The cell " + cellId + " already have a port named " + portName);
    } else if (!portFound && alreadyExits) {
        throw Error("The cell " + cellId + " does not have a port named " + portName);
    }
    return port
};
