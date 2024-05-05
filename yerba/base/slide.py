from __future__ import annotations
from manim import Mobject, VGroup, Rectangle
from collections.abc import Iterable, Callable

from ..defaults import colors
from ..utils.constants import (
    SLIDE_HEIGHT, SLIDE_WIDTH, UP, LEFT, RIGHT, ORIGIN
)
from ..utils.others import (
    restructure_list_to_exclude_certain_family_members, LinkedPositions
)
from .box import Box
from .image import ImageSvg, ImagePDFSvg
from manim_mobject_svg import *


class SubSlide:
    def __init__(self, slide_number: int, subslide_number: int,
                 background: Mobject | VGroup | None = None) -> None:
        """
        Initialize a SubSlide object.

        Parameters
        ----------
        slide_number : int
            The slide number.
        subslide_number : int
            The subslide number.
        background : Mobject, optional
            Custom background (not implemented).
        """

        self.slide_number = slide_number
        self.subslide_number = subslide_number
        self.mobjects = VGroup()

        if background is None:
            background = Rectangle(width=SLIDE_WIDTH, height=SLIDE_HEIGHT,
                                   color=colors["WHITE"],
                                   fill_opacity=1)
        self.mobjects.add(background.set_z_index(-2))

        self.title: str | None = None
        self.subtitle: str | None = None

    def add(self, mobjects) -> None:
        """Add one or more mobjects to the subslide."""
        self.mobjects.add(*mobjects)

    def remove(self, mobjects) -> None:
        """Remove specified mobjects from the subslide."""
        new_l = restructure_list_to_exclude_certain_family_members(
            self.mobjects, mobjects)
        self.mobjects = VGroup(*new_l)

    def write(self) -> None:
        """Write the subslide to an SVG file."""
        out_filename = (f"./media/slides/s{self.slide_number:04g}"
                        f"_subs{self.subslide_number:04g}.svg")

        vec_mobjects = VGroup()
        img_mobjects = []
        pdf_img_mobjects = []

        for mo in self.mobjects:
            if isinstance(mo, ImageSvg) and mo.draft_mode is False:
                img_mobjects.append(mo)
            elif isinstance(mo, ImagePDFSvg) and mo.draft_mode is False:
                pdf_img_mobjects.append(mo)
            else:
                vec_mobjects += mo

        vec_mobjects.to_svg(out_filename, crop=False)

        for img in img_mobjects:
            # TODO(bersp): Figure out how to do this without coping the img
            # shutil.copyfile(img.filename, f"./media/slides/{img.basename}")
            self._write_img(out_filename, img.get_svg_str())

        for pimg in pdf_img_mobjects:
            self._write_img(out_filename, pimg.get_svg_str())

    def _write_img(self, svg_file, svg_str):
        with open(svg_file, 'r') as f:
            t = f.read()
        t = t.replace(r"</svg>", f"{svg_str}\n</svg>")
        with open(svg_file, 'w') as f:
            f.write(t)


class Slide:
    def __init__(self, slide_number: int, background=None) -> None:
        """
        Initialize a Slide object.

        Parameters
        ----------
        slide_number : int
            The slide number.
        """

        self.slide_number: int = slide_number
        self.subslide_number: int = 0

        self.subslides: list[SubSlide] = [
            SubSlide(slide_number, self.subslide_number, background=background)
        ]

        self.linked_positions: list[LinkedPositions] = []
        self.boxes: list[Box] = []

    def add_new_subslide(self, n=1, background=None) -> None:
        """
        Generate a new subslide with the same content as the last one.
        """
        if isinstance(n, int):
            for _ in range(n):
                self.subslide_number += 1
                s = SubSlide(self.slide_number, self.subslide_number,
                             background=background)
                s.add(self.subslides[-1].mobjects)

                self.subslides.append(s)
        else:
            raise TypeError("'n' must be an int")

    def add_to_subslide(self, mobjects: list, idx=-1) -> list:
        """
        Add mobjects to a subslide.

        Parameters
        ----------
        mobjects : mobject(s)
            One or more mobjects to add.
        idx : int, optional
            Index of the subslide to add to. (Default is -1, which refers to the last subslide)
        """

        to_add = []
        for mo in mobjects:
            box = self._get_box_if_already_exists(mo.box)
            if not box.is_null:
                mo.origin_subslide_number = self.subslide_number
                box.add(mo)
                to_add.append(mo)

        self._add_to_subslide(to_add, idx)

        return mobjects

    def remove_from_subslide(self, mobjects, idx=-1) -> None:
        """
        TODO(bersp): DOC
        """

        return self._remove_from_subslide(mobjects, idx=-1)

    def write(self) -> None:
        """
        Arrange mobjects in their boxes and write the all subslides to SVG files.
        """

        for box in self.boxes:
            box.auto_arrange()

        self.arrange_linked_positions()

        for ss in self.subslides:
            ss.write()

    def arrange_linked_positions(self):
        for lmp in self.linked_positions:
            if isinstance(lmp.source, list):
                src_list = lmp.source
            else:
                src_list = [lmp.source]
            dst = lmp.destination

            if lmp.arrange == "dest":
                arrange = dst[0].box.arrange
            elif isinstance(lmp.arrange, Box):
                arrange = lmp.arrange.arrange
            else:
                arrange = lmp.arrange

            assert isinstance(arrange, str)

            if arrange == "center":
                VGroup(*src_list).align_to(dst, UP)
            elif arrange == "relative center":
                VGroup(*src_list).move_to(dst)
            else:
                d1, d2 = arrange.split(" ")
                alignment = ORIGIN.copy()
                if d1 == "top":
                    alignment += UP
                if d2 == "left":
                    alignment += LEFT
                elif d2 == "right":
                    alignment += RIGHT
                VGroup(*src_list).align_to(dst, alignment)

    def _add_to_subslide(self, mobjects, idx=-1):
        self.subslides[idx].add(mobjects)

    def _remove_from_subslide(self, mobjects, idx=-1):
        self.subslides[idx].remove(mobjects)

    def _replace_from_last_subslide(self, old_mobject, new_mobject):
        self._remove_from_subslide(old_mobject, idx=-1)
        self._add_to_subslide(new_mobject, idx=-1)

    def _get_box_if_already_exists(self, box):
        """
        Get box if exists in self.boxes, add to it if not.
        """
        if not isinstance(box, Box):
            raise TypeError(f"box must be a Box instance, not {box!r}")
        for b in self.boxes:
            if b == box:
                return b
        else:
            self.boxes.append(box)
            return box
