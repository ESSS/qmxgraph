import pytest


def pytest_configure(config):
    # During warm up, clean up the temporary files/objects used by ports
    # fixture from previous runs. Note these files are shared among ALL slaves
    # of pytest so they can't reliably be removed by a fixture.
    config.cache.set('qmxgraph/ports', [])

    import os

    lock_file = _get_port_lock_filename(config.rootdir)
    if os.path.isfile(lock_file):
        os.remove(lock_file)

    import socket

    socket.setdefaulttimeout(15.0)


# Fixtures --------------------------------------------------------------------


@pytest.fixture
def phantomjs_driver(capabilities, driver_path, port):
    """
    Overrides default `phantomjs_driver` driver from pytest-selenium.

    Default implementation uses ephemeral ports just as our tests but
    it doesn't provide any way to configure them, for this reason we basically
    recreate the driver fixture using port fixture.
    """
    kwargs = {}
    if capabilities:
        kwargs['desired_capabilities'] = capabilities
    if driver_path is not None:
        kwargs['executable_path'] = driver_path

    kwargs['port'] = port.get()

    from selenium.webdriver import PhantomJS

    return PhantomJS(**kwargs)


@pytest.fixture
def driver_args():
    return ['--debug=true']


@pytest.fixture(autouse=True)
def enable_qgraph_debug():
    """
    During tests it is healthy to have this enable to fail as early as possible
    and have as much information as possible about errors.
    """
    import qmxgraph.debug

    qmxgraph.debug.set_qmxgraph_debug(True)
    yield
    qmxgraph.debug.set_qmxgraph_debug(False)


@pytest.fixture(scope='session')
def port(request):
    """
    Each process hosting a graph page must use an unique port. This fixture
    aids that by providing `get` method, which provides an ephemeral port
    exclusive for every call.
    """
    return Port(request.config.rootdir, request.config.cache)


class Port(object):
    def __init__(self, rootdir, cache):
        self.rootdir = rootdir
        self.cache = cache

    def get(self):
        """
        Gets an unused, ephemeral port.

        :rtype: int
        :return: A free port.
        """
        # We don't care about port number used. To bind to an ephemeral port
        # just bind to port 0, as kernel will select an unused port number.
        # It also works on Windows.
        #
        # Note though there is a small chance 2 different processes ask kernel
        # same time for a socket around same time AND receive same port as
        # answer. To avoid concurrency issues like that it uses a file lock
        # (to avoid race conditions with other processes) and
        # keeps a list of ports used so far by these tests. Note this can't
        # prevent processes outside of this scope from acquiring same ports,
        # but that is hardly impossible to prevent anyway.
        #
        # Reference: http://man7.org/linux/man-pages/man7/ip.7.html
        import os
        import errno
        import time

        lock_file = _get_port_lock_filename(self.rootdir)
        attempts = 10
        port_ = None
        while attempts > 0:
            try:
                f = os.open(lock_file, os.O_CREAT | os.O_EXCL)
                os.close(f)
            except OSError as e:
                import sys

                # On Windows it seems to sometimes to fail because of lack of
                # privileges, for some reason.
                if e.errno == errno.EEXIST or (
                    sys.platform.startswith('win') and e.errno == errno.EACCES
                ):
                    time.sleep(0.1)
                    continue
                else:
                    raise e

            try:
                import socket

                s = socket.socket()
                s.bind(('', 0))
                port_ = s.getsockname()[1]
                s.close()

                ports_ = self.cache.get('qmxgraph/ports', [])
                unique = port_ not in ports_

                if unique:
                    self.cache.set('qmxgraph/ports', ports_ + [port_])
                    break
                else:
                    attempts -= 1
            finally:
                os.remove(lock_file)

        if attempts == 0:
            raise IOError("Unable to obtain unique port after " "{} attempts".format(attempts))

        return port_


@pytest.fixture(scope='session')
def host(port):
    """
    Hosts a graph page, with a series of simple default options and styles.

    :type port: Port
    :rtype: qmxgraph.host_graph.Host
    :return: Object with details about hosted graph page.
    """
    from qmxgraph.configuration import GraphStyles

    styles = GraphStyles(
        {
            'group': {
                'shape': 'rectangle',
                'fill_color': '#ff93ba',
                'dashed': True,
            },
            'table': {
                'fill_color': '#ffffff',
                'stroke_opacity': 0,
                'fill_opacity': 0,
            },
            'yellow': {
                'fill_color': '#ffff00',
            },
            'purple': {
                'fill_color': '#ff00ff',
            },
        }
    )

    from qmxgraph.configuration import GraphOptions

    options = GraphOptions(
        # Highlight disabled for this kind of test as interferes a lot with
        # some mouse events, preventing Selenium from clicking desired
        # HTML elements.
        show_highlight=False,
    )

    from qmxgraph import server

    with server.host(port=port.get(), styles=styles, options=options) as host_:
        yield host_


@pytest.fixture
def wait_graph_page_ready(selenium):
    """
    :type selenium: selenium.webdriver.remote.webdriver.WebDriver
    :rtype: callable
    :return: Wait until graph page is ready to use, raise if timeout expires.
    """
    import functools

    return functools.partial(_wait_graph_page_ready, selenium=selenium)


@pytest.fixture
def selenium_extras(selenium):
    """
    :type selenium: selenium.webdriver.remote.webdriver.WebDriver
    :rtype: SeleniumExtras
    :return: Some additional features not found in Selenium basic fixture.
    """
    return SeleniumExtras(selenium)


class SeleniumExtras(object):
    def __init__(self, selenium):
        self.selenium = selenium

    def get_exception_message(self, e):
        """
        :type e: _pytest._code.code.ExceptionInfo
        :rtype: str
        :return: Error messaged extracted from an `WebDriverException`,
            raised when errors happen during tests using Selenium.
        """
        if self.selenium.name == 'phantomjs':
            # PhantomJS driver for whatever reason encodes error message
            # in JSON...
            import json

            return json.loads(e.value.msg)["errorMessage"]
        else:
            return e.value.msg


@pytest.fixture
def graph_cases(selenium, host):
    """
    Factory method that allows to draw preconfigured graphs and manipulate them
    with a series of helpful methods.

    :type selenium: selenium.webdriver.remote.webdriver.WebDriver
    :type host: qmxgraph.server.Host
    :rtype: GraphCaseFactory
    :return: Factory able to create cases.
    """
    return GraphCaseFactory(selenium=selenium, host=host)


@pytest.fixture
def graph_cases_factory(selenium):
    """
    :type selenium: selenium.webdriver.remote.webdriver.WebDriver
    :rtype: callable
    :return: Constructor method to create a graph cases factory with a custom
        host.
    """
    return lambda host: GraphCaseFactory(selenium=selenium, host=host)


def pytest_collection_modifyitems(items):
    """
    Marks all tests which use the graph_cases fixture as "flaky".

    Unfortunately we've been unable to properly fix some flaky failures with tests using this fixture (#4)*.

    See pytest-rerunfailures plugin for more information.
    """
    import os

    if os.environ.get('CI', 'false') != 'true':
        return
    for item in items:
        if 'graph_cases' in getattr(item, 'fixturenames', []):
            item.add_marker(pytest.mark.flaky(reruns=3))


class GraphCaseFactory(object):
    """
    Creates cases with graphs already preconfigured and with helper methods
    available.
    """

    def __init__(self, selenium, host):
        self._selenium = selenium
        self._host = host
        self.case_map = {
            "empty": BaseGraphCase,
            "1v": Graph1Vertex,
            "1v_1p": Graph1Vertex1Port,
            "1v_style": Graph1VertexWithStyle,
            "2v": Graph2Vertices,
            "2v_1e": Graph2Vertices1EdgeByCode,
            "3v_1e": Graph3Vertices1EdgeByCode,
            "2v_1eDD": Graph2Vertices1EdgeByDragDrop,
            "2v_1e_1d": Graph2Vertices1Edge1Decoration,
            "2v_1e_1d_1t": Graph2Vertices1Edge1Decoration1Table,
            "1t": Graph1Table,
            "3v_3e": Graph3Vertices3EdgesByCode,
        }

    def __call__(self, case_name):
        """
        :param str case_name: Name of of available cases.
        :rtype: BaseGraphCase
        :return: Case with a graph already drawn.
        """
        case_type = self.case_map[case_name]
        return case_type(selenium=self._selenium, host=self._host)


class BaseGraphCase(object):
    def __init__(self, selenium, host):
        import qmxgraph.js

        self._selenium = selenium
        self._host = host
        _wait_graph_page_ready(host=host, selenium=selenium)

        selenium.execute_script(
            'callback = function(cellIds) {'
            '    if (!window.__added__) {'
            '        window.__added__ = [];'
            '    }'
            '    window.__added__.push.apply(window.__added__, cellIds);'
            '}'
        )
        self.eval_js_function('api.registerCellsAddedHandler', qmxgraph.js.Variable('callback'))

        selenium.execute_script(
            'callback = function(cellId, newLabel, oldLabel) {'
            '    if (!window.__labels__) {'
            '        window.__labels__ = [];'
            '    }'
            '    window.__labels__.push({cellId: cellId, newLabel: newLabel, oldLabel: oldLabel});'  # noqa
            '}'
        )
        self.eval_js_function('api.registerLabelChangedHandler', qmxgraph.js.Variable('callback'))

    def get_container(self):
        """
        :rtype: selenium.webdriver.remote.webelement.WebElement
        :return: DIV element containing graph drawing widget.
        """
        return self.selenium.find_element_by_id('graphContainer')

    def get_container_size(self):
        """
        :rtype: tuple[int, int]
        :return: Width and height in pixels of graph drawing widget container
            element, respectively.
        """
        container = self.get_container()
        return container.size['width'], container.size['height']

    def get_vertex_position(self, vertex):
        """
        :param selenium.webdriver.remote.webelement.WebElement vertex:
            Graphical representation of vertex.
        :rtype: tuple[float, float]
        :return: Left/X and top/Y screen coordinates of vertex, respectively.
        """
        return float(vertex.get_attribute('x')), float(vertex.get_attribute('y'))

    def get_vertex_size(self, vertex):
        """
        :param selenium.webdriver.remote.webelement.WebElement vertex:
            Graphical representation of vertex.
        :rtype: tuple[int, int]
        :return: Width and height in pixels of vertex, respectively.
        """
        return int(vertex.get_attribute('width')), int(vertex.get_attribute('height'))

    def get_edge(self, source, target):
        """
        :param selenium.webdriver.remote.webelement.WebElement source:
            Graphical representation of vertex that is source of edge.
        :param selenium.webdriver.remote.webelement.WebElement target:
            Graphical representation of vertex that is target of edge.
        :rtype: selenium.webdriver.remote.webelement.WebElement|None
        :return: Graphical element representing edge between vertices,
            if found, otherwise None.
        """
        # An edge is represented by a SVG path, it is created from
        # right side of 'foo' vertex until it connects with 'bar'.
        def get(v, attr):
            return int(v.get_attribute(attr))

        from selenium.common.exceptions import StaleElementReferenceException

        try:
            if get(source, 'x') < get(target, 'x'):
                h_right = get(source, 'x') + get(source, 'width')
                v_center = get(source, 'y') + get(source, 'height') // 2
            else:
                h_right = get(target, 'x') + get(target, 'width')
                v_center = get(target, 'y') + get(target, 'height') // 2
        except StaleElementReferenceException:
            # If any of vertices is not longer in page, edge is also removed
            return None

        color = self.selenium.execute_script(
            "return graphEditor.graph.getStylesheet().getDefaultEdgeStyle()[mxConstants.STYLE_STROKECOLOR]"  # noqa
        )
        color = color.lower()

        edge = self.selenium.find_elements_by_css_selector(
            'path[stroke="{}"][d~="M"][d~="{}"][d~="{}"]'.format(color, h_right, v_center)
        )
        assert len(edge) <= 1
        return edge[0] if len(edge) == 1 else None

    def get_label_element(self, cell):
        """
        :param selenium.webdriver.remote.webelement.WebElement cell: Graphical
            representation of cell.
        :rtype: selenium.webdriver.remote.webelement.WebElement
        :return: Graphical element of cell's label.
        """
        # Go back from rect and g referent to cell to shared parent. Label of
        # vertices aren't child to cell drawing node in SVG of mxGraph, they
        # actually share a same parent node which contains both cell drawing
        # and text at a same level.
        common = cell.find_element_by_xpath('../..')
        if self.selenium.execute_script('return graphEditor.graph.isHtmlLabel()'):
            # If HTML labels are enabled, label is a bit more complicated...
            g = common.find_element_by_css_selector('g[style]>g[transform]')
            label = g.find_element_by_tag_name('div')
            label = label.find_element_by_tag_name('div')
        else:
            label = common.find_element_by_css_selector('g>g>text')
        return label

    def get_edge_position(self, edge):
        """
        :param selenium.webdriver.remote.webelement.WebElement edge: Graphical
            representation of edge.
        :rtype: tuple[int, int]
        :return: X and Y screen coordinates of start of path of edge,
            respectively.
        """
        import re

        edge_coords = re.search(r'M (\d+) (\d+)', edge.get_attribute('d'))
        return int(edge_coords.group(1)), int(edge_coords.group(2))

    def get_id(self, cell):
        """
        :param selenium.webdriver.remote.webelement.WebElement cell: Graphical
            representation of an edge or node.
        :rtype: str
        :return: Id of cell.
        """
        # To be safe, use tolerance when looking for cells, as especially when
        # searching edges (whose end points overlap with vertices) there is
        # otherwise a chance connected vertices will be found instead.
        #
        # The sensibility in search varies from one web driver to other.
        # PhantomJS seems to deal better with overlaps in lower bound (i.e.
        # without tolerance) and Firefox deals better with upper bound, for
        # instance. As a compromise, half of tolerance seemed empirically ok
        # so far.
        tolerance = self.selenium.execute_script("return graphEditor.graph.tolerance") / 2.0

        id_ = self.eval_js_function(
            'api.getCellIdAt', cell.location['x'] + tolerance, cell.location['y'] + tolerance
        )
        return id_

    def get_type_at(self, x, y):
        """
        :param int x: X in screen coordinates.
        :param int y: Y in screen coordinates.
        :rtype: str
        :return: Cell type at position. See `QmxGraphApi.getCellTypeAt` for
            details about possible types.
        """
        return self.eval_js_function('api.getCellTypeAt', x, y)

    def get_geometry(self, cell):
        """
        :param selenium.webdriver.remote.webelement.WebElement|str cell:
            Graphical element of a cell or its id.
        :rtype: list[int, int, int, int]
        :return: List composed, respectively, by x, y, width and height.
        """
        return self.eval_js_function('api.getGeometry', self._as_cell_id(cell))

    def get_label(self, cell):
        """
        :param selenium.webdriver.remote.webelement.WebElement|str cell:
            Graphical element of a cell or its id.
        :rtype: str
        :return: Label of cell.
        """
        return self.eval_js_function('api.getLabel', self._as_cell_id(cell))

    def set_visible(self, cell, visible):
        """
        :param selenium.webdriver.remote.webelement.WebElement|str cell:
            Graphical element of a cell or its id.
        :param bool visible: New visibility state.
        """
        self.eval_js_function('api.setVisible', self._as_cell_id(cell), visible)

    def is_visible(self, cell):
        """
        :param selenium.webdriver.remote.webelement.WebElement|str cell:
            Graphical element of a cell or its id.
        """
        return self.eval_js_function('api.isVisible', self._as_cell_id(cell))

    def get_table_title(self, table):
        """
        :param selenium.webdriver.remote.webelement.WebElement table: Graphical
            element of table cell.
        :rtype: str
        :return: Table title.
        """
        title = table.find_element_by_css_selector('table.table-cell-title')
        return title.find_element_by_tag_name('tr').text

    def get_table_contents(self, table):
        """
        :param selenium.webdriver.remote.webelement.WebElement table: Graphical
            element of table cell.
        :rtype: str
        :return: Table contents.
        """
        contents = table.find_element_by_css_selector('table.table-cell-contents')
        return [i.text for i in contents.find_elements_by_tag_name('td')]

    def select_vertex(self, vertex):
        """
        :param selenium.webdriver.remote.webelement.WebElement vertex:
            Graphical representation of vertex.
        """
        from selenium.webdriver import ActionChains

        actions = ActionChains(self.selenium)
        # Clicking on vertex can be hard... It has several elements that
        # overlay over it, such as tooltips, that may cause selenium to fail
        # because of element mismatch. This is an attempt to click in the
        # bottom right part of vertex that *usually* doesn't seem to have
        # anything over it.
        actions.move_to_element_with_offset(
            vertex, int(vertex.get_attribute('width')) - 5, int(vertex.get_attribute('height')) - 5
        )
        actions.click()
        actions.perform()

    def select_edge(self, edge):
        """
        :param selenium.webdriver.remote.webelement.WebElement edge: Graphical
            representation of edge.
        """
        from selenium.webdriver import ActionChains

        actions = ActionChains(self.selenium)
        actions.click(edge)
        actions.perform()

    def get_added_cell_ids(self):
        """
        :rtype: list[str]
        :return: Id of every cell added to graph, captured by using
            `registerCellsAddedHandler` event.
        """
        return self.selenium.execute_script('return window.__added__')

    def get_label_changes(self):
        """
        :rtype: list[dict]
        :return: Event object of every time a cell was renamed in graph,
            captured by using `onLabelChanged` event.
        """
        return self.selenium.execute_script('return window.__labels__')

    def insert_vertex(self, x=10, y=10, width=25, height=25, label='label', style=None, tags=None):
        """
        Inserts a vertex with sensible, empirical defaults.

        ..see:: Refer to `insertVertex` in API for argument details.
        :rtype: str
        :return: New vertex id.
        """
        return self.eval_js_function("api.insertVertex", x, y, width, height, label, style, tags)

    def insert_table(self, x=20, y=60, width=100, contents=None, title='Hitchhikers', tags=None):
        """
        Inserts a table with sensible, empirical defaults.

        ..see:: Refer to `insertTable` in API.JS for argument details.
        :rtype: str
        :return: New table id.
        """

        if contents is None:
            contents = {  # graphs.utils.TableRowDescription
                'contents': [
                    # graphs.utils.TableDataDescription
                    {'contents': ['arthur', 'dent']},
                    # graphs.utils.TableDataDescription
                    {'contents': ['ford', 'prefect']},
                ]
            }
        return self.eval_js_function('api.insertTable', x, y, width, contents, title, tags)

    def insert_decoration(
        self, x, y, width=10, height=10, style=None, label='decoration', tags=None
    ):
        """
        Inserts a decoration with sensible, empirical defaults for most
        arguments. Since it needs to be placed over an edge position arguments
        still need to be provided.

        ..see:: Refer to `insertDecoration` in API for argument details.
        :rtype: str
        :return: New decoration id.
        """
        return self.eval_js_function(
            'api.insertDecoration', x, y, width, height, label, style, tags
        )

    def insert_edge_by_drag_drop(self, source, target):
        """
        Inserts an edge by dragging & dropping source over target.

        :param selenium.webdriver.remote.webelement.WebElement source:
            Graphical element of source vertex.
        :param selenium.webdriver.remote.webelement.WebElement target:
            Graphical element of target vertex.
        """
        from selenium.webdriver import ActionChains

        actions = ActionChains(self.selenium)
        actions.drag_and_drop(source, target)
        actions.perform()

    def insert_edge(self, source, target, label='', style=None, tags=None):
        """
        Inserts an edge programatically.

        :param selenium.webdriver.remote.webelement.WebElement|str source:
            Graphical element of source vertex or its id.
        :param selenium.webdriver.remote.webelement.WebElement|str target:
            Graphical element of target vertex or its id.
        :param str label: Label of edge.
        :rtype: str
        :return: Id of added edge.
        ..see: `api.insertEdge` for other arguments.
        """
        return self.eval_js_function(
            "api.insertEdge", self._as_cell_id(source), self._as_cell_id(target), label, style, tags
        )

    def get_vertices(self):
        """
        :rtype: list[selenium.webdriver.remote.webelement.WebElement]
        :return: All vertices found in graph. Be aware it assumes vertices
            only in default style.
        """
        color = self.selenium.execute_script(
            "return graphEditor.graph.getStylesheet().getDefaultVertexStyle()[mxConstants.STYLE_FILLCOLOR]"  # noqa
        )
        color = color.lower()
        vertices = self.selenium.find_elements_by_css_selector('g>g>rect[fill="{}"]'.format(color))
        return vertices

    def remove_cells(self, *cell_ids):
        """
        :param iterable[str] cell_ids: Id of cells to be removed.
        """
        return self.eval_js_function('api.removeCells', list(cell_ids))

    def eval_js_function(self, fn, *args):
        """
        :param str fn: A function expression in JavaScript.
        :param tuple args: Positional arguments passed to JavaScript function.
        :rtype: object
        :return: Return obtained by evaluation of given function.
        """
        import qmxgraph.js

        # Unlike Qt JS evaluation, Selenium doesn't include return by default,
        # it is necessary to include it in statement.
        return self.selenium.execute_script(
            'return {}'.format(qmxgraph.js.prepare_js_call(fn, *args))
        )

    def _as_cell_id(self, cell):
        """
        :param selenium.webdriver.remote.webelement.WebElement|str cell:
            Graphical element of a cell or its id.
        :rtype: str
        :return: Id of cell.
        """
        if not isinstance(cell, str):
            cell = self.get_id(cell)
        return cell

    @property
    def selenium(self):
        """
        :rtype: selenium.webdriver.remote.webdriver.WebDriver
        """
        return self._selenium

    @property
    def host(self):
        """
        :rtype: qmxgraph.server.Host
        """
        return self._host


class Graph1Vertex(BaseGraphCase):
    def __init__(self, selenium, host):
        BaseGraphCase.__init__(self, selenium, host)

        # Insert without style results in a rectangle in SVG drawn by mxGraph
        selenium.execute_script("api.insertVertex(10, 10, 25, 25, 'label', null)")

        vertex = self.get_vertex()
        assert vertex.get_attribute('x') == '10'
        assert vertex.get_attribute('y') == '10'
        assert vertex.get_attribute('width') == '25'
        assert vertex.get_attribute('height') == '25'
        assert self.get_label_element(vertex).text == 'label'

    def get_vertex(self):
        color = self.selenium.execute_script(
            "return graphEditor.graph.getStylesheet().getDefaultVertexStyle()[mxConstants.STYLE_FILLCOLOR]"  # noqa
        )
        color = color.lower()

        # The vertex basically is composed of two parts:
        # * A <rect> tag drawn in SVG (which is a grandchild of two consecutive
        #  <g> tags);
        # * A <text> tag with its label in SVG (which is a grandchild of two
        # consecutive <g> tags)
        rect = self.selenium.find_elements_by_css_selector('g>g>rect[fill="{}"]'.format(color))
        assert len(rect) <= 1
        return rect[0] if rect else None


class Graph1Vertex1Port(Graph1Vertex):
    def __init__(self, selenium, host):
        Graph1Vertex.__init__(self, selenium, host)
        vertex_id = self.get_id(self.get_vertex())
        self.port_color = '#987654'
        selenium.execute_script(
            f"api.insertPort("
            f"  {vertex_id}, 'foo',"
            f"  0, 0, 5, 5,"
            f"  '', 'shape=ellipse;fillColor={self.port_color}', null)"
        )

    def get_port(self):
        port_elements = self.selenium.find_elements_by_css_selector(
            f'g>g>ellipse[fill="{self.port_color}"]'
        )
        assert len(port_elements) <= 1
        return port_elements[0] if port_elements else None


class Graph1VertexWithStyle(BaseGraphCase):
    def __init__(self, selenium, host):
        BaseGraphCase.__init__(self, selenium, host)

        # Insert without style results in a rectangle in SVG drawn by mxGraph
        selenium.execute_script("api.insertVertex(10, 10, 25, 25, 'yellow', 'yellow')")

        vertex = self.get_vertex()
        assert vertex.get_attribute('x') == '10'
        assert vertex.get_attribute('y') == '10'
        assert vertex.get_attribute('width') == '25'
        assert vertex.get_attribute('height') == '25'
        assert self.get_label_element(vertex).text == 'yellow'

    def get_vertex(self):
        color = self.host.styles['yellow']['fill_color']

        # The vertex basically is composed of two parts:
        # * A <rect> tag drawn in SVG (which is a grandchild of two consecutive
        #  <g> tags);
        # * A <text> tag with its label in SVG (which is a grandchild of two
        # consecutive <g> tags)
        rect = self.selenium.find_elements_by_css_selector('g>g>rect[fill="{}"]'.format(color))
        assert len(rect) <= 1
        return rect[0] if rect else None


class Graph2Vertices(BaseGraphCase):
    def __init__(self, selenium, host):
        BaseGraphCase.__init__(self, selenium, host)

        self.vertex1_id = self.insert_vertex(10, 10, 30, 30, 'foo', None)
        self.vertex2_id = self.insert_vertex(90, 10, 30, 30, 'bar', None)


class Graph2Vertices1EdgeByCode(Graph2Vertices):
    def __init__(self, selenium, host):
        Graph2Vertices.__init__(self, selenium, host)

        self.source_id = self.vertex1_id
        self.target_id = self.vertex2_id
        self.edge_id = self.insert_edge(self.source_id, self.target_id, 'edge')


class Graph3Vertices1EdgeByCode(Graph2Vertices1EdgeByCode):
    def __init__(self, selenium, host):
        Graph2Vertices1EdgeByCode.__init__(self, selenium, host)

        self.vertex3_id = self.insert_vertex(10, 90, 30, 30, 'fuz', None)


class Graph3Vertices3EdgesByCode(BaseGraphCase):
    def __init__(self, selenium, host):
        BaseGraphCase.__init__(self, selenium, host)

        self.vertex1_id = self.insert_vertex(0, 0, 1, 1, label='foo')
        self.vertex2_id = self.insert_vertex(100, 0, 1, 1, label='bar')
        self.vertex3_id = self.insert_vertex(200, 0, 1, 1, label='fuz')

        self.edge1_id = self.insert_edge(self.vertex1_id, self.vertex2_id, 'edge1')
        self.edge2_id = self.insert_edge(self.vertex1_id, self.vertex3_id, 'edge2')
        self.edge3_id = self.insert_edge(self.vertex2_id, self.vertex3_id, 'edge3')


class Graph2Vertices1EdgeByDragDrop(Graph2Vertices):
    def __init__(self, selenium, host):
        Graph2Vertices.__init__(self, selenium, host)

        vertex_foo, vertex_bar = self.get_vertices()
        self.insert_edge_by_drag_drop(vertex_foo, vertex_bar)


class Graph2Vertices1Edge1Decoration(Graph2Vertices1EdgeByCode):
    def __init__(self, selenium, host):
        Graph2Vertices1EdgeByCode.__init__(self, selenium, host)

        vertices_width = 30
        vertices_top_border = 10
        source_left_border = 10
        source_right_border = source_left_border + vertices_width
        target_left_border = 90
        edge_length = target_left_border - source_right_border

        # Decorations must be placed over an edge to work. They are drawn
        # centered at the point given over edge.
        x = source_right_border + edge_length * 0.4  # 0.4 along edge.
        y = vertices_top_border + vertices_width / 2  # edge's y coordinate.
        w = 10
        h = 10
        style = 'purple'
        label = 'decoration'
        self.eval_js_function('api.insertDecoration', x, y, w, h, label, style)

        decoration = self.get_decorations()[0]
        assert int(decoration.get_attribute("x")) == x - (w // 2)
        assert int(decoration.get_attribute("y")) == y - (h // 2)
        assert int(decoration.get_attribute("width")) == w
        assert int(decoration.get_attribute("height")) == h

    def get_decorations(self):
        style = 'purple'
        selector = 'g>g>rect[fill="{}"]'.format(self.host.styles[style]['fill_color'])
        decoration = self.selenium.find_elements_by_css_selector(selector)
        return decoration


class Graph2Vertices1Edge1Decoration1Table(Graph2Vertices1Edge1Decoration):
    def __init__(self, selenium, host):
        Graph2Vertices1Edge1Decoration.__init__(self, selenium, host)

        x = 20
        y = 60
        w = 100
        contents = {  # graphs.utils.TableDescription
            'contents': [
                # graphs.utils.TableDataDescription
                {'contents': ['arthur', 'dent']},
                # graphs.utils.TableDataDescription
                {'contents': ['ford', 'prefect']},
            ]
        }
        title = 'Hitchhikers'
        self.table_id = self.eval_js_function('api.insertTable', x, y, w, contents, title)

        assert self.get_table_title(self.get_tables()[0]) == 'Hitchhikers'
        assert self.get_table_contents(self.get_tables()[0]) == [
            'arthur',
            'dent',
            'ford',
            'prefect',
        ]

    def get_tables(self):
        titles = self.selenium.find_elements_by_css_selector('div>table.table-cell-title')
        return [web_el.find_element_by_xpath('../..') for web_el in titles]


class Graph1Table(BaseGraphCase):
    def __init__(self, selenium, host):
        BaseGraphCase.__init__(self, selenium, host)

        x = 20
        y = 60
        w = 100
        contents = {  # graphs.utils.TableDescription
            'contents': [
                # graphs.utils.TableDataDescription
                {'contents': ['arthur', 'dent']},
                # graphs.utils.TableDataDescription
                {'contents': ['ford', 'prefect']},
            ]
        }
        title = 'Hitchhikers'
        self.eval_js_function('api.insertTable', x, y, w, contents, title)

        assert self.get_table_title(self.get_tables()[0]) == 'Hitchhikers'
        assert self.get_table_contents(self.get_tables()[0]) == [
            'arthur',
            'dent',
            'ford',
            'prefect',
        ]

    def get_tables(self):
        titles = self.selenium.find_elements_by_css_selector('div>table.table-cell-title')
        return [web_el.find_element_by_xpath('../..') for web_el in titles]


def _wait_graph_page_ready(host, selenium):
    """
    Wait until graph page is ready to use, raise if timeout expires.

    :type host: qmxgraph.host_graph.Host
    :type selenium: selenium.webdriver.remote.webdriver.WebDriver
    """
    import socket
    from selenium.common.exceptions import TimeoutException

    timeout = 15
    timeout_exceptions = (TimeoutException, TimeoutError, socket.timeout)
    selenium.set_page_load_timeout(1)
    refresh = True
    try:
        selenium.get(host.address)
        refresh = False
    except timeout_exceptions:
        pass

    if refresh:
        for n in range(timeout):
            try:
                selenium.refresh()
                break
            except timeout_exceptions:
                pass
        else:
            raise TimeoutException("All page load tries resulted in timeout")

    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    try:
        WebDriverWait(selenium, timeout=timeout).until(
            EC.presence_of_element_located((By.ID, "graphContainer"))
        )
    except timeout_exceptions as e:
        raise TimeoutException(
            "Graph page wasn't ready in address {} after a timeout of {}"
            " seconds".format(host.address, timeout)
        ) from e

    for n in range(timeout):
        has_api = selenium.execute_script('return !!window.api')
        if has_api:
            break
        else:
            import time

            time.sleep(0.1)
    else:
        msg = "The page is reported to be loaded in {} but 'api' is not found"
        raise TimeoutException(msg.format(host.address))


def _get_port_lock_filename(rootdir):
    return '{}/.port.lock'.format(rootdir)
