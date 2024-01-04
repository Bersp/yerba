from __future__ import annotations
import numpy as np
from manim import VMobject, VGroup, Rectangle

from ..defaults import box_params, colors
from ..utils.constants import (
    UP, DOWN, LEFT, RIGHT, ORIGIN, SLIDE_HEIGHT, SLIDE_WIDTH,
    LEFT_EDGE, RIGHT_EDGE, SLIDE_X_RAD, SLIDE_Y_RAD, TOP_EDGE, BOTTOM_EDGE
)
from ..utils.others import (restructure_list_to_exclude_certain_family_members,
                            replace_in_list)


class Box():
    def __init__(self, center: np.ndarray,
                 width: float, height: float, arrange: str | None = "top left",
                 arrange_buff: float = box_params["arrange_buff"],
                 is_null: bool = False):
        self.center = center
        self.width = width
        self.height = height
        self.arrange = None if arrange == "none" else arrange
        self.arrange_buff = arrange_buff
        self.is_null = is_null

        self.grid: dict[str, Box] | None = None
        self.mobjects: list = []

    @classmethod
    def from_vertex(cls, tl_vertex: tuple[float, float],
                    br_vertex: tuple[float, float], **kwargs):
        top_edge, left_edge = tl_vertex
        bottom_edge, right_edge = br_vertex
        center = np.array(
            [(right_edge+left_edge)/2, (top_edge+bottom_edge)/2, 0])
        width = right_edge-left_edge
        height = top_edge-bottom_edge
        return cls(center, width, height, **kwargs)

    @classmethod
    def get_full_box(cls, arrange):
        return cls(ORIGIN, SLIDE_WIDTH, SLIDE_HEIGHT, arrange=arrange)

    @classmethod
    def get_left_box(cls, width, *, arrange):
        return cls(LEFT_EDGE+RIGHT*width/2, width, SLIDE_HEIGHT,
                   arrange=arrange)

    @classmethod
    def get_right_box(cls, width, *, arrange):
        return cls(RIGHT_EDGE+LEFT*width/2, width, SLIDE_HEIGHT,
                   arrange=arrange)

    @classmethod
    def get_top_box(cls, height, *, arrange):
        return cls(TOP_EDGE+DOWN*height/2, SLIDE_WIDTH, height,
                   arrange=arrange)

    @classmethod
    def get_bottom_box(cls, height, *, arrange):
        return cls(BOTTOM_EDGE+UP*height/2, SLIDE_WIDTH, height,
                   arrange=arrange)

    @classmethod
    def get_inner_box(cls, *, left_box=None, right_box=None,
                      top_box=None, bottom_box=None, arrange):

        lg = SLIDE_X_RAD + left_box.center[0] + left_box.width/2 \
            if left_box else 0
        rg = SLIDE_X_RAD - right_box.center[0] + right_box.width/2 \
            if right_box else 0
        tg = SLIDE_Y_RAD - top_box.center[1] + top_box.height/2 \
            if top_box else 0
        bg = SLIDE_Y_RAD + bottom_box.center[1] + bottom_box.height/2 \
            if bottom_box else 0

        box = cls.get_full_box(arrange)
        box.shrink(left_gap=lg, right_gap=rg, top_gap=tg, bottom_gap=bg)

        return box

    @classmethod
    def get_null_box(cls):
        return cls(ORIGIN, SLIDE_WIDTH, SLIDE_HEIGHT, is_null=True)

    @staticmethod
    def merge_boxes(boxes, arrange):
        if len(boxes) == 1:
            return boxes[0]
        left_edge = min([b.center[0]-b.width/2 for b in boxes])
        right_edge = max([b.center[0]+b.width/2 for b in boxes])
        top_edge = max([b.center[1]+b.height/2 for b in boxes])
        bottom_edge = min([b.center[1]-b.height/2 for b in boxes])

        return Box.from_vertex(tl_vertex=(top_edge, left_edge),
                               br_vertex=(bottom_edge, right_edge),
                               arrange=arrange)

    def add(self, mobject) -> None:
        if hasattr(mobject, "width_units") and mobject.width_units == "box":
            mobject.set(width=self.width*mobject.width)
        if hasattr(mobject, "height_units") and mobject.height_units == "box":
            mobject.set(height=self.height*mobject.height)

        self.mobjects.append(mobject)

    def remove(self, mobjects):
        """Remove specified mobjects from the box."""
        new_l = restructure_list_to_exclude_certain_family_members(
            self.mobjects, mobjects)
        self.mobjects = new_l

    def replace(self, old_mo, new_mo):
        """Remove specified mobjects from the box."""
        replace_in_list(self.mobjects, old_mo, new_mo)

    def remove_all_mobjects(self) -> None:
        self.mobjects = []

    def auto_arrange(self) -> None:
        """TODO(bersp): DOC"""
        if self.arrange is None or len(self.mobjects) == 0 or self.is_null:
            return

        centers = [mo.get_center() for mo in self.mobjects]

        if self.arrange == "center":
            (VGroup(*self.mobjects)
             .arrange(direction=DOWN, buff=self.arrange_buff)
             .move_to(self.center))
        elif self.arrange == "relative center":
            (VGroup(*self.mobjects)
             .move_to(self.center))
        elif self.arrange == "top center":
            (VGroup(*self.mobjects)
             .arrange(DOWN, buff=self.arrange_buff)
             .next_to(self.get_top(), DOWN, buff=0))
        elif self.arrange == "top left":
            (VGroup(*self.mobjects)
             .arrange(DOWN, buff=self.arrange_buff, aligned_edge=LEFT)
             .next_to(self.get_corner(LEFT, UP), DOWN+RIGHT, buff=0))
        elif self.arrange == "top right":
            (VGroup(*self.mobjects)
             .arrange(DOWN, buff=self.arrange_buff, aligned_edge=RIGHT)
             .next_to(self.get_corner(RIGHT, UP), DOWN+LEFT, buff=0))
        elif self.arrange == "center left":
            (VGroup(*self.mobjects)
             .arrange(DOWN, buff=self.arrange_buff, aligned_edge=LEFT)
             .next_to(self.get_left(), RIGHT, buff=0))
        elif self.arrange == "center right":
            (VGroup(*self.mobjects)
             .arrange(DOWN, buff=self.arrange_buff, aligned_edge=RIGHT)
             .next_to(self.get_right(), LEFT, buff=0))
        else:
            ValueError(f"'arrange' {self.arrange!r} is not defined")

        for cent, mo in zip(centers, self.mobjects):

            if hasattr(mo, 'box_arrange'):
                if mo.box_arrange == "center":
                    mo.move_to(self.center)
                elif mo.box_arrange == "hcenter":
                    mo.set_x(self.center[0])
                elif mo.box_arrange == "vcenter":
                    mo.set_y(self.center[1])
                else:
                    ValueError(
                        f"'box arrange' {mo.box_arrange!r} is not defined")

            mo.shift(cent)

    def def_grid(self, grid, hspace=0.5, vspace=0.5,
                 width_ratios=None, height_ratios=None,
                 arrange="self") -> dict[str, Box]:
        """
        TODO(bersp): Handle errors (bad defined grid)
        """

        if arrange == "self":
            arrange = self.arrange

        grid = np.asarray(grid)
        nrows, ncols = grid.shape

        if width_ratios is None:
            width_ratios = np.asarray([1]*ncols)/ncols
        else:
            width_ratios = np.asarray(width_ratios)
            width_ratios = width_ratios/width_ratios.sum()

        if height_ratios is None:
            height_ratios = np.asarray([1]*nrows)/nrows
        else:
            height_ratios = np.asarray(height_ratios)
            height_ratios = height_ratios/height_ratios.sum()

        grid_widths = width_ratios * (self.width-hspace*(ncols-1))
        grid_heights = height_ratios * (self.height-vspace*(nrows-1))

        centers_x = []
        cx = -self.width/2 - hspace
        for gw in grid_widths:
            cx += gw/2 + hspace
            centers_x.append(cx)
            cx += gw/2

        centers_y = []
        cy = self.height/2 + hspace
        for gh in grid_heights:
            cy -= gh/2 + hspace
            centers_y.append(cy)
            cy -= gh/2

        x0, y0, _ = self.center
        subgrid = np.zeros(shape=(nrows, ncols), dtype='object')
        for row, (cy, gh) in enumerate(zip(centers_y, grid_heights)):
            for col, (cx, gw) in enumerate(zip(centers_x, grid_widths)):
                subgrid[row, col] = Box(center=np.array((x0+cx, y0+cy, 0)),
                                        height=gh, width=gw, arrange=arrange)

        self.grid = {}
        for label in np.unique(grid):
            self.grid[label] = Box.merge_boxes(
                subgrid[np.where(grid == label)], arrange=arrange
            )

        return self.grid

    def get_bbox_mo(self, color=colors["BLACK"]) -> VMobject:
        r = (
            Rectangle(height=self.height, width=self.width,
                      fill_color=color, fill_opacity=0.2)
            .set_stroke(color=color, opacity=0.0)
            .move_to(self.center)
            .set_z_index(-1)
        )

        return r

    def get_bbox_grid(self, color=colors["RED"]) -> VMobject:
        if self.grid is None:
            raise ValueError(f"{self!r} has no defined grid")

        o = VGroup()
        for g in self.grid.values():
            o.add(g.get_bbox_mo(color=color))

        return o

    def shrink(self, *, left_gap=0, right_gap=0,
               top_gap=0, bottom_gap=0) -> Box:
        self.width = self.width - (left_gap + right_gap)
        self.height = self.height - (top_gap + bottom_gap)
        self.center = np.array([self.center[0] + (left_gap - right_gap)/2,
                               self.center[1] + (bottom_gap - top_gap)/2,
                               0])
        return self

    # ---

    def set_arrange(self, value):
        self.arrange = None if value == "none" else value
        return self

    def set_arrange_buff(self, value):
        self.arrange_buff = value
        return self

    # ---

    def get_left(self):
        return self.center + self.width/2*LEFT

    def get_right(self):
        return self.center + self.width/2*RIGHT

    def get_top(self):
        return self.center + self.height/2*UP

    def get_bottom(self):
        return self.center + self.height/2*DOWN

    def get_corner(self, x_direction, y_direction):
        return self.center+self.width/2*x_direction+self.height/2*y_direction

    # ---

    def __eq__(self, other_box):
        return (np.all(self.center == other_box.center) and
                self.width == other_box.width and
                self.height == other_box.height and
                self.arrange == other_box.arrange and
                self.arrange_buff == other_box.arrange_buff)

    def __repr__(self):
        c = f"[{self.center[0]:.2g}, {self.center[1]:.2g}]"
        return f"Box(center={c}, width={self.width:.2g}, height={self.height:.2g}, arrange={self.arrange}, is_null={self.is_null})"


class NamedBoxes:
    def __init__(self, **boxes):
        """
        Parameters
        ----------
        **boxes : dict
            Named boxes
        """
        for name, box in boxes.items():
            self.add(name, box)

    def add(self, name, box):
        setattr(self, name, box)

    def set_current_box(self, box_or_box_name):
        """
        TODO(bersp): Documentation.
        TODO(bersp): Handle errors.
        """

        if isinstance(box_or_box_name, Box):
            setattr(self, "active", box_or_box_name)
        else:
            setattr(self, "active", self.__dict__[box_or_box_name])

    def remove_all_mobjects(self):
        """Remove all mobjects from all boxes in the slide layout."""
        for _, box in self.__dict__.items():
            box.remove_all_mobjects()

    def get_bbox_mo(self):
        """Return a VGroup containing all the bounding boxes of the all boxes."""
        o = VGroup()
        for _, box in self.__dict__.items():
            o += box.get_bbox_mo()
        return o

    def __repr__(self):
        s = ''
        for name, box in self.__dict__.items():
            s += f"{name} -> {box}\n"

        return s
