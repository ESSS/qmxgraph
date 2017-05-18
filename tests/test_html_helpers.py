import pytest

from qmxgraph.html import create_image_tag_str


def test_create_image_tag():
    image_tag = create_image_tag_str('some-path', 11, 22)
    assert image_tag == '<img src="some-path" width="11" height="22" />'


def test_image_tag_avoid_injection():
    with pytest.raises(ValueError) as exception:
        create_image_tag_str('"', 0, 0)
    assert 'source argument can not have the " character' in str(exception)
