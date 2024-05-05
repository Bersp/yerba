from __future__ import annotations
import re
from functools import cached_property
from abc import ABCMeta, abstractmethod
from typing import Iterable
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdit_py_plugins.dollarmath import dollarmath_plugin

from ..base.image import ImageSvg, ImagePDFSvg
from ..base.ptext import Ptex
from ..base.box import Box, NamedBoxes
from ..base.slide import Slide
from ..properties import funcs_from_props
from ..utils.others import define_default_kwargs, LinkedPositions
from ..utils.latex import update_tex_enviroment_using_box, add_font_to_preamble
from ..utils.parser import get_markdownit_nodes
from ..utils.constants import DOWN, LEFT, ORIGIN, SLIDE_WIDTH, SLIDE_HEIGHT
from ..globals import g_ids

from manim import *  # to ensure access to manim from python_yerba


class PresentationTemplateAbstract(metaclass=ABCMeta):
    slide_number: int
    subslide_number: int
    current_slide: Slide

    tex_template: TexTemplate

    def __init__(self, template_params, colors):
        self.template_params = template_params
        self.colors = colors

    @abstractmethod
    def new_slide(self, slide_number: int = None):
        pass

    @abstractmethod
    def add(self, mobjects: VMobject | list[VMobject],
            box: Box | str = None) -> VMobject:
        pass

    @abstractmethod
    def remove(self, mobjects: VMobject | list[VMobject]) -> VMobject:
        pass

    @abstractmethod
    def pause(self) -> VMobject:
        pass

    @abstractmethod
    def apply(self, mobjects: VMobject | list[VMobject]) -> VMobject:
        pass

    @abstractmethod
    def modify(self, mobjects: VMobject | list[VMobject]) -> VMobject:
        pass

    @abstractmethod
    def become(self, mobjects: VMobject | list[VMobject]) -> VMobject:
        pass

    @abstractmethod
    def get_box(self, box: str | Box) -> Box:
        pass

    @abstractmethod
    def render_md(self, node) -> str:
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
            arrange=self.template_params["box.content.arrange"]
        )

        d["full"] = Box.get_full_box(arrange="center")
        d["floating"] = Box.get_full_box(arrange="none")
        m = self.template_params["box.full_with_margins.margins"]
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
        """+"\n" + self.template_params["add_to_preamble"])
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

    def add_latex_text(self, text, box="null", **text_props):
        funcs, text_props = funcs_from_props(text_props,
                                             only_custom_props=True)
        text_props = define_default_kwargs(
            text_props,
            tex_template=self.tex_template,
            tex_environment="justify",
            font_size=self.template_params["text.font_size"],
            color=self.template_params["text.color"],
        )

        box = self.get_box(box)

        text_props["tex_template"] = update_tex_enviroment_using_box(
            box, text_props["font_size"], text_props["tex_template"],
        )

        text_mo = Ptex(text, subslide_number=self.subslide_number,
                       **text_props)

        predefined_box = getattr(text_mo, "box", None)
        if predefined_box is None:
            text_mo.set(box=box)
        else:
            text_mo.set(box=self.get_box(predefined_box))

        for f in funcs:
            f(text_mo)

        self.add(text_mo)

        return text_mo

    def add_latex_math(self, text, box="null", **text_props):
        funcs, text_props = funcs_from_props(text_props,
                                             only_custom_props=True)
        text_props = define_default_kwargs(
            text_props,
            tex_template=self.tex_template,
            tex_environment="align*",
            font_size=self.template_params["math.font_size"],
            color=self.template_params["math.color"],
        )

        box = self.get_box(box)

        math_mo = Ptex(text, subslide_number=self.subslide_number,
                       **text_props)

        predefined_box = getattr(math_mo, "box", None)
        if predefined_box is None:
            math_mo.set(box=box, box_arrange='hcenter')
        else:
            math_mo.set(box=self.get_box(predefined_box))

        for f in funcs:
            f(math_mo)

        self.add(math_mo)

        return math_mo

    def add_image(self, filename, box="active", arrange='hcenter',
                  **img_args):
        funcs, img_args = funcs_from_props(img_args, only_custom_props=True)

        box = self.get_box(box)

        if filename.split('.')[-1].lower() == 'pdf':
            img_mo = ImagePDFSvg(filename, **img_args)
        else:
            img_mo = ImageSvg(filename, **img_args)

        img_mo = img_mo.set(box=box, box_arrange=arrange)
        self.add(img_mo)

        for f in funcs:
            f(img_mo)

        return img_mo

    def add_paragraph(self, text, box="active", **text_props):
        tokens = MarkdownIt("commonmark").use(
            dollarmath_plugin, allow_space=True, double_inline=True
        ).parse(text)
        nodes = SyntaxTreeNode(tokens)[0]

        box = self.get_box(box)

        if nodes.type == "math_block":
            t = self.render_md(nodes)[2:-3].strip()
            return self.add_latex_math(t, box=box, **text_props)
        else:
            nodes = nodes[0]

        mo_vg = VGroup()
        acc_text = ""
        for node in nodes:
            if node.type == "math_inline_double":
                acc_text = acc_text.strip()
                if acc_text:
                    mo = self.add_latex_text(acc_text, box=box, **text_props)
                    mo_vg.add(mo)
                acc_text = ""

                t = self.render_md(node)
                mo = self.add_latex_math(t[2:-3], box=box, **text_props)
                mo_vg.add(mo)
            else:
                acc_text += self.render_md(node)
        if acc_text:
            mo = self.add_latex_text(acc_text, box=box, **text_props)
            mo_vg.add(mo)

        mo_vg.set(box=box)

        return mo_vg

    def python_yerba_block(self, content):
        p = self
        exec("p = self;"+content)

    def md_alternate_block(self, content, arrange=None):
        nodes = get_markdownit_nodes(content)

        content_mo_list = []
        content_mo = []
        add_box = "active"
        for node in nodes:
            if node.type == "hr":
                content_mo_list.append(content_mo)
                content_mo = []
                add_box = "null"
            else:
                mo = self.compute_slide_content(node, box=add_box)
                content_mo.append(mo)
        content_mo_list.append(content_mo)

        vg_track = VGroup(*content_mo_list[0])
        for ii in range(len(content_mo_list)-1):
            self.pause()
            self.remove(content_mo_list[ii])

            box_copy = Box.from_box(content_mo_list[ii][0].box)
            for mo in content_mo_list[ii+1]:
                self.add(mo, box=box_copy)
            self.current_slide.linked_positions.append(
                LinkedPositions(
                    source=content_mo_list[ii+1],
                    destination=vg_track,
                    arrange=arrange or box_copy.arrange
                )
            )
            box_copy.auto_arrange()

    def md_fragment_block(self, content, *args, **properties):
        nodes = get_markdownit_nodes(content)

        assert len(args) == 0, "Fragment blocks only accept keyword arguments"

        if "box" in properties:
            box = properties.pop("box")
        else:
            box = "active"

        for node in nodes:
            self.compute_slide_content(node, box=box, **properties)

    def md_overwrite_block(self, content, *args, **properties):
        assert (
            len(args) == 1 and isinstance(args[0], int)
            and args[0] in g_ids
        ), ("The first argument of an overwrite block "
            "must be a previously defined id")
        id = args[0]
        original_mo_l = g_ids.pop(id)

        nodes = get_markdownit_nodes(content)

        if "box" in properties:
            box_copy = self.get_box(properties.pop("box"))
        else:
            box_copy = Box.from_box(original_mo_l[0].box)

        if "arrange" in properties:
            arrange = properties.pop("arrange")
        else:
            arrange = box_copy.arrange

        new_mo_l = []
        self.remove(original_mo_l)
        for node in nodes:
            mo = self.compute_slide_content(node, box=box_copy, **properties)
            new_mo_l.append(mo)
            g_ids[id].append(mo)
        box_copy.auto_arrange()

        self.current_slide.linked_positions.append(
            LinkedPositions(source=new_mo_l,
                            destination=VGroup(*original_mo_l),
                            arrange=arrange))

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

    # -- QOL functions

    def add_text(self, *args, box="null", **kwargs):
        return self.add_paragraph(*args, box="null", **kwargs)
    
    add_math = add_latex_math
