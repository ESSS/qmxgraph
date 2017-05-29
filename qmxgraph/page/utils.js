/*global mxUtils */

/*global graphs */

/*global namespace */

/**
 * Namespace containing methods that help create and manage a graph drawing
 * widget, covering some holes in public interface of mxGraph.
 *
 * @namespace graphs.utils
 */
namespace('graphs.utils');

/**
 * Calculates the angle formed by terminals of an edge.
 *
 * @param {mxGraph} graph A graph.
 * @param {mxCell} edge An edge in graph.
 * @returns {number} Angle in degrees.
 */
graphs.utils.calculateEdgeAngle = function calculateEdgeAngle (graph, edge) {
    "use strict";

    var view = graph.view;
    var sourceState = view.getState(edge).getVisibleTerminalState(true);
    var targetState = view.getState(edge).getVisibleTerminalState(false);
    var atan = Math.atan(
        (targetState.y - sourceState.y) / (targetState.x - sourceState.x));
    return mxUtils.toDegree(atan) % 360;
};

/**
 * A less exotic and more straight-forward version of `mxUtils.setStyleFlag`.
 * Changes value of key in an inline style using format defined by mxGraph.
 *
 * @param {string} style An inline style of mxGraph.
 * @param {string} key Key in style.
 * @param {*} value New value of key in style.
 * @returns {string} New inline style with updated key.
 */
graphs.utils.setStyleKey = function setStyleKey (style, key, value) {
    "use strict";

    if (value === true) {
        value = '1';
    } else if (value === false) {
        value = '0';
    }

    if (style === null || style.length === 0)
    {
        style = key + '=' + value;
    }
    else
    {
        var index = style.indexOf(key+'=');

        if (index < 0)
        {
            var sep = (style.charAt(style.length-1) === ';') ? '' : ';';
            style = style + sep + key + '=' + value;
        }
        else
        {
            var cont = style.indexOf(';', index);

            style = style.substring(0, index) + key + '=' + value +
                ((cont >= 0) ? style.substring(cont) : '');
        }
    }

    return style;
};

/**
 * Obtain decoration style, with most up-to-date rotation.
 *
 * Decorations have their rotation define as a style, as
 * `rotate` method of mxGeometry didn't produce reliable results. Rotation
 * is determined by angle of terminals of parent edge. Not rotations aren't
 * cumulative, a marker updating its rotation r' will replace former rotation r.
 *
 * @param {mxGraph} graph A graph.
 * @param {mxCell} edge Edge that contains decoration.
 * @param {string} baseStyle Inline style to be used as base for decoration.
 * @returns {string} Inline style for a decoration.
 */
graphs.utils.obtainDecorationStyle = function obtainDecorationStyle (
    graph, edge, baseStyle) {
    "use strict";

    var rotation = graphs.utils.calculateEdgeAngle(graph, edge);

    // + 90 as rotation of objects in mxGraph, or at least when using rotation
    // by style, have 0 degrees concurrent with X axis.
    rotation = (rotation + 90) % 360;

    // Rotation style must be integers in [0, 360] interval.
    if (rotation < 0) {
        rotation += 360;
    }
    rotation = Math.round(rotation);
    return graphs.utils.setStyleKey(baseStyle, 'rotation', rotation);
};

/**
 * Converts from screen coordinates to graph coordinates, taking in account
 * scale and translation of graph.
 *
 * TODO: there may be some method for this in mxGraph, but I couldn't figure it out so far
 *
 * @param {mxGraph} graph A graph.
 * @param {number} x X coordinate in screen coordinates
 * @param {number} y Y coordinate in screen coordinates
 * @returns {{x: number, y: number}} Converted coordinates.
 */
graphs.utils.adjustCoordinates = function adjustCoordinates (graph, x, y) {
    "use strict";

    // Take in account scroll position to convert screen-to-graph-coordinates
    var dx = (window.pageXOffset || document.scrollLeft) - (document.clientLeft || 0);
    if (isNaN(dx)) {
        dx = 0;
    }

    var dy = (window.pageYOffset || document.scrollTop) - (document.clientTop || 0);
    if (isNaN(dy)) {
        dy = 0;
    }

    // Now take in account graph's own translation and scale (changed by
    // use of outline tool, for instance)
    var finalX = (x + dx) / graph.view.scale - graph.view.translate.x;
    var finalY = (y + dy) / graph.view.scale - graph.view.translate.y;

    return {x: finalX, y: finalY};
};

/**
 * Determines it some value is an object not some build-in. Relies on {@link Object#toString}
 * having the default value
 *
 * @param {*} value The value tested.
 * @returns {boolean}
 */
graphs.utils.isObject = function isObject (value) {
    return Object.prototype.toString.call(value) === '[object Object]'
};

/**
 * Returns the chosen attribute from the given object.
 *
 * @param {Object} object The object containing the selected property.
 * @param {string} attrName The name of the property.
 * @param {*} [defaultValue=undefined] If the chosen property in not present in the given object
 * this value is returned.
 * @returns {*} The property value or `defaultValue`.
 */
graphs.utils.getValue = function getValue (object, attrName, defaultValue) {
    return (attrName in object) ? object[attrName] : defaultValue;
};

/**
 * The description of a table cell that should span over multiple columns or rows.
 * @typedef {Object} SpannedCellDesc
 * @property {string} value The actual content of the cell.
 * @property {number} [colspan=1] The number of columns this cell span over.
 * @property {number} [rowspan=1] The number of rows this cell span over (value of 0 means over
 * all remaining table rows).
 */

/**
 * @param {Array} contents An array of arrays. The 1st level arrays correspond
 * to rows. The 2nd level arrays correspond to columns of each row.
 * @param {string} title Title of table.
 * @returns {string} A HTML table that contains given contents and title.
 */
graphs.utils.createTableElement = function createTableElement (contents, title) {
    "use strict";

    var isObject = graphs.utils.isObject;
    var getValue = graphs.utils.getValue;

    var table = '<table width="100%" border="1" cellpadding="4" class="table-cell-title">';
    table += '<tr><th colspan="2">' + title + '</th></tr>';
    table += '</table>';
    table += '<div class="table-cell-contents-container">' +
        '<table width="100%" border="1" cellpadding="4" class="table-cell-contents">';
    for (var row = 0; row < contents.length; row++) {
        table += '<tr>';
        for (var col = 0; col < contents[row].length; col++) {
            var data = contents[row][col];
            if (isObject(data)) {
                var spanAttrs = (
                    'colspan="' + getValue(data, 'colspan', 1) + '" '
                    + 'rowspan="' + getValue(data, 'rowspan', 1) + '"'
                );
                table += '<td ' + spanAttrs + '>' + data.value + '</td>';
            } else {
                table += '<td>' + data + '</td>';
            }
        }
        table += '</tr>';
    }
    table += '</table>';
    table += '</div>';

    return table;
};

/**
 * In case cell is added too close to graph boundaries resize the container.
 *
 * @param {mxGraph} graph A graph.
 * @param {mxCell} cell A cell in graph.
 */
graphs.utils.resizeContainerOnDemand = function resizeContainerOnDemand (graph, cell) {
    "use strict";

    var bbox = graph.getBoundingBox([cell]);
    var containerWidth = Math.max(
        graph.container.offsetWidth, bbox.x + bbox.width);
    var containerHeight = Math.max(
        graph.container.offsetHeight, bbox.y + bbox.height);
    graph.doResizeContainer(containerWidth, containerHeight);
};
