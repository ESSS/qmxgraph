import attr


asdict = attr.asdict


def _tuple_of_impl(inst, attr, value, *, child_types):
    """
    The validator implementation for `tuple_of`.
    The description of `inst`, `attrs`, and `value` comes from:
    http://www.attrs.org/en/stable/examples.html#decorator

    :param inst: The *instance* that’s being validated.
    :param attr: the *attribute* that it’s validating.
    :param value: The value that is passed for it.
    :param tuple[type] child_types: A keyword only argument specifying the
        accepted types.
    :raise TypeError: If the validation fails.
    """
    if isinstance(value, tuple):
        for i, v in enumerate(value):
            if not isinstance(v, child_types):
                msg = ("'{name}' must be a tuple of {types!r} but got"
                       " {value!r} and item in index {i} is not one of"
                       " the expected types")
                msg = msg.format(name=attr.name, types=child_types,
                                 value=value, i=i)
                raise TypeError(msg)
    else:
        msg = "'{name}' must be a tuple but got {value!r}"
        raise TypeError(msg.format(name=attr.name, value=value))


def tuple_of(*child_types):
    """
    Creates an validator that accept an item with any type listed or a tuple
    with any of the accept types combination). A tuple is used due it's
    immutable nature.

    :param list[type] child_types:
    :rtype: Callable
    :return: An callable to be used as an validator with the `attr` module.
    ..see: http://www.attrs.org/en/stable/examples.html#callables
    """
    import functools
    return functools.partial(_tuple_of_impl, child_types=child_types)


@attr.s(frozen=True, slots=True)
class Image:
    """
    Represet an image tag that could be embedded into a table contents.

    The image's width and height are required since mxgraph will render the
    html in a helper container in order to get the cell's size. To avoid the
    cell size to be wrongly calculated we got some options like passing the
    image's size explicitly (as done here) or force the user to pre load the
    images so when rendering the html the image is already loaded and the
    correct size is used.

    :ivar str tag:
    :ivar str source: The URL to the image, data URIs can be used.
    :ivar int width: The desired width for the image.
    :ivar int height: The desired height for the image.
    """
    tag = attr.ib(default='img', init=False)
    src = attr.ib(validator=attr.validators.instance_of(str))
    width = attr.ib(validator=attr.validators.instance_of(int))
    height = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(frozen=True, slots=True)
class TableData:
    """
    Represents the contents of a table's cell when inserting or updating a
    table in the graph.

    :ivar str tag:
    :ivar tuple[union[str,Image]] contents: The table cell's contents.
    :ivar int colspan: The number of columns the cell should span into.
    :ivar int rowspan: The number of rows the cell should span into.
    """
    tag = attr.ib(default='td', init=False)
    contents = attr.ib(validator=tuple_of(str, Image),
                       convert=tuple)
    colspan = attr.ib(default=1, validator=attr.validators.instance_of(int))
    rowspan = attr.ib(default=1, validator=attr.validators.instance_of(int))


@attr.s(frozen=True, slots=True)
class TableRow:
    """
    Represents the contents of a table's row when inserting or updating a
    table in the graph.

    :ivar str tag:
    :ivar tuple[union[str,TableData]] contents: The row's cells. Normal `str`
        elements will be interpreted as `TableData` elements with all the
        default values and it's contents equal to a tuple of one element (the
        `str` used).
    """
    tag = attr.ib(default='tr', init=False)
    contents = attr.ib(validator=tuple_of(str, TableData),
                       convert=tuple)


@attr.s(frozen=True, slots=True)
class Table:
    """
    Represents the contents of a table when inserting or updating a table in
    the graph.

    :ivar str tag:
    :ivar tuple[TableRow] contents: The table rows.
    """
    tag = attr.ib(default='table', init=False)
    contents = attr.ib(validator=tuple_of(TableRow), convert=tuple)
