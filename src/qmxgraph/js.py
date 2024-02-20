import functools
import json


def prepare_js_call(fn, *args):
    """
    Prepares a JavaScript call to a function. It takes care of converting
    each argument from Python to JavaScript syntax. Note though that just
    most primitive types that have a natural conversion to JavaScript are
    supported (see `json` to learn about supported types).

    :param str fn: Name of JavaScript function.
    :param object args: Position arguments forwarded to JavaScript function.
        Since JavaScript doesn't support named arguments only this kind of
        variadic arguments is accepted unfortunately.
    :rtype: object
    :return: A JavaScript statement ready to be evaluated.
    """
    return "{fn}({args})".format(
        fn=fn,
        args=", ".join(_js_dump(v) for v in args),
    )


class Variable(object):
    """
    Object that can be used when an actual JavaScript name is need in a
    JavaScript statement. Objects of this type aren't encoded as strings to
    JavaScript as they refer to an actual JavaScript symbol.

    For instance,

    .. code-block::

        prepare_js_call('foo', Variable('bar'))

    generates a JavaScript statement string ``foo(bar)``, basically telling
    JavaScript to call ``foo`` with whatever object is bound to ``bar`` on
    JS side.

    On the other hand

    .. code-block::

        prepare_js_call('foo', 'bar')

    generates a JavaScript statement string ``foo('bar')``, where JavaScript
    would call ``foo`` with a string ``'bar'``.

    This kind of object is convenient when generating statements involving
    bridge objects that were previously added to JavaScript window object,
    for instance.
    """

    def __init__(self, name):
        """
        :param str name: Name of a JavaScript object.
        """
        self.name = name


class _JavaScriptEncoder(json.JSONEncoder):
    """
    A JSON encoder tailored to generate JavaScript statements.
    """

    def encode(self, o):
        if type(o) is Variable:
            return o.name

        return json.JSONEncoder.encode(self, o)


_js_dump = functools.partial(json.dumps, cls=_JavaScriptEncoder)
