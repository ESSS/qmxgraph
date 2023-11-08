import pytest
from conftest import BaseGraphCase
from conftest import GraphCaseFactory


@pytest.fixture
def graph(graph_cases: GraphCaseFactory) -> BaseGraphCase:
    return graph_cases('empty')


def test_set_style_key(graph: BaseGraphCase) -> None:
    assert graph.eval_js_function('graphs.utils.setStyleKey', '', 'bar', 5) == 'bar=5'
    assert graph.eval_js_function('graphs.utils.setStyleKey', 'style', 'bar', 5) == 'style;bar=5'
    assert (
        graph.eval_js_function('graphs.utils.setStyleKey', 'style;bar=7', 'bar', 5) == 'style;bar=5'
    )
    assert (
        graph.eval_js_function('graphs.utils.setStyleKey', 'foobar=3;bar=7', 'bar', 5)
        == 'foobar=3;bar=5'
    )
    assert (
        graph.eval_js_function('graphs.utils.setStyleKey', 'foobar=3', 'bar', 5) == 'foobar=3;bar=5'
    )
    assert (
        graph.eval_js_function('graphs.utils.setStyleKey', 'foobar=3;fizzbar=7', 'bar', 5)
        == 'foobar=3;fizzbar=7;bar=5'
    )


def test_remove_style_key(graph: BaseGraphCase) -> None:
    assert graph.eval_js_function('graphs.utils.removeStyleKey', '', 'bar') == ''
    assert graph.eval_js_function('graphs.utils.removeStyleKey', 'style;bar=7', 'bar') == 'style'
    assert (
        graph.eval_js_function('graphs.utils.removeStyleKey', 'style;bar=7', 'foo') == 'style;bar=7'
    )
    assert (
        graph.eval_js_function('graphs.utils.removeStyleKey', 'style;bar=7', 'style')
        == 'style;bar=7'
    )
    assert (
        graph.eval_js_function('graphs.utils.removeStyleKey', 'foo=3;bar=7', 'style')
        == 'foo=3;bar=7'
    )
    assert graph.eval_js_function('graphs.utils.removeStyleKey', 'foo=3;bar=7', 'foo') == 'bar=7'
    assert graph.eval_js_function('graphs.utils.removeStyleKey', 'foo=3;bar=7', 'bar') == 'foo=3'
