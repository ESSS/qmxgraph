/**
 * The actual javascript implementation
 */
/*global mxCell */
/*global mxConstants */
/*global mxEvent */
/*global mxGraph */
/*global mxPoint */
/*global mxTerminalChange*/
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
 * Constant indicating a cell will be used as source terminal.
 * @type {string}
 */
graphs.Api.SOURCE_TERMINAL_CELL = 'source';


/**
 * Constant indicating a cell will be used as target terminal.
 * @type {string}
 */
graphs.Api.TARGET_TERMINAL_CELL = 'target';


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
 * @param {number} [id] The id of the vertex. If omitted (or non unique) an id is generated.
 * @returns {number} Id of new vertex.
 */
graphs.Api.prototype.insertVertex = function insertVertex (
    x, y, width, height, label, style, tags, id) {
    "use strict";

    var graph = this._graphEditor.graph;
    var coords = graphs.utils.adjustCoordinates(graph, x, y);

    if (id === undefined) {
        id = null;
    }

    var value = this._prepareCellValue(label, tags);
    var parent = graph.getDefaultParent();
    var vertex = graph.insertVertex(
        parent,
        id,
        value,
        coords.x,
        coords.y,
        width,
        height,
        style
    );

    return vertex.getId();
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
    var portId = mxCell.createPortId(vertexId, portName);

    var value = this._prepareCellValue(label, tags);
    model.beginUpdate();
    var port;
    try {
        port = graph.insertVertex(
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
};

graphs.Api.prototype.getPortNames = function getPortNames (vertexId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var parent = this._findCell(model, vertexId);
    var candidates = model.getChildCells(parent, true, false);

    var portNames = [];
    var basePortId = mxCell.createPortId(vertexId, '');
    var basePortIdLength = basePortId.length;
    for (var i = 0; i < candidates.length; ++i) {
        var cell = candidates[i];
        if (cell.isPort()) {
            var name = cell.getId().substring(basePortIdLength);
            portNames.push(name)
        }
    }

    return portNames;
};

graphs.Api.prototype.updatePort = function updatePort (
    vertexId, portName, x, y, width, height, label, style, tags) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var portId = mxCell.createPortId(vertexId, portName);
    var portCell = this._findPort(model, vertexId, portName, true);

    model.beginUpdate();
    try {
        // x,y, width, height.
        var geometry = portCell.getGeometry();
        if (x !== null) {
            geometry.x = x;
        }
        if (y !== null) {
            geometry.y = y;
        }
        if (width !== null) {
            geometry.width = width;
        }
        if (height !== null) {
            geometry.height = height;
        }
        model.setGeometry(portCell, geometry);
        portCell.geometry.offset = new mxPoint(-geometry.width / 2, -geometry.height / 2);
        // label, style.
        if (label !== null) {
            this.setLabel(portId, label);
        }
        if (style !== null) {
            this.setStyle(portId, style)
        }
        // tags.
        if (tags !== null) {
            var existingTags = portCell.getAttributeNames();
            for (var i = 0; i < existingTags.length; ++i) {
                var tagName = existingTags[i];
                if (tags.indexOf(tagName) === -1) {
                    portCell.removeAttribute(tagName)
                }
            }
            var hop = Object.prototype.hasOwnProperty;
            for (var tagName in tags) {
                if (hop.call(tags, tagName)) {
                    this._setMxCellTag(portCell, tagName, tags[tagName]);
                }
            }
        }
    } finally {
        model.endUpdate();
    }
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
 * @param {number} [id] The id of the edge. If omitted (or non unique) an id is generated.
 * @returns {number} Id of new edge.
 * @throws {Error} If source or target aren't found in graph.
 * @throws {Error} If the source or target ports aren't found in the respective vertices.
 */
graphs.Api.prototype.insertEdge = function insertEdge (
    sourceId, targetId, label, style, tags, sourcePortName, targetPortName, id) {
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
        target = this._findPort(model, targetId, targetPortName, true);
    }

    if (id === undefined) {
        id = null;
    }

    var edge = graph.insertEdge(parent, id, value, source, target, style);

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
 * @param {number} [id] The id of the decoration. If omitted (or non unique) an id is generated.
 * @returns {number} Id of new decoration.
 */
graphs.Api.prototype.insertDecoration = function insertDecoration (
    x, y, width, height, label, style, tags, id) {
    "use strict";

    var graph = this._graphEditor.graph;
    var parent = graph.getDefaultParent();
    var edge = graph.getCellAt(x, y, parent, false, true);

    if (edge === null) {
        throw Error("Could not find an edge at position and can only add a " +
            "decoration over an edge.");
    }

    var edgeTerminalPoints = this._getMxEdgeTerminalPoints(edge);
    var sourcePoint = edgeTerminalPoints[0];
    var targetPoint = edgeTerminalPoints[1];

    var distance = function(a, b) {
        return Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2));
    };

    var total = distance(targetPoint, sourcePoint);
    var current = distance(sourcePoint, {x: x, y: y});

    // Relative position in edge
    var position = current / total;

    return this._insertDecorationOnEdge(edge, position, width, height, label, style, tags, id);
};

/**
 * Maps the decoration position in the edge to mxGraph's normalized position.
 *
 * @param {number} position Position of the decoration.
 * @returns {number} Position of the decoration in mxGraph coordinates (normalized between [-1, 1]).
 */
graphs.Api.prototype._mapDecorationPositionToMxGraph = function _mapDecorationPositionToMxGraph(position) {
  if (position < 0) {
    position = 0;
  } else if (position > 1) {
    position = 1;
  }
  return (position * 2) - 1;  // mxGraph normalizes between [-1, 1].
}

/**
 * Inserts a decoration over an edge in graph. A decoration is basically an
 * object used as overlay in edges, to show objects present along its path.
 *
 * @param {number} edgeId Id of an edge in graph.
 * @param {number} position The normalized position in the edge.
 * @param {number} width Width of decoration.
 * @param {number} height Height of decoration.
 * @param {string} label Label of decoration.
 * @param {string} [style] Name of a style or an inline style.
 * @param {Object} [tags] A dict-like object, with string keys and values. Tags are basically custom
 * attributes that may be added to a cell that may be later queried (or even modified), with the
 * objective of allowing better inspection and interaction with cells in a graph.
 * @param {number} [id] The id of the decoration. If omitted (or non unique) an id is generated.
 * @returns {number} Id of new decoration.
 * @throws {Error} If edge isn't found in graph.
 */
graphs.Api.prototype.insertDecorationOnEdge = function insertDecorationOnEdge (
    edgeId, position, width, height, label, style, tags, id) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var edge = this._findCell(model, edgeId);

    return this._insertDecorationOnEdge(edge, position, width, height, label, style, tags, id);
};

/**
 * Inserts a decoration over an edge in graph. A decoration is basically an
 * object used as overlay in edges, to show objects present along its path.
 *
 * @param {mxCell} edge An edge in graph.
 * @param {number} position The normalized position in the edge.
 * @param {number} width Width of decoration.
 * @param {number} height Height of decoration.
 * @param {string} label Label of decoration.
 * @param {string} [style] Name of a style or an inline style.
 * @param {Object} [tags] A dict-like object, with string keys and values. Tags are basically custom
 * attributes that may be added to a cell that may be later queried (or even modified), with the
 * objective of allowing better inspection and interaction with cells in a graph.
 * @param {number} [id] The id of the decoration. If omitted (or non unique) an id is generated.
 * @returns {number} Id of new decoration.
 */
graphs.Api.prototype._insertDecorationOnEdge = function _insertDecorationOnEdge (
    edge, position, width, height, label, style, tags, id) {
    "use strict";

    var graph = this._graphEditor.graph;
    position = this._mapDecorationPositionToMxGraph(position);

    style = graphs.utils.setStyleKey(style, 'labelPosition', 'left');
    style = graphs.utils.setStyleKey(style, 'align', 'right');

    var decorationStyle = graphs.utils.obtainDecorationStyle(graph, edge, style);

    var value = this._prepareCellValue(label, tags);
    value.setAttribute('__decoration__', '1');

    if (id === undefined) {
        id = null;
    }

    var model = graph.getModel();
    model.beginUpdate();
    var decoration;
    try {
        decoration = graph.insertVertex(
            edge, id, value, position, 0, width, height, decorationStyle, true);
        decoration.geometry.offset = new mxPoint(-width / 2, -height / 2);
        decoration.connectable = false;
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
 * @param {graphs.utils.TableDescription} contents A description of the table contents.
 * @param {string} title Title of table.
 * @param {Object} [tags] A dict-like object, with string keys and values. Tags are basically custom
 * attributes that may be added to a cell that may be later queried (or even modified), with the
 * objective of allowing better inspection and interaction with cells in a graph.
 * @param {string} [style] An style name or inline style. The `'table'` style is always used but
 * options defined with this value will overwrite the option defined on the `'table'` style.
 * @param {number} [parentId] If supplied this makes the table position relative to this cell
 * @param {number} [id] The id of the table. If omitted (or non unique) an id is generated.
 * @returns {number} Id of new table.
 * @throws {Error} If parentId  is supplied but isn't found in graph.
 */
graphs.Api.prototype.insertTable = function insertTable (
    x, y, width, contents, title, tags, style, parentId, id) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var isRelative = parentId != null;  // jshint ignore:line
    var parent = null;
    var coords;
    if (isRelative) {
        parent = this._findCell(model, parentId);
        coords = {x: x, y: y};  // No adjustments in coordinates
    } else {
        parent = graph.getDefaultParent();
        coords = graphs.utils.adjustCoordinates(graph, x, y);
    }

    var tableStyle = 'table';
    if (style != null) {  // jshint ignore:line
        tableStyle += ';' + style;
    }
    tableStyle = graphs.utils.setStyleKey(tableStyle, mxConstants.STYLE_OVERFLOW, 'fill');
    tableStyle = graphs.utils.setStyleKey(tableStyle, mxConstants.STYLE_CLONEABLE, false);

    var label = graphs.utils.createTableElement(contents, title);
    var value = this._prepareCellValue(label, tags);
    value.setAttribute('__table__', '1');

    if (id === undefined) {
        id = null;
    }

    model.beginUpdate();
    var table = null;
    try {
        table = graph.insertVertex(
            parent,
            id,
            value,
            coords.x,
            coords.y,
            0,
            0,
            tableStyle,
            isRelative
        );
        table.connectable = false;

        // Updates the height of the cell (override width
        // for table width is set to 100%)
        graph.updateCellSize(table);
    } finally {
        model.endUpdate();
    }

    return table.getId();
};

/**
 * Updates the contents and title of a table.
 *
 * @param {number} tableId Id of a table.
 * @param {graphs.utils.TableDescription} contents A description of the table contents.
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
 * Return the id of the edge containing the given decoration.
 *
 * @param cellId
 * @returns {number} Id of the decoration's parent.
 * @throws {Error} If the given cell is not found or it is a decoration.
 */
graphs.Api.prototype.getDecorationParentCellId = function getDecorationParentCellId (cellId) {
    "use strict";

    var cell = this._findDecoration(cellId);
    return cell.getParent().getId();
};

/**
 * Return an object describing the bounds of the given cell.
 *
 * @param {mxCell} cell The cell.
 * @returns {object} The bounds object.
 */
graphs.Api.prototype._getBoundsFromMxCell = function _getBoundsFromMxCell (cell) {
    "use strict";

    var geometry = cell.getGeometry();
    var parent_anchor_position = null;
    var x = geometry.x, y = geometry.y;

    if (geometry.relative) {
        parent_anchor_position = {'x': x, 'y': y};
        x = geometry.offset ? geometry.offset.x : 0;
        y = geometry.offset ? geometry.offset.y : 0;
    }

    return {
        'x': x,
        'y': y,
        'width': geometry.width,
        'height': geometry.height,
        'parent_anchor_position': parent_anchor_position
    };
};

/**
 * Return an object describing the bounds of a cell.
 *
 * @param {number} cellId Id of a cell in graph.
 * @returns {object} The bounds object.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.getCellBounds = function getCellBounds (cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    return this._getBoundsFromMxCell(cell);
};

/**
 * Return an object describing the bounds of a cell.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {object} cell_bounds The bounds object.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.setCellBounds = function setCellBounds (cellId, cell_bounds) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cell = model.getCell(cellId);
    var geometry = cell.getGeometry().clone();

    geometry.width = cell_bounds.width;
    geometry.height = cell_bounds.height;
    if (cell_bounds.parent_anchor_position) {
        geometry.relative = true;
        geometry.offset = geometry.offset || new mxPoint(0,0);
        geometry.offset.x = cell_bounds.x;
        geometry.offset.y = cell_bounds.y;
        geometry.x = cell_bounds.parent_anchor_position.x;
        geometry.y = cell_bounds.parent_anchor_position.y;
    } else {
        geometry.relative = false;
        geometry.offset = null;
        geometry.x = cell_bounds.x;
        geometry.y = cell_bounds.y;
    }
    model.setGeometry(cell, geometry);
    graph.refresh(cell)
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
 * Gets the decoration's relative position.
 *
 * @param {number} cellId Id of a decoration in graph.
 * @returns {number} Returns an a normalized number between [0, 1] representing the position of the
 * decoration along the parent edge.
 * @throws {Error} Unable to find the cell or it is not an decoration.
 */
graphs.Api.prototype.getDecorationPosition = function getDecorationPosition (cellId) {
    "use strict";

    var cell = this._findDecoration(cellId);
    var position = cell.getGeometry().x;  // Normalized between [-1, 1].
    return (position + 1) / 2;
};

/**
 * Sets the decoration's relative position.
 *
 * @param {number} cellId Id of a decoration in graph.
 * @param {number} position A normalized number between [0, 1] representing the position of the decoration
 * along the parent edge.
 * @throws {Error} Unable to find the cell or it is not an decoration.
 */
graphs.Api.prototype.setDecorationPosition = function setDecorationPosition (cellId, position) {
    "use strict";

    var cell = this._findDecoration(cellId);
    position = this._mapDecorationPositionToMxGraph(position);

    var newGeom = cell.getGeometry().clone();
    newGeom.x = position;

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    model.setGeometry(cell, newGeom);
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
 * Show/hide a cell's port.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {string} portName Name of a port in the cell.
 * @param {boolean} visible Visibility state.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype.setPortVisible = function setPortVisible (cellId, portName, visible) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    this._findCell(model, cellId);  // Cell missing detection.
    var port = this._findPort(model, cellId, portName, true);
    model.setVisible(port, visible);
    graph.refresh(port);
};

/**
 * Indicates a cell's visibility.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {string} portName Name of a port in the cell.
 * @throws {Error} Unable to find cell.
 * @throws {Error} If a port with the given name is not present in the vertex.
 */
graphs.Api.prototype.isPortVisible = function isPortVisible (cellId, portName) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    this._findCell(model, cellId);  // Cell missing detection.
    var port = this._findPort(model, cellId, portName, true);
    return model.isVisible(port);
};

/**
 * Sets a cell connectable property.
 *
 * @param {number} cellId Id of a cell in graph.
 * @param {boolean} enabled Enable value of this property.
 */
graphs.Api.prototype.setConnectable = function setConnectable(cellId, enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cell = this._findCell(model, cellId);
    if (cell) {
        cell.setConnectable(enabled);
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }
};

/**
 * Returns current cell's connectable property. If the graph has connection forbidden this will return `false`.
 *
 * @returns {boolean} Enable value of this property.
 */
graphs.Api.prototype.isConnectable = function isConnectable(cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cell = this._findCell(model, cellId);
    return model.isConnectable(cell);
};


/**
 * Select the cells with the given ids.
 *
 * @param {number[]} cellIds An array with the ids of the cells to select.
 */
graphs.Api.prototype.setSelectedCells = function setSelectedCells (cellIds) {
    "use strict";

    var cellsToSelect = [];
    var model = this._graphEditor.graph.getModel();
    var cell = null;
    for (var i = cellIds.length; i--;) {
        cell = model.getCell(cellIds[i]);
        cellsToSelect.push(cell);
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
        cellIds.push(cells[i].getId());
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
 * Zoom in the graph.
 */
graphs.Api.prototype.zoomIn = function zoomIn () {
    "use strict";

    this._graphEditor.graph.zoomIn();
};

/**
 * Zoom out the graph.
 */
graphs.Api.prototype.zoomOut = function zoomOut () {
    "use strict";

    this._graphEditor.graph.zoomOut();
};

/**
 * Return the current scale (zoom).
 *
 * @returns {number}
 */
graphs.Api.prototype.getZoomScale = function getZoomScale () {
    "use strict";

    return this._graphEditor.graph.view.getScale();
};

/**
 * Reset graph's zoom.
 */
graphs.Api.prototype.resetZoom = function resetZoom () {
    "use strict";

    this._graphEditor.graph.zoomActual();
};

/**
 * Get the current scale and translation.
 *
 * @returns {number[]} The graph scale, the translation along the x axis, and the translation
 * along the y axis. The three values returned by this function is suitable to be supplied to
 * {@link graphs.Api#setScaleAndTranslation} to set the scale and translation to a previous value.
 */
graphs.Api.prototype.getScaleAndTranslation = function getScaleAndTranslation () {
    "use strict";

    var graph = this._graphEditor.graph;
    var scale = graph.view.getScale();
    var translate = graph.view.getTranslate();
    return [scale, translate.x, translate.y];
};

/**
 * Set the scale and translation.
 *
 * @param {number} scale The new graph's scale (1 = 100%).
 * @param {number} x The new graph's translation along the X axis (0 = origin).
 * @param {number} y The new graph's scale along the Y axis (0 = origin}.
 */
graphs.Api.prototype.setScaleAndTranslation = function setScaleAndTranslation (scale, x, y) {
    "use strict";

    var view = this._graphEditor.graph.getView();
    view.scaleAndTranslate(scale, x, y);
};

/**
 * Rescale the graph to fit in the container.
 */
graphs.Api.prototype.fit = function fit () {
    "use strict";

    this._graphEditor.graph.fit(10);
};

/**
 * Remove cells from graph.
 *
 * @param {number[]} cellIds Ids of cells that must be removed.
 * @param {boolean} ignoreMissingCells Ids of non existent cells are ignored instead raising
 * an error.
 */
graphs.Api.prototype.removeCells = function removeCells (cellIds, ignoreMissingCells) {
    "use strict";

    ignoreMissingCells = !!ignoreMissingCells;
    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cells = [];
    for (var i = 0; i < cellIds.length; ++i) {
        var cell = this._findCell(model, cellIds[i], ignoreMissingCells);
        if (cell) {
            cells.push(cell);
        }
    }
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
        var source_terminal = terminals[0];
        var target_terminal = terminals[1];
        if (
            (source_terminal[0] == vertexId && source_terminal[1] == portName)  // jshint ignore:line
            || (target_terminal[0] == vertexId && target_terminal[1] == portName)  // jshint ignore:line
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
graphs.Api.prototype.registerCellsRemovedHandler = function registerCellsRemovedHandler (handler) {
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
graphs.Api.prototype.registerCellsAddedHandler = function registerCellsAddedHandler (handler) {
    "use strict";

    var graph = this._graphEditor.graph;

    var addHandler = function(sender, evt) {
        var cells = evt.getProperty('cells');
        var cellIds = [];
        for (var i = 0; i < cells.length; i++) {
            var cell = cells[i];
            if (cell.isPort()) {
                // See comment about ports on `graphs.Api#registerCellsRemovedHandler`.
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
 * Add function to handle update events in the graph view.
 *
 * @param {function} handler Callback that handles event. Receives two arguments:
 *   1. graph dump;
 *   2. graph scale and translation;
 */
graphs.Api.prototype.registerViewUpdateHandler = function registerViewUpdateHandler (handler) {
    "use strict";
    var graph = this._graphEditor.graph;
    var listener = (function(sender, evt) {
        handler(this.dump(), this.getScaleAndTranslation());
    }).bind(this);
    graph.getView().addListener(mxEvent.SCALE, listener);
    graph.getView().addListener(mxEvent.TRANSLATE, listener);
    graph.getView().addListener(mxEvent.SCALE_AND_TRANSLATE, listener);

    // Listen to events that generate UNDO events.
    graph.getModel().addListener(mxEvent.UNDO, listener);
    graph.getView().addListener(mxEvent.UNDO, listener);
};

/**
 * Add function to handle update events in cells geometry.
 *
 * @param {function} handler Callback that handles event. Receives as argument a map of cell id
 * to a object describing the cell bounds.
 */
graphs.Api.prototype.registerBoundsChangedHandler = function registerBoundsChangedHandler (handler) {
    "use strict";

    var cellBoundsChangeHandler = (function cellBoundsChangeHandler (source, event) {
        var cells = event.getProperty('cells');
        var cell_bounds_map = {};

        for (var index = 0; index < cells.length; ++index) {
            var cell = cells[index];
            var cell_id = cell.getId();
            var geometry = this._getBoundsFromMxCell(cell);
            cell_bounds_map[cell_id] = geometry;
        }
        handler(cell_bounds_map);
    }).bind(this);

    var graph = this._graphEditor.graph;
    graph.addListener(mxEvent.CELLS_MOVED, cellBoundsChangeHandler);
    graph.addListener(mxEvent.CELLS_RESIZED, cellBoundsChangeHandler);
    graph = null;
};

/**
 * Add function to handle selection change events in the graph.
 *
 * @param {function} handler Callback that handles event. Receives an array with the id of cells
 * that are selected as only argument.
 */
graphs.Api.prototype.registerSelectionChangedHandler = function registerSelectionChangedHandler (handler) {
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
 * Add function to handle terminal change events in the graph.
 *
 * @param {function} handler Callback that handles event. Receives, respectively, cell id,
 * boolean indicating if the changed terminal is the source (or target), id of the new terminal,
 * id of the old terminal.
 */
graphs.Api.prototype.registerTerminalChangedHandler = function registerTerminalChangedHandler (handler) {
    "use strict";

    var cellConnectedHandler = function(source, event) {
        var changeList = event.getProperty('edit').changes;
        for (var i = 0; i < changeList.length; i++) {
            var change = changeList[i];

            var notifyTerminalChange = (
                change instanceof mxTerminalChange &&
                change.previous !== null &&
                change.terminal !== null
            );
            if (notifyTerminalChange) {
                handler(
                    change.cell.getId(),
                    (change.source ? 'source' : 'target'),
                    change.terminal.getId(),
                    change.previous.getId()
                );
            }
        }
    };

    var graph = this._graphEditor.graph;
    graph.model.addListener(mxEvent.CHANGE, cellConnectedHandler);
    graph = null;
};

/**
 * Add function to handle terminal change events with the connection port information in the graph.
 *
 * @param {function} handler Callback that handles event. Receives, respectively, cell id,
 * boolean indicating if the changed terminal is the source (or target), id of the new terminal,
 * port id used in the new terminal, id of the old terminal, port id used in the old terminal.
 */
graphs.Api.prototype.registerTerminalWithPortChangedHandler = function registerTerminalWithPortChangedHandler (handler) {
    "use strict";

    function getPortNameFromStyle(stylesheet, style, source) {
        var styleObj = stylesheet.getCellStyle(style, null) || {};
        var portData = mxCell.parsePortId(styleObj[source + 'Port']);
        return portData[1];
    }

    var cellConnectedHandler = function(source, event) {
        var changeList = event.getProperty('edit').changes;
        var eventMap = {};

        for (var i = 0; i < changeList.length; i++) {
            var change = changeList[i];
            if (!change.cell) {
                continue;
            }
            var eventTargetId = change.cell.getId();

            var styleChange = (
                change instanceof mxStyleChange &&
                change.previous !== undefined &&
                change.style !== undefined
            );
            if (styleChange) {
                var eventData = eventMap[eventTargetId] = eventMap[eventTargetId] || {};
                eventData.previousStyle = change.previous;
                eventData.newStyle = change.style;
                continue;
            }

            var notifyTerminalChange = (
                change instanceof mxTerminalChange &&
                change.previous !== null &&
                change.terminal !== null
            );
            if (notifyTerminalChange) {
                var eventData = eventMap[eventTargetId] = eventMap[eventTargetId] || {};
                eventData.source = change.source ? 'source' : 'target';
                eventData.newTerminalId = change.terminal.getId();
                eventData.previousTerminalId = change.previous.getId();
                continue;
            }
        }

        var stylesheet = new mxStylesheet();
        for (var eventTargetId in eventMap) {
            if (Object.prototype.hasOwnProperty.call(eventMap, eventTargetId)) {
                var eventData = eventMap[eventTargetId];
                if (eventData.source !== undefined) {
                    var newPortName = getPortNameFromStyle(
                        stylesheet, eventData.newStyle, eventData.source);
                    var previousPortName = getPortNameFromStyle(
                        stylesheet, eventData.previousStyle, eventData.source);
                    handler(
                        eventTargetId,
                        eventData.source,
                        eventData.newTerminalId,
                        newPortName,
                        eventData.previousTerminalId,
                        previousPortName
                    );
                }
            }
        }
    };

    var graph = this._graphEditor.graph;
    graph.model.addListener(mxEvent.CHANGE, cellConnectedHandler);
    graph = null;
};


/**
 * Register a handler to event when cells have their label changed.
 *
 * @param {function} handler Callback that handles event. Receives, respectively, id of cell
 * that was renamed, its new label and its old label.
 */
graphs.Api.prototype.registerLabelChangedHandler = function registerLabelChangedHandler (handler) {
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
    graph.refresh(cell); // Force a refresh of that cell to guarantee
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

    var graph = this._graphEditor.graph;
    var cell = graph.getModel().getCell(cellId);
    if (cell) {
        this._setMxCellTag(cell, tagName, tagValue);
    } else {
        throw Error("Unable to find cell with id " + cellId);
    }
};

/**
 * Sets a tag in cell.
 *
 * Note that tag values are always coerced to string.
 *
 * @param {mxCell} cell A cell in graph.
 * @param {string} tagName Name of tag.
 * @param {string} tagValue Value of tag.
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype._setMxCellTag = function _setMxCellTag (cell, tagName, tagValue) {
    "use strict";

    this._checkTagValue(tagName, tagValue);
    if (!mxUtils.isNode(cell.value)) {
        var value = this._prepareCellValue(cell.value, null);
        cell.setValue(value);
    }
    var internalTagName = this._getInternalTag(tagName);
    cell.setAttribute(internalTagName, tagValue);
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

graphs.Api.prototype.delTag = function delTag (cellId, tagName) {
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
graphs.Api.prototype.registerDoubleClickHandler = function registerDoubleClickHandler (handler) {
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
graphs.Api.prototype.registerPopupMenuHandler = function registerPopupMenuHandler (handler) {
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
    return this._graphEditor.writeGraphModel();
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
 * Set an edge's  terminal.
 *
 * @param {number} cellId The id of a edge in graph.
 * @param {string} terminalType Indicates if the affected terminal is the source or target (one of
 * `graphs.Api.*_TERMINAL_CELL`).
 * @param {number} newTerminalCellId The if of the new terminal for the edge.
 * @param {string} portName The name of the port to use in the connection, if it is a "falsy"
 * value do not use a port.
 * @throws {Error} Unable to find cell.
 * @throws {Error} Unable to find cell's port.
 * @throws {Error} Not a valid terminal type.
 */
graphs.Api.prototype.setEdgeTerminal = function setEdgeTerminal (
    cellId, terminalType, newTerminalCellId, portName) {
    "use strict";
    var isSource = true;

    if (terminalType === graphs.Api.SOURCE_TERMINAL_CELL) {
        isSource = true;
    } else if (terminalType === graphs.Api.TARGET_TERMINAL_CELL) {
        isSource = false;
    } else {
        throw Error(String(terminalType) + ' is not a valid value for `terminalType`');
    }

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var edge = this._findCell(model, cellId);
    var terminal = this._findCell(model, newTerminalCellId);
    if (portName) {
        // Port missing detection.
        this._findPort(model, newTerminalCellId, portName, true);
    }
    model.beginUpdate();
    try {
        model.setTerminal(edge, terminal, isSource);
        var terminal_value = '';
        if (portName) {
             terminal_value = mxCell.createPortId(newTerminalCellId, portName);
        }
        var edge_style = model.getStyle(edge);
        var terminal_key = terminalType + 'Port';
        if (portName) {
            edge_style = graphs.utils.setStyleKey(edge_style, terminal_key, terminal_value);
        }
        else {
            // Remove the previously connected port.
            edge_style = graphs.utils.removeStyleKey(edge_style, terminal_key);
        }
        model.setStyle(edge, edge_style);
    } finally {
        model.endUpdate();
    }
};

/**
 * This is the core implementation of {@link graphs.Api#getEdgeTerminalsWithPorts} (see for a deeper
 * description of return value).
 *
 * @param {mxCell} edge The edge object (the type of cell is not checked).
 * @returns {[[number, string], [number, string]]}
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
    } else {
        sourcePortName = null;
    }
    var targetPortName = this._qmxgraphTargetPortNameExtractionRegex.exec(style);
    if (targetPortName !== null) {
        targetPortName = targetPortName[1];
    } else {
        targetPortName = null;
    }

    return [[sourceId, sourcePortName], [targetId, targetPortName]];
};

/**
 * Gets the ids of endpoint vertices of an edge and the ports used.
 *
 * @param {number} edgeId Id of an edge in graph.
 * @returns {[[number, string], [number, string]]} An array with four values: source vertex id, port id
 * on source, target vertex id, and port id on target. The port ids can be null if not used for the
 * connection.
 * @throws {Error} Unable to find edge.
 * @throws {Error} Given cell isn't an edge.
 */
graphs.Api.prototype.getEdgeTerminalsWithPorts = function getEdgeTerminalsWithPorts (edgeId) {
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
 * Gets the terminal points for an edge.
 *
 * @param {mxCell} edge An edge.
 * @returns {[mxPoint, mxPoint]} An array with two point (the source and target points).
 * @throws {Error} Given cell isn't an edge.
 */
graphs.Api.prototype._getMxEdgeTerminalPoints = function _getMxEdgeTerminalPoints (edge) {
    "use strict";

    // Need terminal positions to be able to determine correct relative position
    // of decoration in relation to its parent edge.
    var graph = this._graphEditor.graph;
    var view = graph.view;
    var edgeId = edge.getId();

    if (!edge.isEdge()) {
        throw Error("Cell with id " + edgeId + " is not an edge");
    }

    var sourcePort = view.getTerminalPort(
        view.getState(edge), view.getState(edge.getTerminal(true)), true);
    var targetPort = view.getTerminalPort(
        view.getState(edge), view.getState(edge.getTerminal(false)), false);

    var edgeGeo = this.getGeometry(edgeId);
    var x = edgeGeo[0] + Math.floor(edgeGeo[2] / 2);
    var y = edgeGeo[1] + Math.floor(edgeGeo[3] / 2);

    var sourcePoint = view.getPerimeterPoint(sourcePort, new mxPoint(x, y), false);
    var targetPoint = view.getPerimeterPoint(targetPort, new mxPoint(x, y), false);
    return [sourcePoint, targetPoint];
};

/**
 * Gets the terminal points for an edge.
 *
 * @param {number} edgeId Id of an edge in graph.
 * @returns {[[number, number], [number, number]]} An array with two values, the "x,y" coordinates
 * for the source and the "x,y" for the target.
 * @throws {Error} Unable to find edge.
 * @throws {Error} Given cell isn't an edge.
 */
graphs.Api.prototype.getEdgeTerminalPoints = function getEdgeTerminalPoints (edgeId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var edge = this._findCell(model, edgeId);

    var terminal_points = this._getMxEdgeTerminalPoints(edge);
    return [
        [terminal_points[0].x, terminal_points[0].y],
        [terminal_points[1].x, terminal_points[1].y]
    ];
};

/**
 * Sets various interaction-related properties (like deleting cells, moving cells, connecting
 * cells, etc) to enable/disable.
 *
 * @param {boolean} enabled Enable value of this property.
 */
graphs.Api.prototype.setInteractionEnabled = function setInteractionEnabled(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    graph.setCellsDeletable(enabled);
    graph.setCellsDisconnectable(enabled);
    graph.setConnectable(enabled);
    graph.setCellsEditable(enabled);
    graph.setCellsMovable(enabled);
};

/**
 * Sets graph cellsDeletable property.
 *
 * @param {boolean} enabled Enable value of this property.
 */
graphs.Api.prototype.setCellsDeletable = function setCellsDeletable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    graph.setCellsDeletable(enabled);
};

/**
 * Returns current graph cellsDeletable property.
 *
 * @returns {boolean} Enable value of this property.
 */
graphs.Api.prototype.isCellsDeletable = function isCellsDeletable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    return graph.isCellsDeletable(enabled);
};

/**
 * Sets graph cellsDisconnectable property.
 *
 * @param {boolean} enabled Enable value of this property.
 */
graphs.Api.prototype.setCellsDisconnectable = function setCellsDisconnectable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    graph.setCellsDisconnectable(enabled);
};

/**
 * Returns current graph cellsDisconnectable property.
 *
 * @returns {boolean} Enable value of this property.
 */
graphs.Api.prototype.isCellsDisconnectable = function isCellsDisconnectable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    return graph.isCellsDisconnectable(enabled);
};

/**
 * Sets graph cellsEditable property.
 *
 * @param {boolean} enabled Enable value of this property.
 */
graphs.Api.prototype.setCellsEditable = function setCellsEditable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    graph.setCellsEditable(enabled);
};

/**
 * Returns current graph cellsEditable property.
 *
 * @returns {boolean} Enable value of this property.
 */
graphs.Api.prototype.isCellsEditable = function isCellsEditable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    return graph.isCellsEditable(enabled);
};

/**
 * Sets graph cellsMovable property.
 *
 * @param {boolean} enabled Enable value of this property.
 */
graphs.Api.prototype.setCellsMovable = function setCellsMovable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    graph.setCellsMovable(enabled);
};

/**
 * Returns current graph cellsMovable property.
 *
 * @returns {boolean} Enable value of this property.
 */
graphs.Api.prototype.isCellsMovable = function isCellsMovable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    return graph.isCellsMovable(enabled);
};

/**
 * Sets graph connectable property.
 *
 * @param {boolean} enabled Enable value of this property.
 */
graphs.Api.prototype.setCellsConnectable = function setCellsConnectable(enabled) {
    "use strict";

    var graph = this._graphEditor.graph;
    graph.setConnectable(enabled);
};

/**
 * Returns current graph connectable property.
 *
 * @returns {boolean} Enable value of this property.
 */
graphs.Api.prototype.isCellsConnectable = function isCellsConnectable() {
    "use strict";

    var graph = this._graphEditor.graph;
    return graph.isConnectable();
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
 * @param {boolean} ignoreMissingCell Whe the cell id is not found return `null` instead raising
 * an error.
 * @returns {mxCell} The mxGraph's cell object.
 * @private
 * @throws {Error} Unable to find cell.
 */
graphs.Api.prototype._findCell = function _findCell(model, cellId, ignoreMissingCell) {
    "use strict";

    var cell = model.getCell(cellId);
    if ((!cell) && (!ignoreMissingCell)) {
        throw Error("Unable to find cell with id " + cellId);
    }
    return cell;
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

    var portId = mxCell.createPortId(cellId, portName);
    var port = model.getCell(portId);
    var portFound = !!port;

    if (portFound && !alreadyExits) {
        throw Error("The cell " + cellId + " already have a port named " + portName);
    } else if (!portFound && alreadyExits) {
        throw Error("The cell " + cellId + " does not have a port named " + portName);
    }
    return port;
};

/**
 * @param {number} cellId Id of a cell in graph.
 * @param {string} portName The name of the port.
 * @returns {boolean} True if the port exists.
 */
graphs.Api.prototype.hasPort = function hasPort (cellId, portName) {
    "use strict";

    var graph = this._graphEditor.graph;
    var portId = mxCell.createPortId(cellId, portName);
    var port = graph.getModel().getCell(portId);
    return !!port;
};

/**
 *
 * @param {number} cellId
 * @returns {mxCell} The mxGraph's cell object used to display the de3coration.
 * @private
 * @throws {Error} Unable to find cell or the cell is not a decoration.
 */
graphs.Api.prototype._findDecoration = function _findDecoration (cellId) {
    "use strict";

    var graph = this._graphEditor.graph;
    var model = graph.getModel();
    var cell = this._findCell(model, cellId);
    if (!cell.isDecoration()) {
        throw new Error("The cell " + cellId + " is not a decoration");
    }
    return cell;
};

/**
 * Automatically organize the graph using one of the available layouts. If the layout is not
 * implemented, an exception will be raised.
 *
 * @param {string} layoutName The layout name (e.g.: 'organic'). Check the code for the available
 * layouts.
 * @throws {Error} If the layout is unknown.
 */
graphs.Api.prototype.runLayout = function runLayout(layoutName) {
    "use strict";

    var graph = this._graphEditor.graph;
    var layout = null;
    if (layoutName == "organic") {
        layout = new mxFastOrganicLayout(graph);
    } else if (layoutName == "compact") {
        layout = new mxCompactTreeLayout(graph);
    } else if (layoutName == "circle") {
        layout = new mxCircleLayout(graph);
    } else if (layoutName == "compact_tree") {
        layout = new mxCompactTreeLayout(graph);
    } else if (layoutName == "edge_label") {
        layout = new mxEdgeLabelLayout(graph);
    } else if (layoutName == "parallel_edge") {
        layout = new mxParallelEdgeLayout(graph);
    } else if (layoutName == "partition") {
        layout = new mxPartitionLayout(graph, true, 10, 20);
    } else if (layoutName == "radial_tree") {
        layout = new mxRadialTreeLayout(graph);
    } else if (layoutName == "stack") {
        layout = new mxStackLayout(graph);
    } else {
        throw new Error("Unknown layout named " + layoutName);
    }

    layout.execute(graph.getDefaultParent());
};
