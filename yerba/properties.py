from functools import partial
from collections.abc import Callable

from manim.mobject.mobject import Mobject


def hide_func(mo, val):
    if val is True:
        mo.set_opacity(0)
    else:
        mo.set_opacity(1)


properties_set_dict: dict = {
    'opacity': lambda mo, val: mo.set_opacity(val),
    'hide': hide_func
}


def funcs_from_props(props):
    funcs = []
    for custom_prop in properties_set_dict:
        if custom_prop in props:
            f = properties_set_dict[custom_prop]
            val = props.pop(custom_prop)
            funcs.append(partial(f, val=val))

    for prop in list(props.keys()):
        f = getattr(Mobject, prop, None)
        if isinstance(f, Callable):
            val = props.pop(prop)
            funcs.append(
                partial(lambda mo, f, val: f(mo, val), f=f, val=val)
            )

    if props:
        funcs.append(lambda mo: mo.set(**props))

    return funcs
