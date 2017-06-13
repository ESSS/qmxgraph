def test_tuple_of_validator():
    from qmxgraph import decoration_contents
    import attr
    import pytest


    @attr.s
    class Cutlery:
        name = attr.ib()

    @attr.s
    class Door:
        pass

    @attr.s
    class Household:
        silverware = attr.ib(validator=decoration_contents.tuple_of(Cutlery))

    Household(silverware=(Cutlery(name='fork'),))

    with pytest.raises(TypeError) as execinfo:
        Household(silverware=Cutlery(name='fork'))
    msg = "'silverware' must be a tuple but got Cutlery(name='fork')"
    assert msg in str(execinfo.value)

    with pytest.raises(TypeError) as execinfo:
        Household(silverware=(Cutlery(name='fork'), Door()))
    assert "'silverware' must be a tuple of " in str(execinfo.value)
    msg = ("but got (Cutlery(name='fork'), Door()) and item in index 1 is not"
           " one of the expected types")
    assert msg in str(execinfo.value)
