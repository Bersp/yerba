from __future__ import annotations
import re
from functools import cached_property
from typing import Any
from manim import (VMobject, VGroup, TexTemplate, Rectangle)
from abc import ABCMeta, abstractmethod

from ..utils.others import define_default_kwargs
from ..utils.latex import update_tex_enviroment_using_box, add_font_to_preamble
from .image import ImageSvg, ImagePDFSvg
from .ptext import Ptex
from .box import Box, NamedBoxes

from ..utils.constants import DOWN, LEFT, ORIGIN, SLIDE_WIDTH, SLIDE_HEIGHT


class PresentationTemplateAbstract(metaclass=ABCMeta):
    slide_number: int
    pvars: dict[str, list]

    tex_template: TexTemplate

    def __init__(self, template_params, colors):
        self.template_params = template_params
        self.colors = colors

    @abstractmethod
    def new_slide(self, slide_number: int = None):
        pass

    @abstractmethod
    def add(self, mobjects: VMobject | list[VMobject]) -> VMobject:
        pass

    @abstractmethod
    def get_box(self, box: str | Box) -> Box:
        pass

    def text(self, text, color=None, font_size=None, style="regular",
             tex_environment="justify", *args, **kwargs):

        if color is None:
            color = self.colors["BLACK"]
        if font_size is None:
            font_size = self.template_params["text.font_size"]

        return Ptex(
            text=text, color=color, font_size=font_size, style=style,
            tex_environment=tex_environment,
            tex_template=self.tex_template, *args, **kwargs
        )


class PresentationTemplateBase(PresentationTemplateAbstract):
    @cached_property
    def named_boxes(self):
        """Group of named boxes"""
        d = {}
        d["title"] = Box.get_top_box(1.7, arrange="center")
        d["footer"] = Box.get_bottom_box(0.5, arrange="center")
        d["left_margin"] = Box.get_left_box(0.7, arrange="center")
        d["right_margin"] = Box.get_right_box(0.7, arrange="center")
        d["content"] = Box.get_inner_box(
            left_box=d["left_margin"],
            right_box=d["right_margin"],
            top_box=d["title"],
            bottom_box=d["footer"],
            arrange="top left"
        )

        d["full"] = Box.get_full_box(arrange="center")
        d["floating"] = Box.get_full_box(arrange="none")
        m = self.template_params["box.margin_full.margin"]
        d["full_with_margins"] = Box.get_full_box(arrange="center").shrink(
            left_gap=m, right_gap=m, top_gap=m, bottom_gap=m,
        )

        nb = NamedBoxes(**d)
        nb.add("new_slide_default",
               getattr(nb, self.template_params["box.new_slide_default"]))
        nb.set_current_box("new_slide_default")

        return nb

    def background(self) -> VMobject | VGroup:
        return Rectangle(width=SLIDE_WIDTH, height=SLIDE_HEIGHT,
                         color=self.colors["WHITE"], fill_opacity=1)

    @cached_property
    def tex_template(self):
        tt = TexTemplate(tex_compiler="xelatex", output_format=".xdv")
        tt.add_to_preamble(r"""
        \usepackage[no-math]{fontspec}
        \usepackage{ragged2e}
        """+"\n"+self.template_params["add_to_preamble"])
        return tt

    def set_main_font(self, regular, bold, italic, bold_italic, fonts_path=None):
        add_font_to_preamble(
            preamble=self.tex_template, regular=regular, bold=bold,
            italic=italic, bold_italic=bold_italic,  fonts_path=fonts_path
        )

    def add_cover(self, title, subtitle=None, author=None):
        self.new_slide(slide_number=0)

        box = self.get_box("full")

        cover_mo = VGroup()

        title = self.text(title, style="bold", font_size=50)

        cover_mo += title
        if subtitle is not None:
            cover_mo += (self.text(subtitle, font_size=40)
                         .next_to(title, DOWN, buff=0.5))

        if author is not None:
            cover_mo += VGroup(
                self.text("Author", style="bold", font_size=30),
                self.text(author, font_size=30)
            ).arrange(DOWN).next_to(cover_mo, DOWN, buff=2.5)

        cover_mo.move_to(ORIGIN)

        cover_mo.set(box=box)
        self.add(cover_mo)

        return cover_mo

    def add_title(self, text):

        box = self.get_box("title")

        title_mo = self.text(
            text, font_size=self.template_params["title.font_size"],
            color=self.template_params["title.color"],
            style=self.template_params["title.style"],
        )

        title_mo.set(box=box)
        self.add(title_mo)

        return title_mo

    def add_subtitle(self, text):
        box = self.get_box("title")

        subtitle_mo = self.text(
            text, font_size=self.template_params["subtitle.font_size"],
            color=self.template_params["subtitle.color"],
            style=self.template_params["subtitle.style"],
        )

        subtitle_mo.set(box=box)
        self.add(subtitle_mo)

        return subtitle_mo

    def add_footer(self, box="footer"):
        if self.slide_number == 0:  # no footer in the cover slide
            return

        box = self.get_box("footer").set_arrange("none")

        footer_mo = (
            self.text(str(self.slide_number), color=self.colors["DARK_GRAY"])
            .move_to(box.get_right())
            .shift(1/2*LEFT)
        )

        footer_mo.set(box=box)
        self.add(footer_mo)

        return footer_mo

    # -- specialized functions (you probably don't want to modify these)

    def add_text(self, text, box="null", **tex_kwargs):
        tex_kwargs = define_default_kwargs(
            tex_kwargs,
            tex_template=self.tex_template,
            tex_environment="justify",
            font_size=self.template_params["text.font_size"],
            color=self.template_params["text.color"],
            pvars=self.pvars
        )

        box = self.get_box(box)

        tex_kwargs["tex_template"] = update_tex_enviroment_using_box(
            box, tex_kwargs["font_size"], tex_kwargs["tex_template"],
        )

        text_mo = Ptex(text, **tex_kwargs)

        predefined_box = getattr(text_mo, "box", None)
        if predefined_box is None:
            text_mo.set(box=box)
        else:
            text_mo.set(box=self.get_box(predefined_box))

        self.add(text_mo)

        return text_mo

    def add_math(self, text, box="null", **tex_kwargs):
        tex_kwargs = define_default_kwargs(
            tex_kwargs,
            tex_template=self.tex_template,
            tex_environment="align*",
            font_size=self.template_params["math.font_size"],
            color=self.template_params["math.color"],
            pvars=self.pvars
        )

        box = self.get_box(box)

        math_mo = Ptex(text, **tex_kwargs)

        predefined_box = getattr(math_mo, "box", None)
        if predefined_box is None:
            math_mo.set(box=box, box_arrange='hcenter')
        else:
            math_mo.set(box=self.get_box(predefined_box))

        self.add(math_mo)

        return math_mo

    def add_image(self, filename, box="active", arrange='hcenter',
                  **img_args):

        box = self.get_box(box)

        if filename.split('.')[-1].lower() == 'pdf':
            img_mo = ImagePDFSvg(filename, **img_args)
        else:
            img_mo = ImageSvg(filename, **img_args)

        img_mo = img_mo.set(box=box, box_arrange=arrange)
        self.add(img_mo)

        return img_mo

    def add_paragraph(self, text, box="active", **tex_kwargs):
        math_mode_re = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
        mm_text = re.finditer(math_mode_re, text)
        mm_idx = sum([[m.start(), m.end()] for m in mm_text], [])

        if not mm_idx:
            return self.add_text(text, box=box, **tex_kwargs)

        mo_vgroup = VGroup()

        start_with_text = text[:mm_idx[0]]
        if start_with_text:
            mo = self.add_text(start_with_text, box=box, **tex_kwargs)
            mo_vgroup.add(mo)

        for i, (sta, end) in enumerate(zip(mm_idx, mm_idx[1:]+[None])):
            if i % 2 == 0:
                t = text[sta:end].replace("$$", "")
                mo = self.add_math(t, box=box, **tex_kwargs)
            else:
                t = text[sta:end]
                if t != "\n":
                    mo = self.add_text(text[sta:end], box=box, **tex_kwargs)
                else:
                    continue

            mo_vgroup.add(mo)

        return mo_vgroup

    def vspace(self, size=0.25):
        box = self.get_box("active")

        vspace_mo = (Rectangle(height=size, width=box.width)
                     .set_stroke(opacity=0).set(fill_opacity=0))
        vspace_mo.set(box=box)
        self.add(vspace_mo)

        return vspace_mo

    def do_after_create_new_slide(self, **kwargs):
        kwargs = define_default_kwargs(
            kwargs,
            add_footer=False
        )
        if self.template_params["add_footer"]:
            self.add_footer()
