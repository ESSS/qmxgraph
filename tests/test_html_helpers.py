import pytest

from qmxgraph.html import create_image_tag_str, create_table_entry


def test_create_image_tag():
    image_tag = create_image_tag_str('some-path', 11, 22)
    assert image_tag == '<img src="some-path" width="11" height="22" />'


def test_image_tag_avoid_injection():
    with pytest.raises(ValueError) as exception:
        create_image_tag_str('"', 0, 0)
    assert 'source argument can not have the " character' in str(exception)


def test_create_table_entry():
    assert 'foobar' == create_table_entry('foobar')
    assert 'foobar' == create_table_entry('foobar', colspan=1, rowspan=1)
    assert {
        'value': 'foobar',
        'colspan': 2,
        'rowspan': 3,
    } == create_table_entry('foobar', colspan=2, rowspan=3)

    with pytest.raises(ValueError) as exception:
        create_table_entry('foobar', colspan=4, rowspan=-1)

    error_msg = 'colspan(4) and rowspan(-1) must be non negative values'
    assert error_msg in str(exception)
