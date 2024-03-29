from __future__ import annotations
from manim import Tex, Text

from ..utils.latex import process_enhanced_text
from ..utils.others import define_default_kwargs
from ..properties import funcs_from_props
from ..globals import ids


class Ptex(Tex):
    def __init__(self, text, style="regular",
                 subslide_number: int | None = None,
                 **tex_kwargs):

        tex_kwargs = define_default_kwargs(tex_kwargs, font_size=30)
        text, ismo_props_zip = process_enhanced_text(text)

        if style == 'regular':
            super().__init__(text, **tex_kwargs)
        elif style == "bold_italic":
            super().__init__(fr"\textbf{{\textit{{{text}}}}}", **tex_kwargs)
        else:
            try:
                style = {"bold": "textbf", "italic": "textit"}[style]
            except KeyError:
                raise ValueError(
                    "'style' must be 'regular', 'bold', 'italic' or 'bold_italic'"
                )
            super().__init__(fr"\{style}{{{text}}}", **tex_kwargs)

        for imo, props in ismo_props_zip:
            mo = self if imo == -1 else self.submobjects[imo]

            if 'sid' in props:
                props['id'] = props['sid']
                mo.set(box="null")

            if 'id' in props:
                name = props.pop('id')

                if name == 0:
                    ids[name] = [mo]
                else:
                    ids[name].append(mo)

                if subslide_number is not None:
                    mo.origin_subslide_number = subslide_number

            funcs = funcs_from_props(props)
            for f in funcs:
                f(mo)


class Ppango(Text):
    def __init__(self, text, style='regular', **pango_kwargs):
        super().__init__(text, **pango_kwargs)
