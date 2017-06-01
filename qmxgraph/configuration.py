
class GraphOptions(object):
    """
    Object that configures features available in graph drawing widget.
    """

    def __init__(
        self,
        cells_movable=True,
        cells_connectable=True,
        cells_cloneable=True,
        cells_resizable=True,
        allow_create_target=False,
        allow_dangling_edges=False,
        multigraph=False,
        enable_cloning=True,
        show_grid=True,
        snap_to_grid=True,
        show_highlight=True,
        show_outline=False,
        connection_image=None,
        port_image=None,
        font_family=None,
    ):
        """
        :param bool cells_movable: Specifies if the graph should allow moving
            of cells.
        :param bool cells_connectable: Enables new edges between vertices of
            graph.
        :param bool cells_cloneable: Enables the cells to be cloned pressing
            ctrl and dragging them.
        :param bool cells_resizable: Specifies if vertices in graph can be
            resized.
        :param bool allow_create_target: Defines if clones the source if new
            connection has no target.
        :param bool allow_dangling_edges: Defines if it can create edges when
            they don't connect two vertices.
        :param bool multigraph: Allow multiple edges between nodes
        :param bool enable_cloning: Enables cloning by control-drag.
        :param bool show_grid: Show a grid in background to aid users.
        :param bool snap_to_grid: Snap to background grid when moving vertices
            in graph.
        :param bool show_highlight: Show highlight when it hovers over a cell
            in graph.
        :param bool show_outline: Show outline of graph in a floating window.
        :param tuple[str, int, int]|None connection_image: If configured,
            this image is shown to user when he hovers a vertex. It can be
            clicked and dragged to create edges. Respectively, formed by
            image path, its width and height.
        :param tuple[str, int, int]|None port_image: Replaces image in
            connection ports. Respectively, formed by image path, its width and
            height.
        :param tuple[str]|None font_family: Defines the default family for
            all fonts in graph. It configures a priority list, trying always to
            use the left-most family first.
        """
        self._cells_movable = cells_movable
        self._cells_connectable = cells_connectable
        self._cells_cloneable = cells_cloneable
        self._cells_resizable = cells_resizable
        self._allow_create_target = allow_create_target
        self._allow_dangling_edges = allow_dangling_edges
        self._multigraph = multigraph
        self._enable_cloning = enable_cloning
        self._snap_to_grid = snap_to_grid
        self._show_grid = show_grid
        self._show_highlight = show_highlight
        self._show_outline = show_outline
        self._connection_image = connection_image
        self._port_image = port_image
        self._font_family = font_family

    @property
    def cells_movable(self):
        return self._cells_movable

    @property
    def cells_connectable(self):
        return self._cells_connectable

    @property
    def cells_cloneable(self):
        return self._cells_cloneable

    @property
    def cells_resizable(self):
        return self._cells_connectable

    @property
    def allow_create_target(self):
        return self._allow_create_target

    @property
    def allow_dangling_edges(self):
        return self._allow_dangling_edges

    @property
    def multigraph(self):
        return self._multigraph

    @property
    def enable_cloning(self):
        return self._enable_cloning

    @property
    def show_grid(self):
        return self._show_grid

    @property
    def snap_to_grid(self):
        return self._snap_to_grid

    @property
    def show_highlight(self):
        return self._show_highlight

    @property
    def show_outline(self):
        return self._show_outline

    @property
    def connection_image(self):
        return self._connection_image

    @property
    def port_image(self):
        return self._port_image

    @property
    def font_family(self):
        return self._font_family

    def as_dict(self):
        return {
            'cells_movable': self._cells_movable,
            'cells_connectable': self._cells_connectable,
            'cells_cloneable': self._cells_cloneable,
            'cells_resizable': self._cells_resizable,
            'allow_create_target': self._allow_create_target,
            'allow_dangling_edges': self._allow_dangling_edges,
            'multigraph': self._multigraph,
            'enable_cloning': self._enable_cloning,
            'show_grid': self._show_grid,
            'snap_to_grid': self._snap_to_grid,
            'show_highlight': self._show_highlight,
            'show_outline': self._show_outline,
            'connection_image': self._connection_image,
            'port_image': self._port_image,
            'font_family': self._font_family,
        }


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
            'shape',
            'fill_color',
            'fill_opacity',
            'foldable',
            'stroke_color',
            'stroke_opacity',
            'dashed',
            'vertical_label_position',
            'vertical_align',
            'end_arrow',
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
