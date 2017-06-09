import math
import sys

import pytest
from selenium.common.exceptions import NoSuchElementException, \
    WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

import qmxgraph.constants
from qmxgraph import constants, js, server
from qmxgraph.configuration import GraphOptions, GraphStyles


def test_resize_container(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('empty')

    width, height = graph.get_container_size()
    new_width = width + 20
    new_height = height + 20
    graph.selenium.execute_script(
        "api.resizeContainer({}, {})".format(new_width, new_height))

    width, height = graph.get_container_size()
    assert width == new_width
    assert height == new_height


def test_insert_vertex(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v')
    assert graph.get_vertex() is not None


@pytest.mark.parametrize('dumped,restored', [('1v', '2v'), ('2v', '1v')])
def test_dump_restore(dumped, restored, graph_cases):
    """
    :type dumped: str
    :type restored: str
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases(dumped)
    dumped_vertices_count = len(graph.get_vertices())
    dump = graph.eval_js_function('api.dump')
    del graph
    graph = graph_cases(restored)
    assert dumped_vertices_count != len(graph.get_vertices())
    graph.eval_js_function('api.restore', dump)
    assert dumped_vertices_count == len(graph.get_vertices())


def test_insert_vertex_with_style(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v_style')
    vertex = graph.get_vertex()

    # Can't have same color as default vertex style
    default = graph.selenium.execute_script(
        "return graphEditor.graph.getStylesheet().getDefaultVertexStyle()[mxConstants.STYLE_FILLCOLOR]"  # noqa
    )
    default = default.lower()

    assert vertex.get_attribute('fill') != default


def test_insert_vertex_close_to_boundaries(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('empty')

    width, height = graph.get_container_size()

    assert graph.eval_js_function(
        "api.insertVertex", width - 10, height - 10, 25, 25, 'label')

    assert graph.get_container_size() == (width + 16, height + 16)


@pytest.mark.parametrize(
    'mode',
    [
        'by_code',
        'by_drag_drop',
    ],
)
def test_insert_edge(graph_cases, mode):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    if mode == 'by_code':
        case = '2v_1e'
    else:
        assert mode == 'by_drag_drop'
        case = '2v_1eDD'
    graph = graph_cases(case)
    assert graph.get_edge(*graph.get_vertices()) is not None


def test_insert_edge_error_endpoint_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('1v')
    vertex = graph.get_vertices()[0]

    invalid_source_id = invalid_target_id = "999"

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function(
            "api.insertEdge", invalid_source_id, graph.get_id(vertex))

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(invalid_source_id)

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function(
            "api.insertEdge", graph.get_id(vertex), invalid_target_id)

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(invalid_target_id)


def test_insert_decoration(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d')
    assert graph.get_decoration() is not None


def test_decoration_position(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d')
    cell_id = graph.get_id(graph.get_decoration())

    position = graph.eval_js_function('api.getDecorationPosition', cell_id)
    assert position == 0.4

    graph.eval_js_function('api.setDecorationPosition', cell_id, 0.8)
    position = graph.eval_js_function('api.getDecorationPosition', cell_id)
    assert position == 0.8


def test_get_decoration_parent_cell_id(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d')
    cell_id = graph.get_id(graph.get_decoration())
    parent_id = graph.eval_js_function('api.getDecorationParentCellId', cell_id)
    assert parent_id == '4'


def test_delete_vertex(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v')
    graph.select_vertex(graph.get_vertex())

    actions = ActionChains(graph.selenium)
    actions.key_down(Keys.DELETE)
    actions.key_up(Keys.DELETE)
    actions.perform()

    assert not graph.get_vertex()


def test_delete_edge(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e')
    graph.select_edge(graph.get_edge(*graph.get_vertices()))

    actions = ActionChains(graph.selenium)
    actions.key_down(Keys.DELETE)
    actions.key_up(Keys.DELETE)
    actions.perform()

    assert not graph.get_edge(*graph.get_vertices())


def test_group(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v')

    actions = ActionChains(graph.selenium)
    actions.key_down(Keys.CONTROL)
    actions.perform()

    vertex_foo, vertex_bar = graph.get_vertices()
    graph.select_vertex(vertex_foo)
    graph.select_vertex(vertex_bar)

    actions = ActionChains(graph.selenium)
    actions.key_up(Keys.CONTROL)
    actions.perform()

    # Group selected vertices
    graph.selenium.execute_script("api.group()")

    group_fill = graph.host.styles['group']['fill_color']
    group_selector = 'g>g>rect[fill="{}"]'.format(group_fill)
    group = graph.selenium.find_elements_by_css_selector(group_selector)
    assert len(group) == 1

    # Ungroup selected vertices
    graph.selenium.execute_script("api.ungroup()")
    group = graph.selenium.find_elements_by_css_selector(group_selector)
    assert not group


def test_toggle_outline(selenium, host, wait_graph_page_ready):
    """
    :type selenium: selenium.webdriver.remote.webdriver.WebDriver
    :type host: qmxgraph.server.Host
    """
    wait_graph_page_ready(host=host)

    # By default, outline starts hidden. Basically this means mxGraph's window
    # component used to shown outline doesn't exist yet.
    with pytest.raises(NoSuchElementException):
        selenium.find_element_by_css_selector('div.mxWindow')

    # Once shown, outline is displayed in a mxGraph's window component
    selenium.execute_script("api.toggleOutline()")
    outline = selenium.find_element_by_css_selector('div.mxWindow')
    assert outline is not None

    # However once toggled back to hidden, it is not destroyed but simply
    # hidden
    selenium.execute_script("api.toggleOutline()")
    assert not outline.is_displayed()


@pytest.mark.parametrize('grid', [True, False])
def test_toggle_grid(selenium, host, grid, wait_graph_page_ready):
    """
    :type selenium: selenium.webdriver.remote.webdriver.WebDriver
    :type host: qmxgraph.server.Host
    """
    wait_graph_page_ready(host=host)

    # By default, grid starts visible. To hide grid, a class is
    # added to graph container div.
    if not grid:
        selenium.execute_script("api.toggleGrid()")

    container = selenium.find_element_by_css_selector('div.graph')
    assert container.get_attribute('id') == 'graphContainer'
    assert container.get_attribute('class') == \
        'graph' if grid else 'graph hide-bg'


@pytest.mark.parametrize('snap', [True, False])
def test_toggle_snap(graph_cases, snap):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v')
    selenium = graph.selenium

    # If snap is enabled, it should move to closest grid block (which are
    # always multiples of 10, as 10 is grid size). By default snap is enabled.
    if not snap:
        selenium.execute_script("api.toggleSnap()")

    vertex = graph.get_vertex()
    x, y = graph.get_vertex_position(vertex)
    w, h = graph.get_vertex_size(vertex)

    actions = ActionChains(selenium)
    actions.move_to_element(vertex)
    actions.move_by_offset(w / 2., h / 2.)
    actions.drag_and_drop_by_offset(None, 66, 66)
    actions.perform()

    vertex = graph.get_vertex()

    def expected(v):
        result = v + 66
        if snap:
            result = math.ceil(result / 10.) * 10
        return result

    assert int(vertex.get_attribute('width')) == w
    assert int(vertex.get_attribute('height')) == h
    assert int(vertex.get_attribute('x')) == expected(x)
    assert int(vertex.get_attribute('y')) == expected(y)


def test_get_cell_id_at(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d_1t')

    # mxGraph shares a global id counter for all cell types. The first
    # non-reserved id is 2, as lower values are used by internal control
    # structures.
    assert graph.get_id(graph.get_vertices()[0]) == '2'
    assert graph.get_id(graph.get_vertices()[1]) == '3'
    assert graph.get_id(graph.get_edge(*graph.get_vertices())) == '4'
    assert graph.get_id(graph.get_decoration()) == '5'
    assert graph.get_id(graph.get_tables()[0]) == '6'

    class Invalid:
        def __init__(self):
            self.location = {'x': 999, 'y': 999}
    assert graph.get_id(Invalid()) is None


def test_set_visible(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d_1t')

    # Hide then show vertex again
    vertices = graph.get_vertices()
    cell_id = graph.get_id(vertices[0])
    graph.set_visible(cell_id, False)
    assert not graph.is_visible(cell_id)
    assert len(graph.get_vertices()) == len(vertices) - 1
    graph.set_visible(cell_id, True)
    assert graph.is_visible(cell_id)
    assert len(graph.get_vertices()) == len(vertices)

    # hide then show edge again
    cell_id = graph.get_id(graph.get_edge(*graph.get_vertices()))
    graph.set_visible(cell_id, False)
    assert graph.get_edge(*graph.get_vertices()) is None
    graph.set_visible(cell_id, True)
    assert graph.get_edge(*graph.get_vertices()) is not None

    # Hide then show decoration again
    cell_id = graph.get_id(graph.get_decoration())
    graph.set_visible(cell_id, False)
    assert graph.get_decoration() is None
    graph.set_visible(cell_id, True)
    assert graph.get_decoration() is not None

    # Hide then show table again
    cell_id = graph.get_id(graph.get_tables()[0])
    graph.set_visible(cell_id, False)
    assert len(graph.get_tables()) == 0
    graph.set_visible(cell_id, True)
    assert len(graph.get_tables()) == 1


def test_set_visible_error_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('2v_1e_1d_1t')
    cell_id = '999'

    with pytest.raises(WebDriverException) as e:
        graph.set_visible(cell_id, False)

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)

    with pytest.raises(WebDriverException) as e:
        graph.is_visible(cell_id)

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)


def test_get_geometry(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d_1t')

    assert graph.get_geometry(graph.get_vertices()[0]) == [10, 10, 30, 30]
    assert graph.get_geometry(graph.get_edge(*graph.get_vertices())) == \
        [40, 25, 50, 1]
    assert graph.get_geometry(graph.get_decoration()) == [55, 20, 10, 10]
    table_w, table_h = fix_table_size(110, 80)
    assert graph.get_geometry(graph.get_tables()[0]) == [20, 60, table_w, table_h]


def test_get_geometry_error_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('2v_1e_1d_1t')

    cell_id = "999"
    with pytest.raises(WebDriverException) as e:
        graph.get_geometry(cell_id)

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)


def test_insert_table(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1t')
    assert len(graph.get_tables()) == 1


def test_insert_child_table(graph_cases):
    """
    When supplying `parent_id` the origin (the x and y coordinates) are
    normalized and relative to the parent bounds. Here is used another table
    as parent but any cell is eligible.

    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1t')

    tables = graph.get_tables()
    assert len(tables) == 1
    parent_id = graph.get_id(tables[0])
    child_id = graph.eval_js_function(
        'api.insertTable', 0.5, 1.5, 300, {'contents': []}, 'foobar', None,
        None, parent_id)
    tables = graph.get_tables()
    assert len(tables) == 2

    def get_bounds(cell_id):
        return graph.eval_js_function('api.getGeometry', cell_id)
    parent_bounds = get_bounds(parent_id)
    child_bounds = get_bounds(child_id)
    assert parent_bounds[0] < child_bounds[0] < parent_bounds[2]
    assert parent_bounds[3] < child_bounds[1]


def test_table_with_image(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1t')

    tables = graph.get_tables()
    assert len(tables) == 1
    table_id = graph.get_id(tables[0])
    contents = {  # graphs.utils.TableRowDescription
        'contents': [
            {  # graphs.utils.TableDataDescription
                'contents': [
                    {  # graphs.utils.TableDataDescription
                        'contents': [
                            'foo ',
                            {
                                'tag': 'img', 'src': 'some-image-path',
                                'width': 16, 'height': 16,
                            },
                        ]
                    }
                ]
            }
        ]
    }
    graph.eval_js_function('api.updateTable', table_id, contents, '')

    image_elements = graph.selenium.find_elements_by_css_selector(
        '.table-cell-contents img')
    assert len(image_elements) == 1
    image = image_elements[0]
    assert image.get_attribute('src').endswith('some-image-path')


def test_insert_table_close_to_boundaries(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('empty')

    width, height = graph.get_container_size()

    contents = {  # graphs.utils.TableDescription
        'contents': [
            # graphs.utils.TableRowDescription's
            {'contents': ['alpha', '100']},
            {'contents': ['beta', '200']},
            {'contents': ['gamma', '300']},
        ]
    }
    assert graph.eval_js_function(
        "api.insertTable", width - 10, height - 10, 0, contents, 'title')

    assert graph.get_container_size() == \
        fix_table_size(width + 81, height + 91)


def test_update_table(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1t')

    table_id = graph.get_id(graph.get_tables()[0])
    contents = {  # graphs.utils.TableDescription
        'contents': [
            # graphs.utils.TableRowDescription's
            {'contents': ['a', 1]},
            {'contents': ['b', 2]},
        ]
    }
    title = 'updated'
    graph.selenium.execute_script(
        js.prepare_js_call('api.updateTable', table_id, contents, title))

    table = graph.get_tables()[0]
    assert graph.get_table_title(table) == 'updated'
    assert graph.get_table_contents(table) == ['a', '1', 'b', '2']


def test_update_table_error_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('1t')

    table_id = "999"
    contents = []
    title = 'will not matter'

    with pytest.raises(WebDriverException) as e:
        graph.selenium.execute_script(
            js.prepare_js_call('api.updateTable', table_id, contents, title))

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(table_id)


def test_update_table_error_not_table(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('2v_1e_1d_1t')

    table_id = graph.get_id(graph.get_edge(*graph.get_vertices()))
    contents = []
    title = 'will not matter'

    with pytest.raises(WebDriverException) as e:
        graph.selenium.execute_script(
            js.prepare_js_call('api.updateTable', table_id, contents, title))

    assert selenium_extras.get_exception_message(e) == "Cell is not a table"


def test_remove_cells(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e')

    vertices = graph.get_vertices()
    cell_ids = [
        graph.get_id(vertices[0]),
        graph.get_id(graph.get_edge(*vertices)),
    ]
    graph.eval_js_function('api.removeCells', cell_ids)

    assert len(graph.get_vertices()) == 1
    assert graph.get_edge(*vertices) is None


def test_remove_cells_error_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('empty')

    cell_id = 999
    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function('api.removeCells', [cell_id])

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)


def test_on_cells_removed(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e')

    graph.selenium.execute_script(
        'callback = function(cellIds) {window.cellIds = cellIds;}')
    graph.eval_js_function('api.onCellsRemoved', js.Variable('callback'))

    cell_ids = [
        graph.get_id(graph.get_vertices()[0]),
        graph.get_id(graph.get_edge(*graph.get_vertices())),
    ]
    graph.eval_js_function('api.removeCells', cell_ids)

    assert graph.selenium.execute_script('return window.cellIds') == cell_ids


def test_custom_shapes(selenium, port, tmpdir, wait_graph_page_ready):
    """
    :type selenium: selenium.webdriver.remote.webdriver.WebDriver
    :type port: qmxgraph.tests.conftest.Port
    """
    # Shape found in by https://www.draw.io/stencils/basic.xml
    custom_stencil = '''\
<shapes>
    <shape name="Moon" h="103.05" w="77.05" aspect="variable" strokewidth="inherit">
        <connections>
            <constraint x="0.48" y="0" perimeter="0" name="N"/>
            <constraint x="1" y="0.89" perimeter="0" name="SE"/>
        </connections>
        <background>
            <path>
                <move x="37.05" y="0"/>
                    <arc rx="48" ry="48" x-axis-rotation="0" large-arc-flag="1" sweep-flag="0" x="77.05" y="92"/>
                    <arc rx="60" ry="60" x-axis-rotation="0" large-arc-flag="0" sweep-flag="1" x="37.05" y="0"/>
                <close/>
            </path>
        </background>
        <foreground>
            <fillstroke/>
        </foreground>
    </shape>
</shapes>'''  # noqa

    stencil_file = tmpdir.mkdir("stencils").join("custom.xml")
    stencil_file.write(custom_stencil)
    stencils = [str(stencil_file)]

    styles = GraphStyles({
        'moon': {
            'shape': 'Moon',
            'fill_color': '#ffff00',
        },
    })

    def has_custom_shape():
        return bool(selenium.find_elements_by_css_selector(
            'g>g>path[fill="#ffff00"]'))

    with server.host(
            port=port.get(), styles=styles, stencils=stencils) as host:
        wait_graph_page_ready(host=host)
        assert not has_custom_shape()
        selenium.execute_script(
            "api.insertVertex(10, 10, 20, 20, 'custom', 'moon')")
        assert has_custom_shape()


@pytest.mark.parametrize(
    'mode',
    [
        'by_code',
        'by_drag_drop',
    ],
)
def test_edge_with_style(port, mode, graph_cases_factory):
    """
    :type port: qmxgraph.tests.conftest.Port
    :type mode: str
    :type graph_cases_factory: callable
    """
    styles = GraphStyles({
        'edge': {
            'stroke_color': '#000000',
        },
    })

    with server.host(port=port.get(), styles=styles) as host:
        cases = graph_cases_factory(host)
        graph = cases('2v_1e' if mode == 'by_code' else '2v_1eDD')
        assert graph.get_edge(
            *graph.get_vertices()).get_attribute('stroke') == '#000000'


def test_get_label(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d_1t')

    assert graph.get_label(graph.get_vertices()[0]) == 'foo'
    assert graph.get_label(graph.get_vertices()[1]) == 'bar'
    assert graph.get_label(graph.get_edge(*graph.get_vertices())) == 'edge'
    assert graph.get_label(graph.get_decoration()) == 'decoration'

    # Tables use a complex label in HTML
    table_label = graph.get_label(graph.get_tables()[0])

    table_html_data = []

    from html.parser import HTMLParser

    class TableHTMLParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            # tags used are considered implementation detail, don't care
            # about it
            pass

        def handle_endtag(self, tag):
            # tags used are considered implementation detail, don't care
            # about it
            pass

        def handle_data(self, data):
            table_html_data.append(data)

    parser = TableHTMLParser()
    parser.feed(table_label)
    assert table_html_data == \
        ['Hitchhikers', 'arthur', 'dent', 'ford', 'prefect']


def test_get_label_error_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('2v_1e_1d_1t')

    cell_id = "999"
    with pytest.raises(WebDriverException) as e:
        graph.get_label(cell_id)

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)


def test_has_cell(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('empty')

    cell_id = graph.insert_vertex(x=10, y=10)
    assert graph.eval_js_function("api.hasCell", cell_id)
    graph.remove_cells(cell_id)
    assert not graph.eval_js_function("api.hasCell", cell_id)


def test_get_cell_type(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d_1t')

    def get_cell_type(web_element):
        cell_id = graph.get_id(web_element)
        return graph.eval_js_function('api.getCellType', cell_id)

    assert get_cell_type(graph.get_vertices()[0]) == \
           constants.CELL_TYPE_VERTEX

    assert get_cell_type(graph.get_edge(*graph.get_vertices())) == \
           constants.CELL_TYPE_EDGE

    assert get_cell_type(graph.get_decoration()) == \
           constants.CELL_TYPE_DECORATION

    assert get_cell_type(graph.get_tables()[0]) == \
           constants.CELL_TYPE_TABLE


def test_get_cell_type_error_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('empty')

    cell_id = "999"

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function("api.getCellType", cell_id)

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)


@pytest.mark.parametrize(
    'cell_type',
    [
        qmxgraph.constants.CELL_TYPE_VERTEX,
        qmxgraph.constants.CELL_TYPE_EDGE,
        qmxgraph.constants.CELL_TYPE_TABLE,
        qmxgraph.constants.CELL_TYPE_DECORATION,
    ]
)
def test_insert_with_tags(graph_cases, cell_type):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type cell_type: qmxgraph.constants.CELL_TYPE_*
    """
    graph = graph_cases('empty')

    # Listen to on cells added event to be sure tags are already configured
    # as soon as cell is created
    graph.selenium.execute_script(
        'callback = function(cellIds) {'
        '   window.tags = cellIds.map('
        '       function(cellId) {'
        '           return api.hasTag(cellId, "tagTest")? api.getTag(cellId, "tagTest") : null;'  # noqa
        '       }'
        '   );'
        '}')
    graph.eval_js_function('api.onCellsAdded', js.Variable('callback'))
    tags = {'tagTest': '1'}

    cell_id = insert_by_parametrized_type(graph, cell_type, tags=tags)

    assert graph.selenium.execute_script(
        "return api.getTag({}, 'tagTest')".format(cell_id)) == tags['tagTest']
    assert graph.selenium.execute_script('return window.tags') == \
        [tags['tagTest']]


@pytest.mark.parametrize(
    'cell_type',
    [
        qmxgraph.constants.CELL_TYPE_VERTEX,
        qmxgraph.constants.CELL_TYPE_EDGE,
        qmxgraph.constants.CELL_TYPE_TABLE,
        qmxgraph.constants.CELL_TYPE_DECORATION,
    ]
)
def test_insert_with_tags_error_value_not_string(
        graph_cases, cell_type, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type cell_type: qmxgraph.constants.CELL_TYPE_*
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('empty')

    tags = {'tagTest': 999}

    with pytest.raises(WebDriverException) as e:
        insert_by_parametrized_type(graph, cell_type, tags=tags)

    assert selenium_extras.get_exception_message(e) == \
        "Tag '{}' is not a string".format("tagTest")


@pytest.mark.parametrize(
    'cell_type',
    [
        qmxgraph.constants.CELL_TYPE_VERTEX,
        qmxgraph.constants.CELL_TYPE_EDGE,
        qmxgraph.constants.CELL_TYPE_TABLE,
        qmxgraph.constants.CELL_TYPE_DECORATION,
    ]
)
def test_set_get_tag(graph_cases, cell_type):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type cell_type: qmxgraph.constants.CELL_TYPE_*
    """
    graph = graph_cases('empty')

    cell_id = insert_by_parametrized_type(graph, cell_type)

    assert not graph.eval_js_function("api.hasTag", cell_id, "test")
    graph.eval_js_function("api.setTag", cell_id, "test", "foo")
    assert graph.eval_js_function("api.hasTag", cell_id, "test")
    assert graph.eval_js_function("api.getTag", cell_id, "test") == "foo"


@pytest.mark.parametrize(
    'cell_type',
    [
        qmxgraph.constants.CELL_TYPE_VERTEX,
        qmxgraph.constants.CELL_TYPE_EDGE,
        qmxgraph.constants.CELL_TYPE_TABLE,
        qmxgraph.constants.CELL_TYPE_DECORATION,
    ]
)
def test_set_get_tag_error_tag_not_found(
        graph_cases, cell_type, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type cell_type: qmxgraph.constants.CELL_TYPE_*
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('empty')

    cell_id = insert_by_parametrized_type(graph, cell_type)
    assert not graph.eval_js_function("api.hasTag", cell_id, "test")

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function("api.getTag", cell_id, "test")

    assert selenium_extras.get_exception_message(e) == \
        "Tag '{}' not found in cell with id {}".format("test", cell_id)


@pytest.mark.parametrize(
    'cell_type',
    [
        qmxgraph.constants.CELL_TYPE_VERTEX,
        qmxgraph.constants.CELL_TYPE_EDGE,
        qmxgraph.constants.CELL_TYPE_TABLE,
        qmxgraph.constants.CELL_TYPE_DECORATION,
    ]
)
def test_set_get_tag_error_value_not_string(
        graph_cases, cell_type, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type cell_type: qmxgraph.constants.CELL_TYPE_*
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('empty')

    cell_id = insert_by_parametrized_type(graph, cell_type)

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function("api.setTag", cell_id, "test", 999)

    assert selenium_extras.get_exception_message(e) == \
        "Tag '{}' is not a string".format("test")


@pytest.mark.parametrize(
    'cell_type',
    [
        qmxgraph.constants.CELL_TYPE_VERTEX,
        qmxgraph.constants.CELL_TYPE_EDGE,
        qmxgraph.constants.CELL_TYPE_TABLE,
        qmxgraph.constants.CELL_TYPE_DECORATION,
    ]
)
def test_set_get_tag_doesnt_overwrite_protected_tags(graph_cases, cell_type):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type cell_type: qmxgraph.constants.CELL_TYPE_*
    """
    graph = graph_cases('empty')

    cell_id = insert_by_parametrized_type(graph, cell_type)
    assert not graph.eval_js_function("api.hasTag", cell_id, "label")

    graph.eval_js_function("api.setTag", cell_id, "label", "test")
    assert graph.eval_js_function("api.hasTag", cell_id, "label")
    assert graph.eval_js_function("api.getTag", cell_id, "label") == "test"
    assert graph.eval_js_function("api.getTag", cell_id, "label") != \
        graph.get_label(cell_id)


def test_set_get_tag_error_cell_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('empty')

    cell_id = "999"

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function("api.setTag", cell_id, "test", "foo")

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function("api.getTag", cell_id, "test")

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function("api.hasTag", cell_id, "test")

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)


def test_set_get_tag_without_initial_tag_support(graph_cases):
    """
    For instance, edges created by drag&drop in a graph won't have tags in a
    first moment, as they are created directly by mxGraph code and don't have
    any knowledge about custom tag support. However it should be possible to
    use tag method without problems even with these cells, as tag support
    should be dynamically setup in that case.

    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v')

    graph.insert_edge_by_drag_drop(*graph.get_vertices())
    edge = graph.get_edge(*graph.get_vertices())
    edge_id = graph.get_id(edge)

    assert not graph.eval_js_function("api.hasTag", edge_id, "test")
    graph.eval_js_function("api.setTag", edge_id, "test", "foo")
    assert graph.eval_js_function("api.hasTag", edge_id, "test")
    assert graph.eval_js_function("api.getTag", edge_id, "test") == "foo"


def test_on_cells_added(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e_1d_1t')

    added = [
        graph.get_id(graph.get_vertices()[0]),
        graph.get_id(graph.get_vertices()[1]),
        graph.get_id(graph.get_edge(*graph.get_vertices())),
        graph.get_id(graph.get_decoration()),
        graph.get_id(graph.get_tables()[0]),
    ]

    assert graph.get_added_cell_ids() == added


def test_on_label_changed(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v')
    vertex_id = graph.get_id(graph.get_vertex())

    # Sanity check: custom tags are internally stored in same node element as
    # label. This is to make sure tags aren't lost when label is changed by
    # mistakenly overwriting whole node element instead of just label.
    graph.eval_js_function('api.setTag', vertex_id, 'test', 'test')

    label = graph.get_label(graph.get_vertex())
    label_element = graph.get_label_element(graph.get_vertex())

    actions = ActionChains(graph.selenium)
    actions.double_click(label_element)
    actions.send_keys('foo')
    actions.click(graph.get_container())  # to lose focus and confirm
    actions.perform()

    assert graph.get_label(graph.get_vertex()) == 'foo'
    label_changes = graph.get_label_changes()
    assert label_changes == \
        [{
            'cellId': vertex_id,
            'newLabel': 'foo',
            'oldLabel': label,
        }]
    assert graph.eval_js_function('api.getTag', vertex_id, 'test') == 'test'


def test_set_label(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v')

    vertex_id = graph.get_id(graph.get_vertex())
    label = graph.get_label(graph.get_vertex())

    graph.eval_js_function('api.setLabel', vertex_id, 'foo')

    assert graph.get_label(graph.get_vertex()) == 'foo'
    label_changes = graph.get_label_changes()
    assert label_changes == \
        [{
            'cellId': vertex_id,
            'newLabel': 'foo',
            'oldLabel': label,
        }]


def test_set_label_error_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases("empty")

    cell_id = "999"
    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function('api.setLabel', cell_id, 'foo')

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find cell with id {}".format(cell_id)


def test_set_double_click_handler(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v')
    vertex_id = graph.get_id(graph.get_vertex())

    graph.selenium.execute_script(
        'callback = function(cellId) {'
        '    if (!window.__dblClick__) {'
        '        window.__dblClick__ = [];'
        '    }'
        '    window.__dblClick__.push(cellId);'
        '}')
    graph.eval_js_function(
        'api.setDoubleClickHandler', qmxgraph.js.Variable('callback'))

    actions = ActionChains(graph.selenium)
    actions.double_click(graph.get_vertex())
    actions.perform()

    assert graph.selenium.execute_script('return window.__dblClick__') == \
        [vertex_id]


def test_add_selection_change_handler(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """

    graph = graph_cases('2v_1e')
    source, target = graph.get_vertices()
    edge = graph.get_edge(source, target)

    graph.selenium.execute_script(
        'callback = function(cellIds) {'
        '    if (!window.__selectionChange__) {'
        '        window.__selectionChange__ = [];'
        '    }'
        '    window.__selectionChange__.push(cellIds);'
        '}')
    graph.eval_js_function(
        'api.onSelectionChanged', qmxgraph.js.Variable('callback'))

    # Select all cells.
    actions = ActionChains(graph.selenium)
    actions.key_down(Keys.CONTROL)
    actions.click(source)
    actions.click(target)
    actions.click(edge)
    actions.key_up(Keys.CONTROL)
    actions.perform()

    fired_selection_events = graph.selenium.execute_script(
        'return window.__selectionChange__')
    assert fired_selection_events == [
        ['2'],
        ['3', '2'],
        ['4', '3', '2'],
    ]

    assert graph.eval_js_function('api.getSelectedCells') == ['4', '3', '2']

    # Programmatically select one cell.
    graph.eval_js_function('api.setSelectedCells', ['3'])
    # Clear selection.
    graph.eval_js_function('api.setSelectedCells', [])

    fired_selection_events = graph.selenium.execute_script(
        'return window.__selectionChange__')
    assert fired_selection_events == [
        ['2'],
        ['3', '2'],
        ['4', '3', '2'],
        ['3'],
        [],
    ]


def test_set_popup_menu_handler(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v')

    vertex_id = graph.get_id(graph.get_vertex())

    graph.selenium.execute_script(
        'callback = function(cellId, x, y) {'
        '    if (!window.__popupMenu__) {'
        '        window.__popupMenu__ = [];'
        '    }'
        '    window.__popupMenu__.push([cellId, x, y]);'
        '}')
    graph.eval_js_function(
        'api.setPopupMenuHandler', qmxgraph.js.Variable('callback'))

    vertex_label_el = graph.get_label_element(graph.get_vertex())
    actions = ActionChains(graph.selenium)
    actions.context_click(vertex_label_el)
    actions.perform()

    x = vertex_label_el.location['x'] + vertex_label_el.size['width'] // 2
    y = vertex_label_el.location['y'] + vertex_label_el.size['height'] // 2
    assert graph.selenium.execute_script('return window.__popupMenu__') == \
        [[vertex_id, x, y]]


def test_get_edge_terminals(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('2v_1e')
    source, target = graph.get_vertices()
    edge = graph.get_edge(source, target)

    source_id, target_id = graph.eval_js_function(
        'api.getEdgeTerminals', graph.get_id(edge))
    assert source_id == graph.get_id(source)
    assert target_id == graph.get_id(target)


def test_set_get_style(graph_cases):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    """
    graph = graph_cases('1v')
    vertices = graph.get_vertices()
    assert len(vertices) == 1
    vertex_id = graph.get_id(vertices[0])

    style = graph.eval_js_function('api.getStyle', vertex_id)
    assert style is None

    graph.eval_js_function('api.setStyle', vertex_id, 'foo')
    style = graph.eval_js_function('api.getStyle', vertex_id)
    assert style == 'foo'

    with pytest.raises(WebDriverException) as excinfo:
        graph.eval_js_function('api.getStyle', 'nonexistent')
    assert 'Unable to find cell with id nonexistent' in str(excinfo.value)


def test_get_edge_terminals_error_edge_not_found(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('empty')

    edge_id = "999"

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function('api.getEdgeTerminals', edge_id)

    assert selenium_extras.get_exception_message(e) == \
        "Unable to find edge with id {}".format(edge_id)


def test_get_edge_terminals_error_not_an_edge(graph_cases, selenium_extras):
    """
    :type graph_cases: qmxgraph.tests.conftest.GraphCaseFactory
    :type selenium_extras: qmxgraph.tests.conftest.SeleniumExtras
    """
    graph = graph_cases('1v')
    vertex = graph.get_vertices()[0]

    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function('api.getEdgeTerminals', graph.get_id(vertex))

    assert selenium_extras.get_exception_message(e) == \
        "Cell with id {} is not an edge".format(graph.get_id(vertex))


def test_custom_font_family(graph_cases_factory, port):
    """
    :type graph_cases_factory: callable
    :type port: qmxgraph.tests.conftest.Port
    """
    options = GraphOptions(
        font_family=('Helvetica',),
    )

    with server.host(port=port.get(), options=options) as host:
        cases = graph_cases_factory(host)
        graph = cases("1v")

        match = graph.selenium.find_elements_by_css_selector(
            'div[style*="font-family:Helvetica"]')
        assert len(match) == 1


def test_ports(graph_cases):
    graph = graph_cases('2v')
    vertex_a, vertex_b = graph.get_vertices()
    port_x_name, port_y_name = 'X', 'Y'
    vertex_a_id = graph.get_id(vertex_a)
    vertex_b_id = graph.get_id(vertex_b)

    # Test insert port.
    graph.eval_js_function('api.insertPort', vertex_a_id, port_x_name, 0, 0, 9, 9)
    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function('api.insertPort', vertex_a_id, port_x_name, 1, 1, 9, 9)
    expected = 'The cell {} already have a port named {}'.format(vertex_a_id, port_x_name)
    assert expected in str(e.value)

    # Test remove port.
    graph.eval_js_function('api.removePort', vertex_a_id, port_x_name)
    with pytest.raises(WebDriverException) as e:
        graph.eval_js_function('api.removePort', vertex_a_id, port_x_name)
    expected = 'The cell {} does not have a port named {}'.format(vertex_a_id, port_x_name)
    assert expected in str(e.value)

    # Test insert edge.
    graph.eval_js_function('api.insertPort', vertex_a_id, port_x_name, 0, 0, 9, 9)
    graph.eval_js_function('api.insertPort', vertex_b_id, port_y_name, 0, 0, 9, 9)
    edge_id = graph.eval_js_function(
        'api.insertEdge', vertex_a_id, vertex_b_id, None, None, None, port_x_name, port_y_name)

    # When removing a port remove edges connected through it.
    assert graph.eval_js_function('api.hasCell', edge_id)
    graph.eval_js_function('api.removePort', vertex_b_id, port_y_name)
    assert not graph.eval_js_function('api.hasCell', edge_id)



def fix_table_size(width, height):
    """
    Table is rendered slightly different between platforms, as its width isn't
    fixed but content-based.
    """
    fix_width = 0 if sys.platform.startswith('win') else 10
    return width + fix_width, height


def insert_by_parametrized_type(graph, cell_type, tags=None):
    if cell_type == qmxgraph.constants.CELL_TYPE_VERTEX:
        cell_id = graph.insert_vertex(tags=tags)
    elif cell_type == qmxgraph.constants.CELL_TYPE_TABLE:
        cell_id = graph.insert_table(tags=tags)
    elif cell_type in (
            qmxgraph.constants.CELL_TYPE_EDGE,
            qmxgraph.constants.CELL_TYPE_DECORATION):
        graph.insert_vertex(x=10, y=10)
        graph.insert_vertex(x=90, y=10)
        cell_id = graph.insert_edge(*graph.get_vertices(), tags=tags)
        if cell_type == qmxgraph.constants.CELL_TYPE_DECORATION:
            cell_id = graph.insert_decoration(x=50, y=25, tags=tags)
    else:
        assert False, "Unexpected cell type: {}".format(cell_type)

    return cell_id
