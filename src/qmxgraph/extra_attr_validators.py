def _tuple_of_impl(inst, attr, value, *, child_types):
    """
    The validator implementation for `tuple_of`.
    The description of `inst`, `attrs`, and `value` comes from:
    http://www.attrs.org/en/stable/examples.html#decorator

    :param inst: The *instance* that’s being validated.
    :param attr: the *attribute* that it’s validating.
    :param value: The value that is passed for it.
    :param tuple[type] child_types: A keyword only argument specifying the
        accepted types.
    :raise TypeError: If the validation fails.
    """
    if isinstance(value, tuple):
        for i, v in enumerate(value):
            if not isinstance(v, child_types):
                msg = (
                    "'{name}' must be a tuple of {types!r} but got"
                    " {value!r} and item in index {i} is not one of"
                    " the expected types"
                )
                msg = msg.format(name=attr.name, types=child_types, value=value, i=i)
                raise TypeError(msg)
    else:
        msg = "'{name}' must be a tuple but got {value!r}"
        raise TypeError(msg.format(name=attr.name, value=value))


def tuple_of(*child_types):
    """
    Creates an validator that accept an item with any type listed or a tuple
    with any of the accept types combination). A tuple is used due it's
    immutable nature.

    :param list[type] child_types:
    :rtype: Callable
    :return: An callable to be used as an validator with the `attr` module.
    ..see: http://www.attrs.org/en/stable/examples.html#callables
    """
    import functools

    return functools.partial(_tuple_of_impl, child_types=child_types)
