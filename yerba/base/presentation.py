from __future__ import annotations
import os
import shutil
import importlib
from collections import defaultdict

from manim import VMobject, logger

from .slide import Slide
from .box import Box


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

    class Presentation(*inh):
        def __init__(self, output_filename, *args, **kwargs) -> None:
            self.outout_filename = output_filename

            super().__init__(*args, **kwargs)

            self.slide_number: int = -1
            self.current_slide: Slide | None = None
            self.pvars: dict = defaultdict(list)

        def new_slide(self, slide_number=None) -> Slide:
            self.named_boxes.set_current_box('new_slide_default')
            self.pvars: dict = defaultdict(list)

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

        def def_grid(self, *args, from_box="active", **kwargs):
            box = self.get_box(box=from_box)
            g = box.def_grid(*args, **kwargs)

            for subgrid_name, subgrid_box in g.items():
                self.named_boxes.add(subgrid_name, subgrid_box)

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

        #  -- Slides methods --

        def pause(self, *args, **kwargs):
            if self.current_slide is None:
                raise ValueError("The presentation does not have any slide")
            return self.current_slide.add_new_subslide(*args, **kwargs)

        def add(self, mobjects, idx=-1, box=None):
            if self.current_slide is None:
                raise ValueError("The presentation does not have any slide")

            if not isinstance(mobjects, list):
                mobjects = [mobjects]

            if box is None:
                for mo in mobjects:
                    if not hasattr(mo, 'box'):
                        mo.box = self.get_box("active")
            else:
                for mo in mobjects:
                    mo.box = self.get_box(box)

            return self.current_slide.add_to_subslide(mobjects, idx)

        def remove(self, *args, **kwargs):
            if self.current_slide is None:
                raise ValueError("The presentation does not have any slide")
            return self.current_slide.remove_from_subslide(*args, **kwargs)

        def apply(self, mo_or_pvar, *args, **kwargs):
            if self.current_slide is None:
                raise ValueError("The presentation does not have any slide")

            if isinstance(mo_or_pvar, str) and mo_or_pvar in self.pvars:
                return [self.current_slide.apply_func_to_mobject(mo, *args, **kwargs)
                        for mo in self.pvars[mo_or_pvar]]
            else:
                return self.current_slide.apply_func_to_mobject(mo_or_pvar, *args, **kwargs)

        def modify(self, mo_or_pvar, *args, **kwargs):
            if self.current_slide is None:
                raise ValueError("The presentation does not have any slide")

            if isinstance(mo_or_pvar, str) and mo_or_pvar in self.pvars:
                return [self.current_slide.modify_mobject_props(mo, *args, **kwargs)
                        for mo in self.pvars[mo_or_pvar]]
            else:
                return self.current_slide.modify_mobject_props(mo_or_pvar, *args, **kwargs)

        def become(self, old: VMobject | str, new: VMobject | str,
                   *args, **kwargs):
            if self.current_slide is None:
                raise ValueError("The presentation does not have any slide")

            if isinstance(old, str) and old in self.pvars:
                old = self.pvars[old][0]
            if isinstance(new, str) and new in self.pvars:
                new = self.pvars[new][0]

            if "position" in kwargs:
                kwargs["position"] = {
                    "original": "original",
                    "modified": "modified",
                    "old": "original",
                    "new": "modified",
                }[kwargs["position"]]

            return self.current_slide.apply_func_to_mobject(
                old, lambda old, new: old.become(new),
                f_args=[new], *args, **kwargs
            )

        def hide(self, mo_or_pvar):
            return self.modify(mo_or_pvar, hide=True)

        def unhide(self, mo_or_pvar):
            return self.modify(mo_or_pvar, hide=False)

        mod = modify
        app = apply
        bec = become

    return Presentation
