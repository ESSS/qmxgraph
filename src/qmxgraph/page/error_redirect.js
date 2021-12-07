/* global bridge_error_handler */

/**
 * Connects global error handler hook to error handler bridge, providing way
 * to forward errors when JavaScript is embedded on Qt web views.
 *
 * @see For `onerror` details refer to @link{https://developer.mozilla.org/en-US/docs/Web/API/GlobalEventHandlers/onerror}
 */
window.onerror = function (msg, url, lineNo, columnNo, error) {
    'use strict'

    if (typeof bridge_error_handler === 'undefined') {
        return
    }

    // Unfortunately, WebKit engine doesn't provide the error object on
    // `onerror` hook, so stack trace can't be forwarded
    if (lineNo === undefined) {
        lineNo = -1
    }

    if (columnNo === undefined) {
        columnNo = -1
    }
    msg = msg + '\nstack:\n' + error.stack
    bridge_error_handler.error_slot(msg, url, lineNo, columnNo)
}
