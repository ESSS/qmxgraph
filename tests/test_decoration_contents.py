import attr
import pytest

from qmxgraph import extra_attr_validators


@attr.s
class Cutlery:
    name = attr.ib()


@attr.s
class Door:
    pass


@attr.s
class Household:
    silverware = attr.ib(validator=extra_attr_validators.tuple_of(Cutlery))


def test_tuple_of_validator() -> None:
    Household(silverware=(Cutlery(name='fork'),))

    with pytest.raises(TypeError) as execinfo:
        Household(silverware=Cutlery(name='fork'))
    msg = "'silverware' must be a tuple but got Cutlery(name='fork')"
    assert msg in str(execinfo.value)

    with pytest.raises(TypeError) as execinfo:
        Household(silverware=(Cutlery(name='fork'), Door()))
    assert "'silverware' must be a tuple of " in str(execinfo.value)
    msg = (
        "but got (Cutlery(name='fork'), Door()) and item in index 1 is not"
        " one of the expected types"
    )
    assert msg in str(execinfo.value)


def test_contents_after() -> None:
    from qmxgraph.decoration_contents import Table, TableRow, TableData

    table = Table(
        [
            TableRow([TableData(['Cutlery'])]),
            TableRow(['Spoons', '2']),
            TableRow(['Knifes', '5']),
            TableRow([TableData(['Bathroom'])]),
            TableRow(['Soap', '2']),
            TableRow(['Toothpaste', '1']),
        ]
    )
    assert table.contents_after('Bathroom') == (
        TableRow(['Soap', '2']),
        TableRow(['Toothpaste', '1']),
    )
    assert table.contents_after('Soap') == (TableRow(['Toothpaste', '1']),)


def test_content_converter() -> None:
    from qmxgraph.decoration_contents import Table, TableRow, TableData, Image

    table = Table(
        [
            dict(tag='tr', contents=['1', 'Cutlery']),  # type:ignore[list-item]
            TableRow(
                [
                    '',
                    'Spoon',
                    dict(  # type:ignore[list-item]
                        tag='td',
                        contents=[
                            dict(
                                tag='img',
                                src='spoon.gif',
                                height=5,
                                width=10,
                            )
                        ],
                    ),
                ]
            ),
        ]
    )
    assert table == Table(
        [
            TableRow(['1', 'Cutlery']),
            TableRow(['', 'Spoon', TableData([Image(src='spoon.gif', height=5, width=10)])]),
        ]
    )
