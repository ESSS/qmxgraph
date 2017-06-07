/*global graphs*/
/*global namespace */
/*global mxClient */

namespace('graphs');

/**
 * Creates a standalone graph drawing widget in browser window.
 *
 * @param {HTMLElement} container Div containing graph widget.
 * @param {Object} options Options configuring features of graph.
 * @param {Object} styles Additional styles available for graph.
 */
graphs.runStandAlone = function runStandAlone (container, options, styles) {
    "use strict";

    if (!mxClient.isBrowserSupported())
    {
        throw Error('Browser is not supported by mxGraph');
    } else {
        if (!options) {
            throw Error("Options undefined!");
        }
        if (!styles) {
            throw Error("Styles undefined!");
        }
        styles = graphs.parseStyles(styles);

        // Keeping it in window to help with debugging
        window.graphEditor = graphs.createGraph(container, options, styles);
        window.api = new graphs.Api(window.graphEditor);
    }
};


/**
 * @returns {boolean} Indicates if standalone graph drawing widget is running.
 */
graphs.isRunning = function isRunning() {
    "use strict";

    return !!window.graphEditor;
};
