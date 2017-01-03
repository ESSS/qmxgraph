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
 * @param {Array} contents An array of arrays. The 1st level arrays correspond
 * to rows. The 2nd level arrays correspond to columns of each row.
 * @param {string} title Title of table.
 * @returns {string} A HTML table that contains given contents and title.
 */
graphs.utils.createTableElement = function createTableElement (contents, title) {
    "use strict";

    var table = '<table style="overflow:hidden;" width="100%" border="1" cellpadding="4" class="title">';
    table += '<tr><th colspan="2">' + title + '</th></tr>';
    table += '</table>';
    table += '<div style="overflow:auto;cursor:default;">' +
        '<table width="100%" border="1" cellpadding="4" class="contents">';
    for (var row = 0; row < contents.length; row++) {
        table += '<tr>';
        for (var col = 0; col < contents[row].length; col++) {
            table += '<td>' + contents[row][col] + '</td>';
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
