import json
import textwrap
from functools import partial

import pytest
import pytestqt.exceptions
from _pytest.compat import nullcontext
from PyQt5.QtCore import QByteArray
from PyQt5.QtCore import QDataStream
from PyQt5.QtCore import QIODevice
from PyQt5.QtCore import QMimeData
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtGui import QDragMoveEvent
from PyQt5.QtGui import QDropEvent
from pytest_mock import MockFixture

import qmxgraph.constants
import qmxgraph.js
import qmxgraph.mime
from qmxgraph._web_view import ViewState
from qmxgraph.exceptions import ViewStateError
from qmxgraph.waiting import wait_callback_called
from qmxgraph.waiting import wait_signals_called
from qmxgraph.widget import QmxGraph


def test_error_redirection(loaded_graph):
    """
    It is possible to redirect errors in JS code to Python/Qt side.

    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    error_redirection = loaded_graph.error_bridge

    with wait_signals_called(error_redirection.on_error) as cb:
        eval_js(loaded_graph, """throw Error("test")""")

    msg, url, line, column = cb.args
    expected = textwrap.dedent(
        '''\
        Uncaught Error: test
        stack:
        Error: test
            at <anonymous>:1:7'''
    )
    assert (url, line, column) == ('qrc:/', 1, 1)


def test_events_bridge_delayed_signals(graph, qtbot, mocker):
    from qmxgraph.widget import EventsBridge

    events = EventsBridge()

    stub = mocker.stub()
    call = mocker.call
    events.on_cells_added.connect(stub)

    events.cells_added_slot(["1"])
    assert stub.call_args_list == []

    def check_call(expected):
        assert stub.call_args_list == expected

    qtbot.waitUntil(partial(check_call, [call(["1"])]))

    with events.delaying_signals():
        events.cells_added_slot(["2"])

        with pytest.raises(pytestqt.exceptions.TimeoutError):
            expected = [call(["1"]), call(["2"])]
            qtbot.waitUntil(partial(check_call, expected), timeout=1000)

    qtbot.waitUntil(partial(check_call, expected))


def test_events_bridge_plain(graph, mocker):
    """
    Verify if the Python code can listen to JavaScript events by using
    qmxgraph's events bridge.

    :type graph: qmxgraph.widget.qmxgraph
    :type mocker: pytest_mock.MockFixture
    """
    from qmxgraph.api import QmxGraphApi

    events = graph.events_bridge

    added_handler = mocker.Mock()
    removed_handler = mocker.Mock()
    labels_handler = mocker.Mock()
    selections_handler = mocker.Mock()
    terminal_handler = mocker.Mock()
    terminal_with_port_handler = mocker.Mock()

    events.on_cells_added.connect(added_handler)
    events.on_cells_removed.connect(removed_handler)
    events.on_label_changed.connect(labels_handler)
    events.on_selection_changed.connect(selections_handler)
    events.on_terminal_changed.connect(terminal_handler)
    events.on_terminal_with_port_changed.connect(terminal_with_port_handler)

    graph.load_and_wait()
    # on_cells_added
    with wait_signals_called(events.on_cells_added):
        vertex_id = graph.api.insert_vertex(40, 40, 20, 20, 'test')
    assert added_handler.call_args_list == [mocker.call([vertex_id])]
    # on_selection_changed
    assert selections_handler.call_args_list == []
    with wait_signals_called(events.on_selection_changed):
        eval_js(graph, "graphEditor.execute('selectVertices')")
    assert selections_handler.call_args_list == [mocker.call([vertex_id])]
    # on_label_changed
    with wait_signals_called(events.on_label_changed):
        graph.api.set_label(vertex_id, 'TOTALLY NEW LABEL')
    assert labels_handler.call_args_list == [mocker.call(vertex_id, 'TOTALLY NEW LABEL', 'test')]
    # on_terminal_changed, on_terminal_with_port_changed
    foo_id = graph.api.insert_vertex(440, 40, 20, 20, 'foo')
    bar_id = graph.api.insert_vertex(40, 140, 20, 20, 'bar')
    edge_id = graph.api.insert_edge(vertex_id, foo_id, 'edge')
    bar_port_name = 'a-port'
    assert not graph.api.has_port(bar_id, bar_port_name)
    graph.api.insert_port(bar_id, bar_port_name, 0, 0, 5, 5)
    assert graph.api.has_port(bar_id, bar_port_name)

    with wait_signals_called(
        events.on_terminal_changed,
        events.on_terminal_with_port_changed,
    ):
        graph.api.set_edge_terminal(
            edge_id, QmxGraphApi.TARGET_TERMINAL_CELL, bar_id, bar_port_name
        )
    with wait_signals_called(
        events.on_terminal_changed,
        events.on_terminal_with_port_changed,
    ):
        graph.api.set_edge_terminal(edge_id, QmxGraphApi.SOURCE_TERMINAL_CELL, foo_id)

    assert terminal_handler.call_args_list == [
        mocker.call(edge_id, QmxGraphApi.TARGET_TERMINAL_CELL, bar_id, foo_id),
        mocker.call(edge_id, QmxGraphApi.SOURCE_TERMINAL_CELL, foo_id, vertex_id),
    ]
    assert terminal_with_port_handler.call_args_list == [
        mocker.call(
            edge_id,
            QmxGraphApi.TARGET_TERMINAL_CELL,
            bar_id,
            bar_port_name,
            foo_id,
            '',
        ),
        mocker.call(
            edge_id,
            QmxGraphApi.SOURCE_TERMINAL_CELL,
            foo_id,
            '',
            vertex_id,
            '',
        ),
    ]
    # on_cells_removed
    with wait_signals_called(events.on_cells_removed):
        graph.api.remove_cells([vertex_id])
    assert removed_handler.call_args_list == [mocker.call([vertex_id])]


def test_bridges_signal_handlers_can_call_api(loaded_graph):
    """
    Verify if the Python code handling bridge signals can call the
    qmxgraph api.
    Testing only one method of `EventsBridge` since all bridge signals
    are handled the same way.

    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    zoom_scale_obtained = []

    def handler_that_call_api(*args):
        result = loaded_graph.api.get_zoom_scale()
        zoom_scale_obtained.append(result)

    events = loaded_graph.events_bridge
    events.on_cells_added.connect(handler_that_call_api)
    with wait_signals_called(events.on_cells_added):
        loaded_graph.api.insert_vertex(40, 40, 20, 20, 'test')

    assert zoom_scale_obtained == [1]


def test_set_double_click_handler(graph, handler, qtbot):
    """
    :type graph: qmxgraph.widget.qmxgraph
    :type handler: _HandlerFixture
    """
    js_script = "graphEditor.execute('doubleClick', {vertex})"

    # Handler can be set even while not yet loaded
    graph.double_click_bridge.on_double_click.connect(handler.handler_func)
    handler.assert_handled(
        js_script=js_script,
        called=True,
        expected_calls=[()],
    )

    # It should be restored if loaded again after being blanked
    wait_until_blanked(qtbot, graph)
    handler.assert_handled(
        js_script=js_script,
        called=True,
        expected_calls=[()],
    )

    # Setting handler to None disconnects it from event
    graph.double_click_bridge.on_double_click.disconnect(handler.handler_func)
    handler.assert_handled(
        js_script=js_script,
        called=False,
        expected_calls=[],
    )


def test_set_popup_menu_handler(graph, handler, qtbot):
    """
    :type graph: qmxgraph.widget.qmxgraph
    :type handler: _HandlerFixture
    """
    js_script = "graphEditor.execute('popupMenu', {vertex}, 15, 15)"

    # Handler can be set even while not yet loaded
    graph.popup_menu_bridge.on_popup_menu.connect(handler.handler_func)
    handler.assert_handled(
        js_script=js_script,
        called=True,
        expected_calls=[(15, 15)],
    )

    # It should be restored if loaded again after being blanked
    wait_until_blanked(qtbot, graph)
    handler.assert_handled(
        js_script=js_script,
        called=True,
        expected_calls=[(15, 15)],
    )

    # Setting handler to None disconnects it from event
    graph.popup_menu_bridge.on_popup_menu.disconnect(handler.handler_func)
    handler.assert_handled(
        js_script=js_script,
        called=False,
        expected_calls=[],
    )


def test_container_resize(loaded_graph):
    """
    The div containing graph in web view must be resized match dimensions of
    Qt widget in initialization and also when web view is resized.

    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    expected_width = loaded_graph.inner_web_view().width()
    expected_height = loaded_graph.inner_web_view().height()

    def get_container_dimensions():
        width = eval_js(loaded_graph, """document.getElementById('graphContainer').style.width""")
        height = eval_js(loaded_graph, """document.getElementById('graphContainer').style.height""")
        return int(width.replace('px', '')), int(height.replace('px', ''))

    width, height = get_container_dimensions()
    assert width == expected_width
    assert height == expected_height

    expected_width += 20
    loaded_graph.resize(expected_width, expected_height)
    width, height = get_container_dimensions()
    assert width == expected_width
    assert height == expected_height


def test_web_inspector(loaded_graph, mocker):
    """
    :type loaded_graph: qmxgraph.widget.qmxgraph
    :type mocker: pytest_mock.MockFixture
    """
    from PyQt5.QtWidgets import QDialog

    mocker.patch.object(QDialog, 'show')
    mocker.patch.object(QDialog, 'hide')

    loaded_graph.show_inspector()
    QDialog.show.assert_called_once_with()

    loaded_graph.hide_inspector()
    QDialog.hide.assert_called_once_with()

    QDialog.show.reset_mock()
    loaded_graph.toggle_inspector()
    QDialog.show.assert_called_once_with()


def test_blank(loaded_graph, qtbot):
    """
    :type loaded_graph: qmxgraph.widget.QmxGraph
    """
    assert loaded_graph.is_loaded()

    loaded_graph.blank()

    def check():
        assert loaded_graph.inner_web_view().view_state == ViewState.Blank

    qtbot.waitUntil(check)
    assert not loaded_graph.is_loaded()


def test_blank_and_load(graph, qtbot):
    graph.load_and_wait()
    graph.blank()
    wait_until_blanked(qtbot, graph)
    graph.load_and_wait(timeout_ms=5000)


def test_web_channel_blocking(graph, qtbot):
    def is_web_channel_blocked() -> bool:
        # Both updates and signals should be blocked/unblocked. at the same time.
        result = graph.inner_web_view().page().webChannel().blockUpdates()
        assert graph.inner_web_view().page().webChannel().signalsBlocked() is result
        return result

    assert is_web_channel_blocked() is True
    graph.load_and_wait()
    assert is_web_channel_blocked() is False
    graph.blank_and_wait()
    assert is_web_channel_blocked() is True
    graph.load_and_wait()
    assert is_web_channel_blocked() is False


def test_call_once_when_loaded(graph: QmxGraph, mocker: MockFixture) -> None:
    stubA = mocker.stub()
    graph.call_once_when_loaded(stubA)

    graph.load_and_wait()
    assert stubA.call_count == 1

    stubB = mocker.stub()
    graph.call_once_when_loaded(stubB)

    assert stubA.call_count == 1
    assert stubB.call_count == 1

    graph.blank_and_wait()
    stubC = mocker.stub()
    graph.call_once_when_loaded(stubC)

    graph.load_and_wait()
    assert stubA.call_count == 1
    assert stubB.call_count == 1
    assert stubC.call_count == 1


def test_state_errors_after_closing(graph: QmxGraph) -> None:
    graph.close()
    with pytest.raises(ViewStateError):
        graph.load_and_wait()
    with pytest.raises(ViewStateError):
        graph.blank_and_wait()


def test_drag_drop(loaded_graph, drag_drop_events):
    """
    Dragging and dropping data with valid qmxgraph MIME data in qmxgraph should
    result graph changes according to contents of dropped data.

    :type loaded_graph: qmxgraph.widget.qmxgraph
    :type drag_drop_events: DragDropEventsFactory
    """
    mime_data = qmxgraph.mime.create_qt_mime_data(
        {
            'vertices': [
                {
                    'dx': 0,
                    'dy': 0,
                    'width': 64,
                    'height': 64,
                    'label': 'test 1',
                },
                {
                    'dx': 50,
                    'dy': 50,
                    'width': 32,
                    'height': 32,
                    'label': 'test 2',
                    'tags': {'foo': '1', 'bar': 'a'},
                },
            ],
        }
    )

    drag_enter_event = drag_drop_events.drag_enter(mime_data, position=(100, 100))
    loaded_graph.inner_web_view().dragEnterEvent(drag_enter_event)
    assert drag_enter_event.acceptProposedAction.call_count == 1

    drag_move_event = drag_drop_events.drag_move(mime_data, position=(100, 100))
    loaded_graph.inner_web_view().dragEnterEvent(drag_move_event)
    assert drag_move_event.acceptProposedAction.call_count == 1

    drop_event = drag_drop_events.drop(mime_data, position=(100, 100))
    loaded_graph.inner_web_view().dropEvent(drop_event)
    assert drop_event.acceptProposedAction.call_count == 1

    cell_id = loaded_graph.api.get_cell_id_at(100, 100)
    assert loaded_graph.api.get_cell_type(cell_id) == qmxgraph.constants.CELL_TYPE_VERTEX
    assert loaded_graph.api.get_geometry(cell_id) == [100.0 - 64 / 2, 100.0 - 64 / 2, 64.0, 64.0]
    assert loaded_graph.api.get_label(cell_id) == 'test 1'

    cell_id = loaded_graph.api.get_cell_id_at(150, 150)
    assert loaded_graph.api.get_cell_type(cell_id) == qmxgraph.constants.CELL_TYPE_VERTEX
    assert loaded_graph.api.get_geometry(cell_id) == [150.0 - 32 / 2, 150.0 - 32 / 2, 32.0, 32.0]
    assert loaded_graph.api.get_label(cell_id) == 'test 2'
    assert loaded_graph.api.get_tag(cell_id, 'foo') == '1'
    assert loaded_graph.api.get_tag(cell_id, 'bar') == 'a'


def test_drag_drop_invalid_mime_type(loaded_graph, drag_drop_events):
    """
    Can't drop data in qmxgraph unless it is from qmxgraph valid MIME type,
    all events should be ignored.

    :type loaded_graph: qmxgraph.widget.qmxgraph
    :type drag_drop_events: DragDropEventsFactory
    """
    item_data = QByteArray()
    data_stream = QDataStream(item_data, QIODevice.WriteOnly)
    data_stream.writeString(
        json.dumps('<?xml version="1.0"?><message>Hello World!</message>').encode('utf8')
    )

    mime_data = QMimeData()
    mime_data.setData('application/xml', item_data)

    drag_enter_event = drag_drop_events.drag_enter(mime_data)
    loaded_graph.inner_web_view().dragEnterEvent(drag_enter_event)
    assert drag_enter_event.ignore.call_count == 1

    drag_move_event = drag_drop_events.drag_move(mime_data)
    loaded_graph.inner_web_view().dragMoveEvent(drag_move_event)
    assert drag_move_event.ignore.call_count == 1

    drop_event = drag_drop_events.drop(mime_data)
    loaded_graph.inner_web_view().dropEvent(drop_event)
    assert drop_event.ignore.call_count == 1


@pytest.mark.qt_no_exception_capture
def test_drag_drop_invalid_version(loaded_graph, drag_drop_events):
    """
    :type loaded_graph: qmxgraph.widget.qmxgraph
    :type drag_drop_events: DragDropEventsFactory
    """
    mime_data = qmxgraph.mime.create_qt_mime_data(
        {
            'version': -1,
        }
    )

    drag_enter_event = drag_drop_events.drag_enter(mime_data)
    loaded_graph.inner_web_view().dragEnterEvent(drag_enter_event)
    assert drag_enter_event.acceptProposedAction.call_count == 1

    drag_move_event = drag_drop_events.drag_move(mime_data)
    loaded_graph.inner_web_view().dragMoveEvent(drag_move_event)
    assert drag_move_event.acceptProposedAction.call_count == 1

    drop_event = drag_drop_events.drop(mime_data)

    import sys

    print(
        (
            'This test will cause an exception in a Qt event loop:\n'
            '    ValueError: Unsupported version of QmxGraph MIME data: -1'
        ),
        file=sys.stderr,
    )
    from pytestqt.exceptions import capture_exceptions

    with capture_exceptions() as exceptions:
        loaded_graph.inner_web_view().dropEvent(drop_event)

    assert drop_event.acceptProposedAction.call_count == 0
    assert len(exceptions) == 1
    assert str(exceptions[0][1]) == "Unsupported version of QmxGraph MIME data: -1"


@pytest.mark.parametrize('debug', (True, False))
@pytest.mark.xfail(reason="ASIM-4287: append extra debug checks to api calls", run=False)
def test_invalid_api_call(loaded_graph, debug):
    """
    :type loaded_graph: qmxgraph.widget.qmxgraph
    :type debug: bool
    """
    import qmxgraph.debug

    old_debug = qmxgraph.debug.is_qmxgraph_debug_enabled()
    qmxgraph.debug.set_qmxgraph_debug(debug)
    try:
        if debug:
            # When debug feature is enabled, it fails as soon as call is made
            with pytest.raises(qmxgraph.js.InvalidJavaScriptError) as api_exception:
                loaded_graph.api.call_api('BOOM')

            assert (
                str(api_exception.value)
                == 'Unable to find function "BOOM" in QmxGraph JavaScript API'
            )
        else:
            # When debug feature is disabled, code will raise on JavaScript
            # side, but unless an error bridge is configured that could go
            # unnoticed, as call would return None and could easily be
            # mistaken by an OK call
            assert loaded_graph.api.call_api('BOOM') is None
    finally:
        qmxgraph.debug.set_qmxgraph_debug(old_debug)


@pytest.mark.parametrize('enabled', (True, False))
def test_graph_api_calls(loaded_graph, enabled):
    """
    Tests the available calls to the graph api.
    """
    graph_api_functions = [
        ('is_cells_deletable', 'set_cells_deletable'),
        ('is_cells_disconnectable', 'set_cells_disconnectable'),
        ('is_cells_editable', 'set_cells_editable'),
        (
            'is_cells_movable',
            'set_cells_movable',
        ),
        (
            'is_cells_connectable',
            'set_cells_connectable',
        ),
    ]

    for getter_name, setter_name in graph_api_functions:
        getter_func = getattr(loaded_graph.api, getter_name)
        setter_func = getattr(loaded_graph.api, setter_name)

        setter_func(enabled)
        assert getter_func() is enabled
        setter_func(not enabled)
        assert getter_func() is not enabled


def test_tags(loaded_graph):
    """
    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    no_tags_id = loaded_graph.api.insert_vertex(10, 10, 20, 20, 'test')

    assert not loaded_graph.api.has_tag(no_tags_id, 'foo')
    loaded_graph.api.set_tag(no_tags_id, 'foo', '1')
    assert loaded_graph.api.has_tag(no_tags_id, 'foo')
    assert loaded_graph.api.get_tag(no_tags_id, 'foo') == '1'

    with_tags_id = loaded_graph.api.insert_vertex(50, 50, 20, 20, 'test', tags={'bar': '2'})
    assert loaded_graph.api.has_tag(with_tags_id, 'bar')
    assert loaded_graph.api.get_tag(with_tags_id, 'bar') == '2'


def test_get_cell_count(loaded_graph):
    """
    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    from qmxgraph.common_testing import get_cell_count

    node_a = loaded_graph.api.insert_vertex(10, 10, 50, 50, 'A')
    node_b = loaded_graph.api.insert_vertex(400, 300, 50, 50, 'B')
    loaded_graph.api.insert_edge(node_a, node_b, 'AB')

    assert get_cell_count(loaded_graph, 'function(cell){ return false }') == 0
    assert get_cell_count(loaded_graph, 'function(cell){ return cell.isEdge() }') == 1
    assert get_cell_count(loaded_graph, 'function(cell){ return cell.isVertex() }') == 2


def test_get_cell_ids(loaded_graph):
    """
    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    from qmxgraph.common_testing import get_cell_ids

    node_a = loaded_graph.api.insert_vertex(10, 10, 50, 50, 'A')
    node_b = loaded_graph.api.insert_vertex(400, 300, 50, 50, 'B')
    loaded_graph.api.insert_edge(node_a, node_b, 'AB')

    assert get_cell_ids(loaded_graph, 'function(cell){ return false }') == []
    assert get_cell_ids(loaded_graph, 'function(cell){ return cell.isEdge() }') == ['4']
    assert get_cell_ids(loaded_graph, 'function(cell){ return cell.isVertex() }') == ['2', '3']


def test_last_index_of(loaded_graph):
    """
    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    assert eval_js(loaded_graph, "'canal'.lastIndexOf('a')") == 3
    assert eval_js(loaded_graph, "'canal'.lastIndexOf('a', 2)") == 1
    assert eval_js(loaded_graph, "'canal'.lastIndexOf('a', 0)") == -1
    assert eval_js(loaded_graph, "'canal'.lastIndexOf('x')") == -1
    assert eval_js(loaded_graph, "'canal'.lastIndexOf('c', -5)") == 0
    assert eval_js(loaded_graph, "'canal'.lastIndexOf('c', 0)") == 0
    assert eval_js(loaded_graph, "'canal'.lastIndexOf('')") == 5
    assert eval_js(loaded_graph, "'canal'.lastIndexOf('', 2)") == 2


def eval_js(graph_widget, statement):
    return graph_widget.inner_web_view().eval_js(statement)


@pytest.fixture(name='graph')
def graph_(qtbot) -> QmxGraph:
    """
    :type qtbot: pytestqt.plugin.QtBot
    :rtype: qmxgraph.widget.qmxgraph
    """
    graph_ = QmxGraph(auto_load=False)
    graph_.show()
    qtbot.addWidget(graph_)

    return graph_


@pytest.fixture(name='loaded_graph')
def loaded_graph_(graph):
    """
    :type graph: qmxgraph.widget.qmxgraph
    :rtype: qmxgraph.widget.qmxgraph
    """
    graph.load_and_wait()
    return graph


@pytest.fixture(name='drag_drop_events')
def drag_drop_events_(mocker):
    """
    :type mocker: pyest_mock.MockFixture
    :rtype: DragDropEventsFactory
    """
    return DragDropEventsFactory(mocker)


class DragDropEventsFactory(object):
    """
    Creates Qt drag & drop events spying some essential methods so tests can
    track how many calls are made to them.
    """

    def __init__(self, mocker):
        self.mocker = mocker

    def drag_enter(self, mime_data, position=None):
        return self._create_dd_event(QDragEnterEvent, mime_data=mime_data, position=position)

    def drag_move(self, mime_data, position=None):
        return self._create_dd_event(QDragMoveEvent, mime_data=mime_data, position=position)

    def drop(self, mime_data, position=None):
        return self._create_dd_event(QDropEvent, mime_data=mime_data, position=position)

    def _create_dd_event(self, event_type, position, mime_data):
        # just a sensible position to those test this is useless
        position = position or (100, 100)
        dd_args = QPoint(*position), Qt.MoveAction, mime_data, Qt.LeftButton, Qt.NoModifier
        dd_event = event_type(*dd_args)
        self.mocker.spy(dd_event, 'acceptProposedAction')
        self.mocker.spy(dd_event, 'ignore')
        return dd_event


def wait_until_blanked(qtbot, graph):
    """
    :type graph: qmxgraph.widget.qmxgraph
    """
    graph.blank()

    def is_blank():
        assert graph.inner_web_view().view_state == ViewState.Blank

    qtbot.waitUntil(is_blank)


class _HandlerFixture:
    def __init__(self, graph, qtbot):
        self.calls = []
        self.cb = None
        self.graph = graph
        self.qtbot = qtbot

    def handler_func(self, *args):
        assert self.cb
        self.calls.append(args)
        self.cb(*args)

    def assert_handled(self, *, js_script, called, expected_calls=()):
        pass

        assert "{vertex}" in js_script
        self.graph.load_and_wait()
        vertex_id = self.graph.api.insert_vertex(
            10,
            10,
            20,
            20,
            'handler fixture test',
        )
        js_script = js_script.format(
            vertex=f"graphEditor.graph.model.getCell({vertex_id})",
        )
        if called:
            error_context = nullcontext()
        else:
            error_context = pytest.raises(TimeoutError)

        with error_context:
            with wait_callback_called() as cb:
                self.cb = cb

                eval_js(self.graph, js_script)

        assert self.calls == [tuple(vertex_id) + tuple(args) for args in expected_calls]
        self.calls.clear()


@pytest.fixture(name='handler')
def handler_(graph, qtbot):
    """
    :type graph: qmxgraph.widget.qmxgraph
    :rtype: _HandlerFixture
    """
    return _HandlerFixture(graph, qtbot)
