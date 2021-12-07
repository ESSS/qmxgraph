/**
 * These are some polyfils or fixes.
 */

// In Qt 5.6.2 String.prototype.lastIndexOf is broken.
// https://bugreports.qt.io/browse/QTBUG-54287
if ('asd'.lastIndexOf('s') !== 1) {
    /**
     * See: https://developer.mozilla.org/en/docs/Web/JavaScript/Reference/Global_Objects/String/lastIndexOf
     * This implementation uses:
     * - String
     * - String.prototype.length
     * - String.prototype.substr
     * - parseInt
     */
    String.prototype.lastIndexOf = function lastIndexOf(
        searchValue,
        fromIndex
    ) {
        'use strict'
        searchValue = String(searchValue)
        var searchValueLength = searchValue.length
        var thisLength = this.length
        if (typeof fromIndex === 'undefined') {
            fromIndex = thisLength - searchValueLength
        } else {
            fromIndex = parseInt(fromIndex, 10) || 0
        }
        if (fromIndex < 0) {
            fromIndex = 0
        } else if (fromIndex >= thisLength) {
            fromIndex = thisLength - searchValueLength
        }
        for (; fromIndex >= 0; --fromIndex) {
            if (this.substr(fromIndex, searchValueLength) === searchValue) {
                return fromIndex
            }
        }
        return -1
    }
}
