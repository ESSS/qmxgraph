/*global mxConstraintHandler */
/*global mxEditor */
/*global mxGraph */
/*global mxCell */
/*global mxCellTracker */
/*global mxImage */
/*global mxConstants */
/*global mxEvent */
/*global mxEventObject */
/*global mxUtils */

/*global graphs */

/*global namespace */

/*global console */

/**
 * Namespace containing essential parts to create a graph drawing widget.
 *
 * @namespace graphs
 */
namespace('graphs');

/**
 * Factory method to configure and create a new graph drawing widget using
 * mxGraph as its backend.
 *
 * @param {HTMLElement} container Div containing graph widget.
 * @param {Object} options Options configuring features of graph.
 * @param {Object} styles Additional styles available for graph.
 * @returns {mxEditor} A new graph drawing widget.
 */
graphs.createGraph = function createGraph (container, options, styles) {
    "use strict";

    // Initialization ----------------------------------------------------------

    var editor = new mxEditor();
    editor.setGraphContainer(container);
    var graph = editor.graph;

    // NOTE: grid size must usually equal the size of grid GIF
    // used as background of graph's div
    graph.gridEnabled = true;
    graph.gridSize = 10;
    graph.graphHandler.guidesEnabled = true;

    // Enables HTML markup in all labels
    graph.setHtmlLabels(true);

    // Customizations ----------------------------------------------------------

    mxCell.prototype.hasAttribute = function(name)
    {
        var userObject = this.getValue();

        return (userObject !== null &&
            userObject.nodeType === mxConstants.NODETYPE_ELEMENT) ?
            userObject.hasAttribute(name) : false;
    };

    mxCell.prototype.isDecoration = function() {
        return !!this.__decoration__;
    };

    mxCell._PORT_ID_PREFIX = 'qmxgraph-port-';

    mxCell.prototype.isPort = function() {
        var cellId = this.getId();
        return cellId.indexOf(mxCell._PORT_ID_PREFIX) === 0;

    };

    var superIsCellFoldable = graph.isCellFoldable;
    graph.isCellFoldable = function(cell, collapse)
    {
        return cell.isTable() || superIsCellFoldable.apply(this, arguments);
    };

    // Table-like vertices inspired by this example:
    // https://jgraph.github.io/mxgraph/javascript/examples/scrollbars.html
    mxCell.prototype.isTable = function() {
        return !!this.__table__;
    };

    // Overrides getLabel to be able to fold table cells reliably
    var supeGetLabel = graph.getLabel;
    graph.getLabel = function(cell)
    {
        if (cell.isTable())
        {
            if (this.isCellCollapsed(cell))
            {
                // When collapsed, just show just title part of table vertices
                var value = cell.getAttribute('label');
                return value.substring(0, value.indexOf("</table>") + "</table>".length);
            }
            else
            {
                return supeGetLabel.apply(this, arguments);
            }
        }
        else
        {
            return supeGetLabel.apply(this, arguments);
        }
    };

    // Overrides getTooltipForCell so tables don't have tooltips
    var superGetTooltipForCell = graph.getTooltipForCell;
    graph.getTooltipForCell = function(cell)
    {
        if (cell.isTable()) {
            return '';
        } else {
            return superGetTooltipForCell.apply(this, arguments);
        }
    };

    // Overrides inspired by suggestion how to hold custom attributes (
    // https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxCell-js.html)
    var superConvertValueToString = graph.convertValueToString;
    graph.convertValueToString = function(cell)
    {
        if (mxUtils.isNode(cell.value)) {
            return cell.getAttribute('label', '');
        } else {
            return superConvertValueToString.apply(this, arguments);
        }
    };

    var superCellLabelChanged = graph.cellLabelChanged;
    graph.cellLabelChanged = function(cell, newValue, autoSize)
    {
        if (mxUtils.isNode(cell.value)) {
            var newValue_ = cell.cloneValue();
            newValue_.setAttribute('label', newValue);
            superCellLabelChanged.call(this, cell, newValue_, autoSize);
        } else {
            superCellLabelChanged.apply(this, arguments);
        }
    };

    graph.isPort = function(cell) {
        return cell.isPort();
    };

    var superIsCellSelectable = mxGraph.prototype.isCellSelectable;
    mxGraph.prototype.isCellSelectable = function(cell) {
        return superIsCellSelectable.apply(this, arguments) && !cell.isPort();
    };

    mxGraph.prototype.labelChanged = function(cell, value, evt)
    {
        this.model.beginUpdate();
        try
        {
            var old = null;
            if (mxUtils.isNode(cell.value)) {
                old = cell.getAttribute('label', '');
            } else {
                old = cell.value;
            }
            this.cellLabelChanged(cell, value, this.isAutoSizeCell(cell));
            this.fireEvent(new mxEventObject(mxEvent.LABEL_CHANGED,
                'cell', cell, 'value', value, 'old', old, 'event', evt));
        }
        finally
        {
            this.model.endUpdate();
        }

        return cell;
    };

    /**
     * Simitar to the original {@link mxGraph#isCellLocked} but allow to move relative positioned
     * tables.
     *
     * @param {mxCell} cell The cell of interest.
     * @returns {boolean}
     */
    mxGraph.prototype.isCellLocked = function(cell)
    {
        if (this.isCellsLocked()) {
            return true;
        }
        if (cell.isTable()) {
            return false;
        }
        var geometry = this.model.getGeometry(cell);
        return (
            geometry != null &&  // jshint ignore:line
            this.model.isVertex(cell) &&
            geometry.relative
        );
    };

    /**
     * Does not automatically reparent cells when moving.
     */
    graph.graphHandler.setRemoveCellsFromParent(false);

    // Key bindings ------------------------------------------------------------
    var keyHandler = editor.keyHandler;
    keyHandler.bindAction(46, 'delete');

    // Styles ------------------------------------------------------------------
    if (!!styles) {
        var hop = Object.prototype.hasOwnProperty;
        for (var name in styles) {
            if (!hop.call(styles, name)) {
                continue;
            }
            if (name !== 'edge') {
                graph.getStylesheet().putCellStyle(name, styles[name]);
            }
        }

        /* jshint -W069 */
        if (!!styles['edge']) {
            graph.getStylesheet().putDefaultEdgeStyle(styles['edge']);
        }
        /* jshint +W069 */
    }

    // Additional Actions ------------------------------------------------------
    var toggleGrid = function(editor, cell) {
        var graph = editor.graph;
        var classes = editor.graph.container.classList;
        var hideBG = "hide-bg";
        if (!classes.contains(hideBG)) {
            classes.add(hideBG);

            // This variable, despite its name, controls snapping to grid and
            // not grid visibility. If grid is hidden, disable snapping too.
            graph.__formerGridEnabled = graph.gridEnabled;
            graph.gridEnabled = false;
        } else {
            classes.remove(hideBG);
            graph.gridEnabled = graph.__formerGridEnabled;
        }
    };
    editor.addAction('toggleGrid', toggleGrid);

    var toggleSnap = function(editor, cell) {
        var graph = editor.graph;
        graph.gridEnabled = !graph.gridEnabled;
        graph.__formerGridEnabled = graph.gridEnabled;
    };
    editor.addAction('toggleSnap', toggleSnap);

    // Options -----------------------------------------------------------------

    // Configure options in graph editor
    /* jshint -W069 */
    graph.setCellsMovable(options['cells_movable']);

    graph.setConnectable(options['cells_connectable']);

    graph.setCellsCloneable(options['cells_cloneable']);

    graph.setCellsResizable(options['cells_resizable']);

    graph.connectionHandler.setCreateTarget(options['allow_create_target']);

    graph.allowDanglingEdges = options['allow_dangling_edges'];

    graph.multigraph = options['multigraph'];

    graph.graphHandler.setCloneEnabled(options['enable_cloning']);

    if (options['show_highlight']) {
        new mxCellTracker(graph, '#00FF00');  // jshint ignore:line
    }

    if (options['show_outline']) {
        editor.showOutline();
    }

    if (!options['show_grid']) {
        // By default, grid is shown. Can't have snap without grid visible
        // though
        editor.execute("toggleGrid");
        editor.execute("toggleSnap");
    } else if (!options['snap_to_grid']) {
        editor.execute("toggleSnap");
    }

    if (!!options['connection_image']) {
        graph.connectionHandler.connectImage = new mxImage(
            options['connection_image'][0],
            options['connection_image'][1],
            options['connection_image'][2]
        );
    }

    if (!!options['port_image']) {
        // TODO: way to do it without messing prototype?
        mxConstraintHandler.prototype.pointImage = new mxImage(
            options['port_image'][0],
            options['port_image'][1],
            options['port_image'][2]
        );
    }

    if (!!options['font_family'] && options['font_family'].length > 0) {
        // There is a `setFontFamily` method it isn't seem safe/easy to use it as:
        // * every canvas used by mxGraph is temporary (see `mxShape.prototype.redrawShape`)
        // * there are parts that are hardcoded to use always constant below (see
        // `mxSvgCanvas2D.prototype.createStyle`)
        // For these reasons it just straight up updates default font family used throughout
        // graph.
        var family = "";
        var raw = options['font_family'];
        for (var i = 0; i < raw.length; i++) {
            family += raw[i];
            if (i < raw.length - 1) {
                family += ",";
            }
        }
        mxConstants.DEFAULT_FONTFAMILY = family;
    }

    /* jshint +W069 */

    // Hooks -------------------------------------------------------------------
    graph.createGroupCell = function(cells)
    {
        var group = mxGraph.prototype.createGroupCell.call(this, cells);
        group.setValue('group');
        group.setStyle('group');

        return group;
    };

    // Event Handling ----------------------------------------------------------

    // * When an edge is moved, the rotation of any child marker must update too
    var onCellsMove = function(sender, evt) {
        var cells = evt.getProperty('cells');
        var dx = evt.getProperty('dx');
        var dy = evt.getProperty('dy');

        sender.__moved = [];

        for (var c = cells.length; c--;) {
            var cell = cells[c];
            if (!cell.isEdge()) {
                var edges = sender.model.getEdges(cell);
                for (var e = 0; e < edges.length; e++) {
                    var edge = edges[e];
                    var markers = sender.getChildCells(edge, true, false);
                    if (markers.length > 0) {
                        sender.__moved.push([edge, markers]);
                    }
                }
            }
        }

        // Hack-ish: sadly, edges connected to moved vertices aren't updated at
        // this point and, to make matters worse, there isn't an event triggered
        // when edges are updated as consequence of this move action (at
        // least unable to find an event like that so far) ... Force a refresh
        // to make sure necessary parts are all updated (this may be too costly
        // in bigger graphs, may need to be reviewed).
        if (sender.__moved.length > 0) {
            sender.refresh();
        }
    };
    graph.addListener(mxEvent.MOVE_CELLS, onCellsMove);

    // * Handle delayed rotation of edge markers
    var onRefresh = function(sender, event) {
        // If any edges with markers were moved indirectly when one or more
        // vertices were moved it is time to consume their delayed event
        // and update markers rotation.
        if (!sender.__moved) {
            return;
        }

        graph.model.beginUpdate();
        try {
            while (sender.__moved.length > 0) {
                var edge_markers = sender.__moved.pop();
                var edge = edge_markers[0];
                var markers = edge_markers[1];
                for (var i = 0; i < markers.length; i++) {
                    var marker = markers[i];
                    if (marker.isTable()) {  // Tables are not actual markers.
                        continue;
                    }
                    var markerStyle = graphs.utils.obtainDecorationStyle(
                        graph, edge, marker.getStyle());
                    graph.model.setStyle(marker, markerStyle);
                }
            }
        } finally {
            graph.model.endUpdate();
        }
    };
    graph.addListener(mxEvent.REFRESH, onRefresh);

    // DEBUG -------------------------------------------------------------------

    graph.container.addEventListener(
        "mousedown",
        function(event) {
            if (event.shiftKey) {
                console.log(event.clientX, event.clientY);
            }
        },
        false
    );

    return editor;
};

/**
 * Helper method to parse styles received in format used by `GraphStyles`
 * objects.
 *
 * @param {Object} rawStyles A "dict-of-dict" object configuring additional
 * styles.
 * @returns {Object} Styles converted to mxGraph format.
 */
graphs.parseStyles = function parseStyles (rawStyles) {
    "use strict";

    if (!rawStyles) {
        return null;
    }

    var styles = {};

    var styleMap = {};
    /* jshint -W069 */
    styleMap['shape'] = mxConstants.STYLE_SHAPE;
    styleMap['fill_color'] = mxConstants.STYLE_FILLCOLOR;
    styleMap['fill_opacity'] = mxConstants.STYLE_FILL_OPACITY;
    styleMap['foldable'] = mxConstants.STYLE_FOLDABLE;
    styleMap['stroke_opacity'] = mxConstants.STYLE_STROKE_OPACITY;
    styleMap['stroke_color'] = mxConstants.STYLE_STROKECOLOR;
    styleMap['dashed'] = mxConstants.STYLE_DASHED;
    styleMap['vertical_label_position'] = mxConstants.STYLE_VERTICAL_LABEL_POSITION;
    styleMap['vertical_align'] = mxConstants.STYLE_VERTICAL_ALIGN;
    styleMap['end_arrow'] = mxConstants.STYLE_ENDARROW;
    /* jshint +W069 */

    var hop = Object.prototype.hasOwnProperty;
    for (var name in rawStyles) {
        if (!hop.call(rawStyles, name)) {
            continue;
        }
        var style = rawStyles[name];

        styles[name] = {};
        for (var key in style) {
            if (!hop.call(style, key)) {
                continue;
            }

            var mapping = styleMap[key];
            if (mapping === undefined) {
                throw Error("Couldn't find style mapping for " +
                    key + " in style " + name);
            }

            styles[name][mapping] = style[key];
        }
    }

    return styles;
};
