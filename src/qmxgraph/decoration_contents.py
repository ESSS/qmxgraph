"""
Classes to used to represent content in:

- :meth:`qmxgraph.api.QmxGraphApi.insert_table`
- :meth:`qmxgraph.api.QmxGraphApi.update_table`

"""
from functools import lru_cache
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Type
from typing import Union

import attr

from qmxgraph.extra_attr_validators import tuple_of


asdict = attr.asdict


_is_int = attr.validators.instance_of(int)
_is_str = attr.validators.instance_of(str)
_tag_to_class: Dict[str, Type] = {}


def _register_decoration_class(class_):
    """
    Register a class so attributes can be automatically converted from
    `dict`'s to instances of that class.

    :param class_:
        This class is expected to be an `attr.s` decorated class with a
        "tag" `attr.ib`.
    """
    for attr_name in class_.__attrs_attrs__:
        if attr_name.name == 'tag':
            if not isinstance(attr_name.default, str):
                raise ValueError(f"{class_}'s `tag` default must be a `str`")
            if attr_name.init:
                raise ValueError(f"{class_}'s `init` must be `False`")

            _tag_to_class[attr_name.default] = class_
            _is_preprocessed_data.cache_clear()
            break
    else:
        raise ValueError(f"{class_}'s must have a `tag` attribute")


@lru_cache(maxsize=8)
def _is_preprocessed_data(raw_data_type):
    return issubclass(raw_data_type, (str, *_tag_to_class.values()))


def _convert_decoration_content_item(raw_data):
    """
    Convert some raw data (usually a `dict`) to one of the registered
    table content classes. Given that string is a valid table content
    `str` values are returned unchanged.
    """
    if _is_preprocessed_data(type(raw_data)):
        return raw_data
    else:
        if not isinstance(raw_data, dict):
            raise TypeError(f'`raw_data` must be `str` or `dict` but got {type(raw_data)}')
        raw_data = raw_data.copy()
        tag = raw_data.pop('tag', None)
        if tag is None:
            raise ValueError('`raw_data` must have a `"tag"´ item')
        class_ = _tag_to_class.get(tag)
        if class_ is None:
            raise ValueError(f"Can't locate a class for tag \"{tag}\"")

        return class_(**raw_data)


def attrib_table_contents(*classes):
    """
    Create an `attr.ib` with the validator and converter to be used
    on `contents` attributes.

    :param classes:
        The accepted classes for this contents.
    """

    def converter(v):
        return tuple(_convert_decoration_content_item(item) for item in v)

    return attr.ib(validator=tuple_of(*classes), converter=converter)


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


_register_decoration_class(Image)


@attr.s(frozen=True, slots=True, auto_attribs=True)
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

    tag: str = attr.ib(default='td', init=False)
    contents: List[Union[str, Image]] = attrib_table_contents(str, Image)
    colspan: int = attr.ib(default=1, validator=_is_int)
    rowspan: int = attr.ib(default=1, validator=_is_int)
    style: Optional[str] = attr.ib(default=None, validator=attr.validators.optional(_is_str))


_register_decoration_class(TableData)


@attr.s(frozen=True, slots=True, auto_attribs=True)
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

    tag: str = attr.ib(default='tr', init=False)
    contents: Sequence[Union[str, TableData]] = attrib_table_contents(str, TableData)


_register_decoration_class(TableRow)


@attr.s(frozen=True, slots=True, auto_attribs=True)
class Table:
    """
    Represents the contents of a table when inserting or updating a table in
    the graph.

    :ivar str tag:
    :ivar tuple[TableRow] contents: The table rows.
    """

    tag: str = attr.ib(default='table', init=False)
    contents: Sequence[TableRow] = attrib_table_contents(TableRow)

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
        return tuple(self.contents[index + 1 :])


_register_decoration_class(Table)
