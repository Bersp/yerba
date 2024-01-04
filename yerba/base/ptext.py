from __future__ import annotations
from manim import Tex, Text

from ..utils.latex import process_enhanced_text
from ..utils.others import define_default_kwargs
from ..properties import funcs_from_props


class Ptex(Tex):
    def __init__(self, text, style="regular",
                 pvars: dict | None = None, **tex_kwargs):
        tex_kwargs = define_default_kwargs(tex_kwargs, font_size=30)

        text, ismo_props_zip = process_enhanced_text(text)

        if style == 'regular':
            super().__init__(text, **tex_kwargs)
        elif style == "bold_italic":
            super().__init__(fr"\textbf{{\textit{{{text}}}}}", **tex_kwargs)
        else:
            style = {"bold": "textbf", "italic": "textit"}[style]
            super().__init__(fr"\{style}{{{text}}}", **tex_kwargs)

        for imo, props in ismo_props_zip:
            mo = self if imo == -1 else self.submobjects[imo]

            if 'svar' in props:
                props['var'] = props['svar']
                mo.set(box="null")

            if 'var' in props:
                name = props.pop('var')
                if pvars is None:
                    raise ValueError("'pvars' is None")

                if name == "_":
                    pvars[name] = [mo]
                else:
                    pvars[name].append(mo)

            funcs = funcs_from_props(props)
            for f in funcs:
                f(mo)


class Ppango(Text):
    def __init__(self, text, style='regular', **pango_kwargs):
        super().__init__(text, **pango_kwargs)
