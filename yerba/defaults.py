from __future__ import annotations
from manim.mobject.types.vectorized_mobject import VMobject

colors: dict[str, str] = {
    "BLACK": "#2b3339",
    "DARKEST_GRAY":  "#323b41",
    "DARKER_GRAY":  "#3a454a",
    "DARK_GRAY":  "#4c5b6a",
    "GRAY":  "#adbcc1",
    "LIGHTER_GRAY":  "#d8e2e9",
    "LIGHTEST_GRAY":  "#e5eaf0",
    "WHITE":  "#ecf0f4",

    "RED":  "#c95e61",
    "ORANGE":  "#e69875",
    "YELLOW":  "#dbbc7f",
    "GREEN":  "#689c6e",
    "AQUA":  "#73ad9c",
    "BLUE":  "#6f8aa6",
    "PURPLE":  "#b891b0",
}

VMobject.set_default(color=colors["BLACK"])

parser_params: dict[str, bool] = {
    "errors.verbose": False,
    "only_calculate_new_slides": True,
}

template_params: dict[str, str | float | bool] = {
    "add_footer": True,

    "add_to_preamble": "",

    "title.font_size": 40,
    "title.color": colors["BLACK"],
    "title.style": "bold",

    "subtitle.font_size": 30,
    "subtitle.color": colors["BLACK"],
    "subtitle.style": "regular",

    "text.font_size": 30,
    "text.color": colors["BLACK"],

    "math.font_size": 30,
    "math.color": colors["BLACK"],

    "box.new_slide_default": "content",

    "box.full_with_margins.margins": 0.7,
    "box.content.arrange": "top left"

}

box_params: dict[str, float] = {
    "arrange_buff": 0.25,
}


codeblocks_namedict = {
    "python_yerba": ["python yerba", "yerba"],
    "md_alternate": ["md alt", "md alternate",
                     "markdown alt", "markdown alternate",
                     "alt", "alternate"],
    "md_fragment": ["md frag", "md fragment",
                    "markdown frag", "markdown fragment",
                    "frag", "fragment"],
    "md_overwrite": ["md overwrite", "md overw",
                     "markdown overwrite", "markdown overw",
                     "overwrite", "overw"],
}
