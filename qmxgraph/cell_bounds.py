"""
Classes used to represent bounds in:

- :meth:`qmxgraph.api.QmxGraphApi.on_bounds_changed`
- :meth:`qmxgraph.api.QmxGraphApi.get_cell_bounds`
- :meth:`qmxgraph.api.QmxGraphApi.set_cell_bounds`
- :attr:`qmxgraph.widget.EventsBridge.on_cell_geometry_changed`

"""


import attr


asdict = attr.asdict


_is_number = attr.validators.instance_of((int, float))


@attr.s(frozen=True, slots=True)
class ParentAnchorPosition:
    """
    This represents the anchor point relative to the parent cell.
    See :class:`CellBounds` for more details.

    The attributes are normalized to the parent bounds. For example, give
    a parent positioned at the x coordinate `50` with width `16` we
    will have:

    .. list-table::
       :widths: 50 50
       :header-rows: 1

       * - Normalized (anchor position)
         - Effective
       * - 0
         - 50 (50 + 0 * 16)
       * - 1
         - 66 (50 + 1 * 16)
       * - 2
         - 82 (50 + 2 * 16)
       * - -1
         - 34 (50 + -1 * 16)
       * - 0.5
         - 58 (50 + 0.5 * 16)

    :ivar float x: A normalized position relative to the parent's width.
    :ivar float y: A normalized position relative to the parent's height.
    """
    x = attr.ib(validator=_is_number)
    y = attr.ib(validator=_is_number)


_is_optional_parent_anchor_position = attr.validators.optional(
    attr.validators.instance_of(ParentAnchorPosition)
)


def _convert_parent_anchor_position(v):
    if not v:
        return None
    elif v.__class__ == ParentAnchorPosition:
        return v
    else:
        return ParentAnchorPosition(**v)


@attr.s(frozen=True, slots=True)
class CellBounds:
    """
    This represents the bounds of a cell. If the cell is relatively
    positioned to its parent `parent_anchor_position` should be
    supplied (not `None`).

    :ivar float x: The cell's origin horizontal position.
    :ivar float y: The cell's origin vertical position.
    :ivar float width: The cell's horizontal size.
    :ivar float height: The cell's vertical size.
    :ivar ParentAnchorPosition parent_anchor_position: When not `None`
        indicates the cell is relatively positioned to its parent.
    """
    x = attr.ib(validator=_is_number)
    y = attr.ib(validator=_is_number)
    width = attr.ib(validator=_is_number)
    height = attr.ib(validator=_is_number)
    parent_anchor_position = attr.ib(
        default=None,
        validator=_is_optional_parent_anchor_position,
        converter=_convert_parent_anchor_position,
    )
