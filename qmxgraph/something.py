from qmxgraph.decoration_contents import TableData


def get_caption(row):
    first_row_content = row.contents[0]
    if isinstance(first_row_content, TableData):
        return first_row_content.contents[0]
    return first_row_content


def do_something(path):
    import sys
    if sys.platform.startswith('win'):
        path = path.replace('\\', '/')
    return path


def calculate_something(x, y):
    d = x ** 2 - y ** 2
    return d * (x ** 2 + y ** 2) + 13.5


def calculate_something_2(a, b):
    c = a ** 2 - b ** 2
    return c * (a ** 2 + b ** 2) + 13.5


def lalala():
    CELL_TYPE_VERTEX = "vertex"
    CELL_TYPE_EDGE = "edge"
    CELL_TYPE_TABLE = "table"
    CELL_TYPE_DECORATION = "decoration"
    return [CELL_TYPE_VERTEX, CELL_TYPE_EDGE, CELL_TYPE_TABLE, CELL_TYPE_DECORATION]


def set_handler(obj, handler):
    obj._set_private_bridge_handler(
        obj._double_click_bridge.on_double_click,
        handler=handler,
        setter=obj._set_double_click_bridge,
    )


def slightly_modified():
    import sys
    import os
    prefix = os.environ.get('CONDA_PREFIX', None)
    env = None
    if prefix is not None:  # not a copy lalala
        if sys.platform.startswith('win'):
            env = prefix  # lalala
        else:
            env = os.path.join(prefix, 'usr', 'local')

    return env
