// TODO: this came from behir code, see if we will want to reuse more and share somewhere

/**
 * Creates a namespace based in given string. Nested namespaces can be created with paths separated by dots (.).
 *
 * Examples:
 *
 * namespace('bob') # creates namespace 'bob'
 * namespace('alice') # creates namespace 'alice'
 * namespace('foo.bar') # creates both namespaces 'foo' and 'foo.bar'
 *
 * @see Reference: http://elegantcode.com/2011/01/26/basic-javascript-part-8-namespaces/
 *
 * @param namespaceString
 * @returns {Object} Deepest namespace that was created/retrieved from given namespace path.
 */
function namespace(namespaceString) {
    "use strict";

    var parts = namespaceString.split("."),
        parent = window,
        currentPart = "";

    for (var i = 0, length = parts.length; i < length; i++) {
        currentPart = parts[i];
        parent[currentPart] = parent[currentPart] || {};
        parent = parent[currentPart];
    }

    return parent;
}
