"""
Classes to used to represent content in:

- :meth:`qmxgraph.api.QmxGraphApi.insert_table`
- :meth:`qmxgraph.api.QmxGraphApi.update_table`

"""

import attr

from qmxgraph.extra_attr_validators import tuple_of


asdict = attr.asdict


_is_int = attr.validators.instance_of(int)
_is_str = attr.validators.instance_of(str)


@attr.s(frozen=True, slots=True)
class Image:
    """
    Represents an image tag that could be embedded into a table contents.

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
    src = attr.ib(validator=_is_str)
    width = attr.ib(validator=_is_int)
    height = attr.ib(validator=_is_int)


@attr.s(frozen=True, slots=True)
class TableData:
    """
    Represents the contents of a table's cell when inserting or updating a
    table in the graph.

    :ivar str tag:
    :ivar tuple[union[str,Image]] contents: The table cell's contents.
    :ivar int colspan: The number of columns the cell should span into.
    :ivar int rowspan: The number of rows the cell should span into.
    :ivar optional[str] style: A inline style for the element.
    """
    tag = attr.ib(default='td', init=False)
    contents = attr.ib(validator=tuple_of(str, Image),
                       converter=tuple)
    colspan = attr.ib(default=1, validator=_is_int)
    rowspan = attr.ib(default=1, validator=_is_int)
    style = attr.ib(default=None, validator=attr.validators.optional(_is_str))


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
                       converter=tuple)


@attr.s(frozen=True, slots=True)
class Table:
    """
    Represents the contents of a table when inserting or updating a table in
    the graph.

    :ivar str tag:
    :ivar tuple[TableRow] contents: The table rows.
    """
    tag = attr.ib(default='table', init=False)
    contents = attr.ib(validator=tuple_of(TableRow), converter=tuple)

    def contents_after(self, caption):
        """
        Useful for testing: truncates the contents after the first row with
        the given caption and return it as a list.

        :rtype: tuple[TableRow]
        """
        seen_captions = []

        def get_caption(row):
            first_row_content = row.contents[0]
            if isinstance(first_row_content, TableData):
                return first_row_content.contents[0]
            return first_row_content

        for index, row in enumerate(self.contents):
            row_caption = get_caption(row)
            if row_caption == caption:
                break
            seen_captions.append(row_caption)
        else:
            __tracebackhide__ = True
            msg = '\nCould not find row with caption "{}" in\n{}'
            assert False, msg.format(caption, seen_captions)
        return tuple(self.contents[index + 1:])
