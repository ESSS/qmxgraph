/*global mxConstants */

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
    var dy = targetState.y - sourceState.y;
    var dx = targetState.x - sourceState.x;
    var atan = Math.atan2(dy, dx);
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

    if (style === null || style === undefined || style.length === 0)
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
            var parts = style.split(';')
            for (var i = 0; i < parts.length; ++i)
            {
                var current = parts[i];
                var current_key = current.split('=')[0];
                if (current_key == key)
                {
                    // Just to find the key index
                    break;
                }
            }

            var updated_key_value = key + '=' + value;
            style = parts.slice(0, i).concat(updated_key_value).concat(parts.slice(i+1, parts.length)).join(';');
        }
    }

    return style;
};

/**
 * Removes the given key in an inline style.
 *
 * @param {string} style An inline style of mxGraph.
 * @param {string} key Key in style.
 * @returns {string} New inline style with the key removed.
 */
graphs.utils.removeStyleKey = function removeStyleKey (style, key) {
    "use strict";

    if (style === null || style === undefined || style.length === 0)
    {
        return style;
    }

    var index = style.indexOf(key+'=');

    if (index >= 0)
    {
        var parts = style.split(';')
        for (var i = 0; i < parts.length; ++i) {
          var current = parts[i];
          if (current.split('=')[0] == key) {
              break;
          }
        }
        style = parts.slice(0, i).concat(parts.slice(i+1, parts.length)).join(';');
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

    // Obtain customized base rotation in the element's style
    // TODO: handle multiple names (overrides) in the baseStyle for obtaining desired style
    var styleName = baseStyle.split(';')[0];
    var styleSheet = graph.stylesheet.styles[styleName];

    // + 90 as rotation of objects in mxGraph, or at least when using rotation
    // by style, have 0 degrees concurrent with X axis.
    var baseRotation = mxUtils.getValue(styleSheet, mxConstants.STYLE_DECORATION_BASE_ROTATION, 90);

    rotation = (rotation + baseRotation) % 360;

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
    "use strict";
    return Object.prototype.toString.call(value) === '[object Object]';
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
    "use strict";
    return (attrName in object) ? object[attrName] : defaultValue;
};

/**
 * The description of a table contents.
 *
 * @typedef {Object} graphs.utils.TableDescription
 * @property {string} [tag='table'] The html tag used to create the table.
 * @property {graphs.utils.TableRowDescription[]} contents The row that compose the table.
 */

/**
 * The description of a table row contents.
 *
 * @typedef {Object} graphs.utils.TableRowDescription
 * @property {string} [tag='tr'] The html tag used to create the table row. Normal {@link string}
 * elements will be interpreted as {@link graphs.utils.TableDataDescription) elements with all the
 * default values and it's contents equal to a tuple of one element (the {@link string} used).
 * @property {(string|graphs.utils.TableDataDescription)[]} contents The cells that compose the row.
 */

/**
 * The description of a table cell that could span over multiple columns or rows.
 *
 * @typedef {Object} graphs.utils.TableDataDescription
 * @property {string} [tag='td'] The html tag used to create the table cell.
 * @property {(string|graphs.utils.ImageDescription)[]} contents The elements that compose the cells. Plain
 * strings are escaped to properly render in the generated HTML and all the content is concatenated.
 * @property {number} [colspan=1] The number of columns this cell span over.
 * @property {number} [rowspan=1] The number of rows this cell span over (value of 0 means over
 * all remaining table rows).
 */

/**
 * The description of a image.
 *
 * @typedef {Object} graphs.utils.ImageDescription
 * @property {string} tag The html tag used to create the image element. This value must be "img".
 * @property {string} src  The URI of the resource. Special characters can be used an will be
 * properly escaped.
 * @property {number} width The desired width for the image.
 * @property {number} height The desired height for the image.
 */

/**
 * @param {graphs.utils.TableDescription} contents A description of the table contents.
 * @param {string} title Title of table.
 * @returns {string} A HTML table that contains given contents and title.
 */
graphs.utils.createTableElement = function createTableElement (contents, title) {
    "use strict";

    var isObject = graphs.utils.isObject;
    var escapeHtml = graphs.utils.escapeHtml;

    /**
     * @param {string|graphs.utils.TableDataDescription} data
     */
    var createTableData = function createTableDataContents (data) {
        if (!isObject(data)) {
            return '<td>' + escapeHtml(data) + '</td>';
        }

        var td_defaults = [
            ['colspan', 1],
            ['rowspan', 1],
            ['style', null]
        ];
        var result = '<td';
        for (var i = 0; i < td_defaults.length; ++i) {
            var attr_name = td_defaults[i][0];
            if (data[attr_name] !== td_defaults[i][1]) {
                result += ' ' + attr_name + '="' + data[attr_name] + '"';
            }
        }
        result += '>';
        var dataContents = data.contents;
        for (var index = 0; index < dataContents.length; ++index) {
            var element = dataContents[index];
            if (isObject(element)) {
                result += '<img src="' + element.src;
                result += '" width="' + element.width + '" height="' + element.height + '">';
            } else {
                result += escapeHtml(element);
            }
        }
        result += '</td>';
        return result;
    };

    var table = '<table width="100%" border="1" cellpadding="4" class="table-cell-title">';
    table += '<tr><th colspan="2">' + title + '</th></tr>';
    table += '</table>';
    table += '<div class="table-cell-contents-container">' +
        '<table width="100%" border="1" cellpadding="4" class="table-cell-contents">';

    var tableContents = contents.contents;
    for (var rowIndex = 0; rowIndex < tableContents.length; ++rowIndex) {
        var rowContents = tableContents[rowIndex].contents;
        table += '<tr>';
        for (var colIndex = 0; colIndex < rowContents.length; ++colIndex) {
            table += createTableData(rowContents[colIndex]);
        }
        table += '</tr>';
    }
    table += '</table>';
    table += '</div>';

    return table;
};

/**
 * Replace html "unsafe" characters on a given string.
 * From https://stackoverflow.com/a/4835406/783219
 *
 * @param {string} text The string to be escaped.
 * @returns {string}
 */
graphs.utils.escapeHtml = function escapeHtml (text) {
    "use strict";
    var map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
};
