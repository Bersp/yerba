from __future__ import annotations
from manim import Mobject, VGroup, Rectangle
from collections.abc import Iterable, Callable

from ..defaults import colors
from ..properties import funcs_from_props
from ..utils.constants import SLIDE_HEIGHT, SLIDE_WIDTH
from ..utils.others import restructure_list_to_exclude_certain_family_members
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

        self.subslide_number: int = 0
        self.subslides: list[SubSlide] = [
            SubSlide(slide_number, self.subslide_number, background=background)
        ]
        self.slide_number: int = slide_number
        self.following_mobjects: list[tuple[Mobject, Mobject]] = []
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

    def apply_func_to_mobject(self, mobject, funcs, position="original",
                              f_args=None, f_kwargs=None) -> Mobject:
        """
        Apply a function to a mobject.

        Parameters
        ----------
        mobject : mobject(s)
            The mobject to modify.
        func : callable
            The function to apply to the mobject.
        f_args, f_kwargs :
            Arguments of func

        Returns
        -------
        mobject
            The modified mobject.
        """
        if f_args is None:
            f_args = []
        if f_kwargs is None:
            f_kwargs = {}

        modified_mobject = mobject.copy()
        if isinstance(funcs, Callable):
            funcs(modified_mobject, *f_args, **f_kwargs)
        elif isinstance(funcs, Iterable):
            for f in funcs:
                f(modified_mobject, *f_args, **f_kwargs)
        else:
            raise TypeError("'func' must be callable or list of callables")

        self._replace_from_last_subslide(mobject, modified_mobject)
        if position == "original":
            self.following_mobjects.append((modified_mobject, mobject))
        elif position == "modified":
            mobject.box.replace(mobject, modified_mobject)
            self.following_mobjects.append((mobject, modified_mobject))
        elif position == "independent":
            pass
        else:
            raise ValueError(
                f"'position' must be 'original' or 'independent' not {repr(position)}")

        return modified_mobject

    def modify_mobject_props(self, mobject, **props) -> Mobject:
        """
        Modify properties of a mobject,

        Parameters
        ----------
        mobject : mobject(s)
            The mobject to modify.
        **props
            Properties to modify.
        """
        funcs = funcs_from_props(props)

        modified_mobject = self.apply_func_to_mobject(
            mobject=mobject,
            funcs=funcs,
        )
        return modified_mobject

    def add_to_subslide(self, mobjects, idx=-1) -> None:
        """
        Add mobjects to a subslide.

        Parameters
        ----------
        mobjects : mobject(s)
            One or more mobjects to add.
        idx : int, optional
            Index of the subslide to add to. (Default is -1, which refers to the last subslide)
        """

        for mo in mobjects:
            box = self._check_if_box_already_exists(mo.box)
            if not box.is_null:
                box.add(mo)
                self._add_to_subslide([mo], idx)

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

        for m_mo in self.following_mobjects:
            m_mo[0].move_to(m_mo[1].get_center())

        for ss in self.subslides:
            ss.write()

    def _add_to_subslide(self, mobjects, idx=-1):
        self.subslides[idx].add(mobjects)

    def _remove_from_subslide(self, mobjects, idx=-1):
        self.subslides[idx].remove(mobjects)

    def _replace_from_last_subslide(self, old_mobject, new_mobject):
        self._remove_from_subslide(old_mobject, idx=-1)
        self._add_to_subslide(new_mobject, idx=-1)

    def _check_if_box_already_exists(self, box):
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
