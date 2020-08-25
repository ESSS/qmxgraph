import json
import textwrap

import pytest
from PyQt5.QtCore import (QByteArray, QDataStream, QIODevice, QMimeData,
                          QPoint, Qt)
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from _pytest.compat import nullcontext

import qmxgraph.constants
import qmxgraph.js
import qmxgraph.mime
from qmxgraph.callback_blocker import CallbackBlocker, silent_disconnect
from qmxgraph.common_testing import wait_signals


def test_error_redirection(loaded_graph):
    """
    It is possible to redirect errors in JS code to Python/Qt side.

    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    from qmxgraph.widget import ErrorHandlingBridge

    error_redirection = ErrorHandlingBridge()
    loaded_graph.set_error_bridge(error_redirection)

    with wait_signals(error_redirection.on_error) as (cb,):
        eval_js(loaded_graph, """throw Error("test")""")

    msg, url, line, column = cb.args
    assert msg == textwrap.dedent(
        '''\
        Uncaught Error: test
        stack:
        Error: test
            at <anonymous>:1:7'''
    )
    assert (url, line, column) == ('qrc:/', 1, 1)


def test_events_bridge_plain(graph, mocker):
    """
    Verify if the Python code can listen to JavaScript events by using
    qmxgraph's events bridge.

    :type graph: qmxgraph.widget.qmxgraph
    :type mocker: pytest_mock.MockFixture
    """
    from qmxgraph.api import QmxGraphApi
    from qmxgraph.widget import EventsBridge

    events = EventsBridge()
    graph.set_events_bridge(events)

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

    wait_until_loaded(graph)
    # on_cells_added
    with wait_signals(events.on_cells_added):
        vertex_id = graph.api.insert_vertex(40, 40, 20, 20, 'test')
    assert added_handler.call_args_list == [mocker.call([vertex_id])]
    # on_selection_changed
    assert selections_handler.call_args_list == []
    with wait_signals(events.on_selection_changed):
        eval_js(graph, "graphEditor.execute('selectVertices')")
    assert selections_handler.call_args_list == [mocker.call([vertex_id])]
    # on_label_changed
    with wait_signals(events.on_label_changed):
        graph.api.set_label(vertex_id, 'TOTALLY NEW LABEL')
    assert labels_handler.call_args_list == [
        mocker.call(vertex_id, 'TOTALLY NEW LABEL', 'test')]
    # on_terminal_changed, on_terminal_with_port_changed
    foo_id = graph.api.insert_vertex(440, 40, 20, 20, 'foo')
    bar_id = graph.api.insert_vertex(40, 140, 20, 20, 'bar')
    edge_id = graph.api.insert_edge(vertex_id, foo_id, 'edge')
    bar_port_name = 'a-port'
    assert not graph.api.has_port(bar_id, bar_port_name)
    graph.api.insert_port(bar_id, bar_port_name, 0, 0, 5, 5)
    assert graph.api.has_port(bar_id, bar_port_name)

    with wait_signals(
        events.on_terminal_changed, events.on_terminal_with_port_changed,
    ):
        graph.api.set_edge_terminal(
            edge_id, QmxGraphApi.TARGET_TERMINAL_CELL, bar_id, bar_port_name)
    with wait_signals(
        events.on_terminal_changed, events.on_terminal_with_port_changed,
    ):
        graph.api.set_edge_terminal(
            edge_id, QmxGraphApi.SOURCE_TERMINAL_CELL, foo_id)

    assert terminal_handler.call_args_list == [
        mocker.call(
            edge_id, QmxGraphApi.TARGET_TERMINAL_CELL, bar_id, foo_id
        ),
        mocker.call(
            edge_id, QmxGraphApi.SOURCE_TERMINAL_CELL, foo_id, vertex_id
        ),
    ]
    assert terminal_with_port_handler.call_args_list == [
        mocker.call(
            edge_id, QmxGraphApi.TARGET_TERMINAL_CELL,
            bar_id, bar_port_name,
            foo_id, '',
        ),
        mocker.call(
            edge_id, QmxGraphApi.SOURCE_TERMINAL_CELL,
            foo_id, '',
            vertex_id, '',
        ),
    ]
    # on_cells_removed
    with wait_signals(events.on_cells_removed):
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
    from qmxgraph.widget import EventsBridge

    def handler_that_call_api(*args):
        result = loaded_graph.api.get_zoom_scale()
        assert result == 1

    events = EventsBridge()
    loaded_graph.set_events_bridge(events)
    events.on_cells_added.connect(handler_that_call_api)
    with wait_signals(events.on_cells_added):
        loaded_graph.api.insert_vertex(40, 40, 20, 20, 'test')


def test_set_double_click_handler(graph, handler):
    """
    :type graph: qmxgraph.widget.qmxgraph
    :type handler: _HandlerFixture
    """
    js_script = "graphEditor.execute('doubleClick', {vertex})"

    # Handler can be set even while not yet loaded
    graph.set_double_click_handler(handler.handler_func)
    handler.assert_handled(
        js_script=js_script, called=True, expected_calls=[()],
    )

    # It should be restored if loaded again after being blanked
    wait_until_blanked(graph)
    handler.assert_handled(
        js_script=js_script, called=True, expected_calls=[()],
    )

    # Setting handler to None disconnects it from event
    graph.set_double_click_handler(None)
    handler.assert_handled(
        js_script=js_script, called=False, expected_calls=[],
    )


def test_set_popup_menu_handler(graph, handler):
    """
    :type graph: qmxgraph.widget.qmxgraph
    :type handler: _HandlerFixture
    """
    js_script = "graphEditor.execute('popupMenu', {vertex}, 15, 15)"

    # Handler can be set even while not yet loaded
    graph.set_popup_menu_handler(handler.handler_func)
    handler.assert_handled(
        js_script=js_script, called=True, expected_calls=[(15, 15)],
    )

    # It should be restored if loaded again after being blanked
    wait_until_blanked(graph)
    handler.assert_handled(
        js_script=js_script, called=True, expected_calls=[(15, 15)],
    )

    # Setting handler to None disconnects it from event
    graph.set_popup_menu_handler(None)
    handler.assert_handled(
        js_script=js_script, called=False, expected_calls=[],
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
        width = eval_js(
            loaded_graph,
            """document.getElementById('graphContainer').style.width""")
        height = eval_js(
            loaded_graph,
            """document.getElementById('graphContainer').style.height""")
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


def test_blank(loaded_graph):
    """
    :type loaded_graph: qmxgraph.widget.QmxGraph
    """
    assert eval_js(loaded_graph, 'typeof api !== "undefined"')
    assert loaded_graph.is_loaded()

    # Graph page that was loaded is now unloaded by `blank` call and all
    # objects formerly available in JavaScript window object are now gone
    wait_until_blanked(loaded_graph)
    assert eval_js(loaded_graph, 'typeof api === "undefined"')
    assert not loaded_graph.is_loaded()


def test_drag_drop(loaded_graph, drag_drop_events):
    """
    Dragging and dropping data with valid qmxgraph MIME data in qmxgraph should
    result graph changes according to contents of dropped data.

    :type loaded_graph: qmxgraph.widget.qmxgraph
    :type drag_drop_events: DragDropEventsFactory
    """
    mime_data = qmxgraph.mime.create_qt_mime_data({
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
    })

    drag_enter_event = drag_drop_events.drag_enter(
        mime_data, position=(100, 100))
    loaded_graph.inner_web_view().dragEnterEvent(drag_enter_event)
    assert drag_enter_event.acceptProposedAction.call_count == 1

    drag_move_event = drag_drop_events.drag_move(
        mime_data, position=(100, 100))
    loaded_graph.inner_web_view().dragEnterEvent(drag_move_event)
    assert drag_move_event.acceptProposedAction.call_count == 1

    drop_event = drag_drop_events.drop(mime_data, position=(100, 100))
    loaded_graph.inner_web_view().dropEvent(drop_event)
    assert drop_event.acceptProposedAction.call_count == 1

    cell_id = loaded_graph.api.get_cell_id_at(100, 100)
    assert loaded_graph.api.get_cell_type(cell_id) == \
        qmxgraph.constants.CELL_TYPE_VERTEX
    assert loaded_graph.api.get_geometry(cell_id) == \
        [100. - 64 / 2, 100. - 64 / 2, 64., 64.]
    assert loaded_graph.api.get_label(cell_id) == 'test 1'

    cell_id = loaded_graph.api.get_cell_id_at(150, 150)
    assert loaded_graph.api.get_cell_type(cell_id) == \
        qmxgraph.constants.CELL_TYPE_VERTEX
    assert loaded_graph.api.get_geometry(cell_id) == \
        [150. - 32 / 2, 150. - 32 / 2, 32., 32.]
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
        json.dumps(
            '<?xml version="1.0"?><message>Hello World!</message>'
        ).encode('utf8'))

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
    mime_data = qmxgraph.mime.create_qt_mime_data({
        'version':-1,
    })

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
    from pytestqt.plugin import capture_exceptions
    with capture_exceptions() as exceptions:
        loaded_graph.inner_web_view().dropEvent(drop_event)

    assert drop_event.acceptProposedAction.call_count == 0
    assert len(exceptions) == 1
    assert str(exceptions[0][1]) == \
        "Unsupported version of QmxGraph MIME data: -1"


@pytest.mark.parametrize('debug', (True, False))
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

            assert str(api_exception.value) == \
                'Unable to find function "BOOM" in QmxGraph JavaScript API'
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
        ('is_cells_movable', 'set_cells_movable',),
        ('is_cells_connectable', 'set_cells_connectable',),
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

    with_tags_id = loaded_graph.api.insert_vertex(
        50, 50, 20, 20, 'test', tags={'bar': '2'})
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

    assert get_cell_count(loaded_graph,
                          'function(cell){ return false }') == 0
    assert get_cell_count(loaded_graph,
                          'function(cell){ return cell.isEdge() }') == 1
    assert get_cell_count(loaded_graph,
                          'function(cell){ return cell.isVertex() }') == 2


def test_get_cell_ids(loaded_graph):
    """
    :type loaded_graph: qmxgraph.widget.qmxgraph
    """
    from qmxgraph.common_testing import get_cell_ids
    node_a = loaded_graph.api.insert_vertex(10, 10, 50, 50, 'A')
    node_b = loaded_graph.api.insert_vertex(400, 300, 50, 50, 'B')
    loaded_graph.api.insert_edge(node_a, node_b, 'AB')

    assert get_cell_ids(loaded_graph,
                        'function(cell){ return false }') == []
    assert get_cell_ids(loaded_graph,
                        'function(cell){ return cell.isEdge() }') == ['4']
    assert get_cell_ids(loaded_graph,
                        'function(cell){ return cell.isVertex() }') == ['2', '3']


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
def graph_(qtbot):
    """
    :type qtbot: pytestqt.plugin.QtBot
    :rtype: qmxgraph.widget.qmxgraph
    """
    from qmxgraph.widget import QmxGraph
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
    wait_until_loaded(graph)
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
        return self._create_dd_event(
            QDragEnterEvent, mime_data=mime_data, position=position)

    def drag_move(self, mime_data, position=None):
        return self._create_dd_event(
            QDragMoveEvent, mime_data=mime_data, position=position)

    def drop(self, mime_data, position=None):
        return self._create_dd_event(
            QDropEvent, mime_data=mime_data, position=position)

    def _create_dd_event(self, event_type, position, mime_data):
        # just a sensible position to those test this is useless
        position = position or (100, 100)
        dd_args = QPoint(*position), Qt.MoveAction, \
            mime_data, Qt.LeftButton, Qt.NoModifier
        dd_event = event_type(*dd_args)
        self.mocker.spy(dd_event, 'acceptProposedAction')
        self.mocker.spy(dd_event, 'ignore')
        return dd_event


def wait_until_loaded(graph):
    """
    :type graph: qmxgraph.widget.qmxgraph
    """
    with CallbackBlocker(timeout=5000, msg='wait_until_loaded') as cb:
        graph.loadFinished.connect(cb)
        graph.load()
    silent_disconnect(graph.loadFinished, cb)


def wait_until_blanked(graph):
    """
    :type graph: qmxgraph.widget.qmxgraph
    """
    with CallbackBlocker(timeout=5000, msg='wait_until_blanked') as cb:
        graph.loadFinished.connect(cb)
        graph.blank()
    silent_disconnect(graph.loadFinished, cb)


class _HandlerFixture:
    def __init__(self, graph):
        self.calls = []
        self.cb = None
        self.graph = graph

    def handler_func(self, *args):
        assert self.cb and self.cb._timer
        self.calls.append(args)
        self.cb(*args)

    def assert_handled(self, *, js_script, called, expected_calls=()):
        assert "{vertex}" in js_script
        wait_until_loaded(self.graph)
        vertex_id = self.graph.api.insert_vertex(
            10, 10, 20, 20, 'handler fixture test',
        )
        js_script = js_script.format(
            vertex=f"graphEditor.graph.model.getCell({vertex_id})",
        )

        if called:
            error_context = nullcontext()
        else:
            error_context = pytest.raises(
                TimeoutError, match="Callback wasn't called",
            )

        with error_context:
            with CallbackBlocker() as cb:
                self.cb = cb
                eval_js(self.graph, js_script)

        assert self.calls == [
            tuple(vertex_id) + tuple(args) for args in expected_calls
        ]
        self.calls.clear()


@pytest.fixture(name='handler')
def handler_(graph):
    """
    :type graph: qmxgraph.widget.qmxgraph
    :rtype: _HandlerFixture
    """
    return _HandlerFixture(graph)
