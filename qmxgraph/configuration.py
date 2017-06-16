import attr

from qmxgraph.extra_attr_validators import tuple_of


_is_bool = attr.validators.instance_of(bool)


def _is_image_configuration(inst, attr, value):
    """
    The description of `inst`, `attrs`, and `value` comes from:
    http://www.attrs.org/en/stable/examples.html#decorator

    :param inst: The *instance* that’s being validated.
    :param attr: the *attribute* that it’s validating.
    :param value: The value that is passed for it.
    :raise TypeError: If the validation fails.
    """
    if not ((len(value) == 3) and isinstance(value[0], str)
            and isinstance(value[1], int) and isinstance(value[2], int)):
        msg = '{} must be a tuple of `(str, int, int)` but got {}'
        raise TypeError(msg.format(attr.name, repr(value)))


@attr.s(frozen=True, slots=True)
class GraphOptions(object):
    """
    Object that configures features available in graph drawing widget.

    :ivar bool allow_create_target: Defines if clones the source if new
        connection has no target.
    :ivar bool allow_dangling_edges: Defines if it can create edges when
        they don't connect two vertices.
    :ivar bool cells_cloneable: Enables the cells to be cloned pressing
        ctrl and dragging them.
    :ivar bool cells_connectable: Enables new edges between vertices of
        graph.
    :ivar bool cells_movable: Specifies if the graph should allow moving
        of cells.
    :ivar bool cells_resizable: Specifies if vertices in graph can be
        resized.
    :ivar tuple[str, int, int]|None connection_image: If configured,
        this image is shown to user when he hovers a vertex. It can be
        clicked and dragged to create edges. Respectively, formed by
        image path, its width and height.
    :ivar bool enable_cloning: Enables cloning by control-drag.
    :ivar tuple[str]|None font_family: Defines the default family for
        all fonts in graph. It configures a priority list, trying always to
        use the left-most family first.
    :ivar bool multigraph: Allow multiple edges between nodes
    :ivar tuple[str, int, int]|None port_image: Replaces image in
        connection ports. Respectively, formed by image path, its width and
        height.
    :ivar bool show_grid: Show a grid in background to aid users.
    :ivar bool show_highlight: Show highlight when it hovers over a cell
        in graph.
    :ivar bool show_outline: Show outline of graph in a floating window.
    :ivar bool snap_to_grid: Snap to background grid when moving vertices
        in graph.
    """

    allow_create_target = attr.ib(default=False, validator=_is_bool)
    allow_dangling_edges = attr.ib(default=False, validator=_is_bool)
    cells_cloneable = attr.ib(default=True, validator=_is_bool)
    cells_connectable = attr.ib(default=True, validator=_is_bool)
    cells_movable = attr.ib(default=True, validator=_is_bool)
    cells_resizable = attr.ib(default=True, validator=_is_bool)
    connection_image = attr.ib(
        default=None,
        validator=attr.validators.optional(_is_image_configuration),
    )
    enable_cloning = attr.ib(default=True, validator=_is_bool)
    font_family = attr.ib(
        default=None, validator=attr.validators.optional(tuple_of(str)))
    multigraph = attr.ib(default=False, validator=_is_bool)
    port_image = attr.ib(
        default=None,
        validator=attr.validators.optional(_is_image_configuration),
    )
    show_grid = attr.ib(default=True, validator=_is_bool)
    show_highlight = attr.ib(default=True, validator=_is_bool)
    show_outline = attr.ib(default=False, validator=_is_bool)
    snap_to_grid = attr.ib(default=True, validator=_is_bool)

    def as_dict(self):
        return attr.asdict(self)


class GraphStyles(object):
    """
    Object that configures additional styles available in graph drawing widget.

    Each key in styles dict given as input will define the *name* of style.
    Below are some reserved names:

    * 'edge': Style used by edges in graph.
    * 'group': Style used when cells are grouped in graph.
    * 'table': Style used by table cells.

    Each style key must receive as a value other dict, which will configure
    the style. All options are optional. The available options for each style
    are:

    * 'shape': Name of shape of cell. Can be any of mxGraph's default shapes
        plus the custom ones created by additional stencil files
    * 'end_arrow': End arrow of an edge. Possible values are found in
        mxGraphs constants with an ARROW-prefix
    * 'fill_color': Color used inside of cell
    * 'fill_opacity': Opacity used inside of cell between 0 and 1
    * 'stroke_color': Color used in border of cell
    * 'stroke_opacity': Opacity used in border of cell between 0 and 1
    * 'dashed': If border of cell should be dashed
    * 'vertical_label_position': vertical label position of vertices. Possible
        values are 'bottom', 'top' and 'middle'
    * 'vertical_align': vertical alignment of label text of vertices. Possible
        values are 'bottom', 'top' and 'middle'

    Example of styles:

    ```
    GraphStyles({
        'group': {
            'shape': 'rectangle',
            'fill_color': None,
            'dashed': True,
        },
        'foo': {
            'shape': 'star',
            'fill_color': '#ffffff',
        },
        'bar': {
            'fill_color': '#ff00ff',
            'dashed': True,
        },
    })
    ```
    """

    def __init__(self, styles=None):
        """
        :param dict styles: See class docs about how to configure styles dict.
        """
        self._styles = styles if styles is not None else {}
        self.validate()

    def validate(self):
        import six

        known_keys = {
            'dashed',
            'deletable',
            'end_arrow',
            'fill_color',
            'fill_opacity',
            'foldable',
            'image',
            'label_position',
            'label_rotatable',
            'no_label',
            'resizable',
            'rotatable',
            'shape',
            'start_arrow',
            'stroke_color',
            'stroke_width',
            'stroke_opacity',
            'vertical_align',
            'vertical_label_position',
        }

        invalid = {}
        for name, config in six.iteritems(self._styles):
            for key, value in six.iteritems(config):
                if key not in known_keys:
                    invalid.setdefault(name, []).append(key)

        if invalid:
            raise ValueError("Invalid keys in styles {}".format(
                ",".join(
                    "{} ({})".format(name, ", ".join(keys))
                    for name, keys in six.iteritems(invalid))))

    def as_dict(self):
        return self._styles

    def __getitem__(self, item):
        return self._styles[item]
