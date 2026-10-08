/* global bridge_error_handler */

/**
 * Connects global error handler hook to error handler bridge, providing way
 * to forward errors when JavaScript is embedded on Qt web views.
 *
 * @see For `onerror` details refer to @link{https://developer.mozilla.org/en-US/docs/Web/API/GlobalEventHandlers/onerror}
 */
window.onerror = function (msg, url, lineNo, columnNo, error) {
    "use strict";

    if (typeof bridge_error_handler === "undefined") {
        return;
    }

    // Unfortunately, WebKit engine doesn't provide the error object on
    // `onerror` hook, so stack trace can't be forwarded
    if (lineNo === undefined) {
        lineNo = -1;
    }

    if (columnNo === undefined) {
        columnNo = -1;
    }

    if (error !== null) {
        msg = msg + "\nstack:\n" + error.stack;
    }

    bridge_error_handler.error_slot(msg, url, lineNo, columnNo);
};

/**
 * Evaluates a script on behalf of Python, returning the value of its last statement.
 *
 * Chromium reports uncaught errors from scripts injected by `runJavaScript` as a bare
 * "Script error." with no details. Evaluated from here, the code counts as the page's own,
 * so `onerror` above receives its message and stack.
 *
 * @param {string} source The script to evaluate, in global scope.
 * @returns {*} The value of the script's last statement.
 */
window.qmxgraphEval = function (source) {
    "use strict";
    /* jshint evil: true */
    return (0, eval)(source);
};
