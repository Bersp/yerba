from __future__ import annotations
import os
import shutil
import importlib
from collections import defaultdict
from typing import Callable, Iterable, Any
from mdformat.renderer import MDRenderer

from manim import Mobject, VMobject, logger

from .slide import Slide
from .box import Box, NamedBoxes
from ..utils.latex import YerbaRenderers
from ..globals import g_ids
from ..utils.others import LinkedPositions, exec_and_handle_exeption
from ..properties import funcs_from_props
from ..defaults import colors, codeblocks_namedict

from manim import *

for k, v in colors.items():
    globals()[k] = v


def make_presentation_from_template(template_name, custom_template_name):
    inh = []

    if custom_template_name is not None:
        try:
            ct = importlib.import_module(custom_template_name)
        except ModuleNotFoundError:
            raise Exception(f"No template named {repr(custom_template_name)}")

        pct = getattr(ct, "PresentationTemplate", None)
        if pct is None:
            logger.error(
                f"'PresentationTemplate' is not defined in {repr(custom_template_name)}")
            quit()
        else:
            inh.append(pct)

    if os.path.exists(template_name+".py"):
        mod = (template_name,)
    else:
        mod = (f".templates.{template_name}", "yerba")
    try:
        t = importlib.import_module(*mod)
    except ModuleNotFoundError:
        raise Exception(f"No template named {repr(template_name)}")

    pt = getattr(t, "PresentationTemplate", None)
    if pt is None:
        logger.error(
            f"'PresentationTemplate' is not defined in {repr(template_name)}")
        quit()
    else:
        inh.append(pt)

    class Presentation(_Presentation, _MdComputations, *inh):
        ...

    return Presentation


class _Presentation:

    # For typing
    named_boxes: NamedBoxes
    background: Callable
    do_after_create_new_slide: Callable

    def __init__(self, output_filename, *args, **kwargs) -> None:
        self.outout_filename = output_filename

        super().__init__(*args, **kwargs)

        self.slide_number: int = -1
        self.subslide_number: int = 0
        self.current_slide: Slide | None = None

        self.renderer: MDRenderer = MDRenderer()
        self.yerba_renderers: YerbaRenderers = YerbaRenderers()

    def new_slide(self, slide_number=None) -> Slide:
        g_ids.clear()
        self.named_boxes.set_current_box('new_slide_default')

        # write last slide before create a new one
        if self.current_slide is not None:
            self.current_slide.write()

        self.named_boxes.remove_all_mobjects()

        if slide_number is None:
            self.slide_number += 1
        else:
            self.slide_number = slide_number

        background = self.background()
        s = Slide(self.slide_number, background=background)
        self.current_slide = s
        self.subslide_number = self.current_slide.subslide_number

        self.do_after_create_new_slide()

        return self.current_slide

    def close(self) -> None:
        if self.current_slide:
            self.current_slide.write()
        os.system(
            f"rsvg-convert -f pdf -o {self.outout_filename} ./media/slides/*.svg"
        )

    def set_box(self, box, arrange=None):
        box = self.get_box(box)
        if arrange is not None:
            box.arrange = arrange
        self.named_boxes.set_current_box(box)

    def get_box(self, box) -> Box:
        err_msg = f"{box!r} is not a named box or a box instance"
        if isinstance(box, Box):
            return box
        elif box == "null":
            return Box.get_null_box()
        elif isinstance(box, str):
            pos, *grid_idx = box.split('.')
            if hasattr(self.named_boxes, pos):
                box = getattr(self.named_boxes, pos)
            else:
                raise ValueError(err_msg)

            if grid_idx:
                return box[grid_idx[0]]
            else:
                return box
        else:
            raise ValueError(err_msg)

    def def_grid(self, *args, from_box="active", **kwargs):
        box = self.get_box(box=from_box)
        g = box.def_grid(*args, **kwargs)

        for subgrid_name, subgrid_box in g.items():
            self.named_boxes.add(subgrid_name, subgrid_box)

    def render_md(self, node):
        return self.renderer.render(
            node.to_tokens(), {
                "parser_extension": [
                    self.yerba_renderers]
            }, {}
        )

    def _apply_func_to_mobject(self, mobject, funcs, position="original",
                               transfer_id=None,
                               f_args=None, f_kwargs=None) -> Mobject:
        """
        Apply a function or a list of functions to a Mobject.

        Parameters
        ----------
        mobject : Mobject
            The Mobject to modify.
        funcs : callable or list of callable
            The function or list of functions to apply to the Mobject.
        position : str, optional
            Specifies where the modified Mobject should be positioned.
        f_args : list, optional
            Positional arguments for the functions.
        f_kwargs : dict, optional
            Keyword arguments for the functions.

        Returns
        -------
        Mobject
            The modified Mobject.
        """
        if self.current_slide is None:
            raise ValueError("The presentation does not have any slide")

        if f_args is None:
            f_args = []
        if f_kwargs is None:
            f_kwargs = {}

        if mobject.origin_subslide_number == self.subslide_number:
            modified_mobject = mobject
        else:
            modified_mobject = mobject.copy()
            if transfer_id:
                assert mobject in g_ids[transfer_id], (
                    f"The original object does not have the id {transfer_id}"
                )
                g_ids[transfer_id].remove(mobject)
                g_ids[transfer_id].append(modified_mobject)

        if isinstance(funcs, Callable):
            funcs(modified_mobject, *f_args, **f_kwargs)
        elif isinstance(funcs, Iterable):
            for f in funcs:
                f(modified_mobject, *f_args, **f_kwargs)
        else:
            raise TypeError("'func' must be callable or list of callables")

        if mobject.origin_subslide_number != self.subslide_number:
            self.current_slide._replace_from_last_subslide(
                mobject, modified_mobject
            )
            if position == "original":
                self.current_slide.linked_positions.append(
                    LinkedPositions(source=modified_mobject,
                                    destination=mobject,
                                    arrange="relative center")
                )
            elif position == "modified":
                mobject.box.replace(mobject, modified_mobject)
                self.current_slide.linked_positions.append(
                    LinkedPositions(source=mobject,
                                    destination=modified_mobject,
                                    arrange="relative center")
                )
            elif position == "independent":
                pass
            else:
                raise ValueError(
                    f"'position' must be 'original', 'modified' or 'independent' not {repr(position)}"
                )

        return modified_mobject

    def _modify_mobject_props(self, mobject, transfer_id=None,
                              **props) -> Mobject:
        """
        Modify properties of a mobject,

        Parameters
        ----------
        mobject : mobject(s)
            The mobject to modify.
        **props
            Properties to modify.
        """
        funcs, _ = funcs_from_props(props)

        modified_mobject = self._apply_func_to_mobject(
            mobject=mobject,
            funcs=funcs,
            transfer_id=transfer_id,
        )
        return modified_mobject

    #  -- slide methods --

    def pause(self, *args, **kwargs):
        if self.current_slide is None:
            raise ValueError("The presentation does not have any slide")
        self.current_slide.add_new_subslide(*args, **kwargs)
        self.subslide_number = self.current_slide.subslide_number
        return None

    def add(self, mobjects, idx=-1, box=None):
        if self.current_slide is None:
            raise ValueError("The presentation does not have any slide")

        if not isinstance(mobjects, list):
            mobjects = [mobjects]

        if box is None:
            for mo in mobjects:
                if not hasattr(mo, "box"):
                    mo.box = self.get_box("active")
        else:
            for mo in mobjects:
                mo.box = self.get_box(box)

        return self.current_slide.add_to_subslide(mobjects, idx)

    def remove(self, mobjects):
        if self.current_slide is None:
            raise ValueError("The presentation does not have any slide")
        return self.current_slide.remove_from_subslide(mobjects)

    def apply(self, mo_or_id, *args, **kwargs):
        if isinstance(mo_or_id, int):
            assert mo_or_id in g_ids, f"id {mo_or_id} is not defined"
            return [self._apply_func_to_mobject(mo, *args, **kwargs)
                    for mo in g_ids[mo_or_id]]
        else:
            return self._apply_func_to_mobject(mo_or_id, *args, **kwargs)

    def modify(self, mo_or_id, *args, **kwargs):
        if isinstance(mo_or_id, int):
            assert mo_or_id in g_ids, f"id {mo_or_id} is not defined"
            return [
                self._modify_mobject_props(
                    mo, transfer_id=mo_or_id, *args, **kwargs
                ) for mo in g_ids[mo_or_id].copy()
            ]
        else:
            return self._modify_mobject_props(mo_or_id,
                                              *args, **kwargs)

    def become(self, old: VMobject | int, new: VMobject | int,
               *args, **kwargs):
        if self.current_slide is None:
            raise ValueError("The presentation does not have any slide")

        if isinstance(old, int):
            assert old in g_ids, f"id {old} is not defined"
            old = g_ids[old][0]
        if isinstance(new, int):
            assert new in g_ids, f"id {new} is not defined"
            new = g_ids[new][0]

        if "position" in kwargs:
            kwargs["position"] = {
                "original": "original",
                "modified": "modified",
                "old": "original",
                "new": "modified",
            }[kwargs["position"]]

        new.origin_subslide_number = self.subslide_number
        return self._apply_func_to_mobject(
            old, lambda old, new: old.become(new),
            f_args=[new], *args, **kwargs
        )

    def hide(self, mo_or_id):
        return self.modify(mo_or_id, hide=True)

    def unhide(self, mo_or_id):
        return self.modify(mo_or_id, hide=False)

    mod = modify
    app = apply
    bec = become


class _MdComputations:

    def compute_slide_content(self, node, **f_kwargs):
        if node.type == "heading":
            if node.tag == "h2":
                return self.compute_subtitle(node, **f_kwargs)
            else:
                logger.error(
                    f"{node.tag} is not implemented in the parser"
                )
        elif node.type == "paragraph" or node.type == "math_block":
            return self.compute_paragraph(node, **f_kwargs)
        elif node.type == "blockquote":
            return self.compute_inline_command(node, **f_kwargs)
        elif (node.type == "fence" and node.tag == "code"):
            for block_type, names in codeblocks_namedict.items():
                node_name, *args = node.info.split('-')
                if node_name.strip() in names:
                    return self.compute_md_block(
                        block_type, node.content, args
                    )
        else:
            pass

    def compute_title(self, title):
        if not title or title.lower() == "notitle":
            return exec_and_handle_exeption(
                self.set_box, msg=title,
                f_kwargs=dict(box="full_with_margins")
            )
        else:
            return exec_and_handle_exeption(
                self.add_title, msg=title, f_kwargs=dict(text=title)
            )

    def compute_subtitle(self, node):
        subtitle = node.children[0].content
        return exec_and_handle_exeption(
            self.add_subtitle, msg=subtitle,
            f_kwargs=dict(text=subtitle)
        )

    def compute_inline_command(self, node, **f_kwargs) -> None:

        if node.children:
            text = node.children[0].children[0].content
        else:
            return [('', None)]

        out = None
        for t in text.split("\n"):
            if t.strip().startswith("! `"):
                # TODO(bersp): Use regex to identify >!`(.*)`
                command = t.replace("!", "").replace("`", "").strip()
                command = "p = self;" + command
                exec_and_handle_exeption(
                    lambda self, c: exec(c),
                    msg=f">{t}",
                    f_kwargs=dict(self=self, c=command)
                )

            elif t.strip().startswith("!"):
                command, *str_args = (t.replace("!", "").strip()
                                      .split("-", maxsplit=1))
                command = command.strip().replace(" ", "_")
                out = exec_and_handle_exeption(
                    self._exec_inline_command, msg=f">{t}",
                    f_kwargs=dict(
                        command=command, str_args=str_args, f_kwargs=f_kwargs
                    )
                )
        return out

    def compute_md_block(self, block_type: str, content: str, args: list[str]):
        self._exec_block_command(block_type=block_type,
                                 content=content, args=args)

    def compute_paragraph(self, node, **f_kwargs):
        paragraph = self.render_md(node)
        return exec_and_handle_exeption(
            self.add_paragraph,
            msg=paragraph, f_kwargs=dict(text=paragraph, **f_kwargs)
        )

    def _exec_inline_command(self, command, str_args, f_kwargs=None):
        f_kwargs = f_kwargs or {}
        p = self
        if str_args:
            return eval(f"self.{command}({str_args[0]}, **f_kwargs)")
        else:
            return eval(f"self.{command}()")

    def _exec_block_command(self, block_type, content, args):
        if args:
            return eval(f"self.{block_type}_block(content, {args[0]})")
        else:
            return eval(f"self.{block_type}_block(content)")
