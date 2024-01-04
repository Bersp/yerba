from manim import config
from manim.constants import (
    ORIGIN, UP, DOWN, RIGHT, LEFT, IN, OUT, UL, UR, DL, DR, PI, TAU, DEGREES
)
from manim.typing import Vector3
import numpy as np

SLIDE_WIDTH: float = config.frame_width
SLIDE_HEIGHT: float = config.frame_height
SLIDE_X_RAD: float = config.frame_x_radius
SLIDE_Y_RAD: float = config.frame_y_radius

TOP_EDGE: Vector3 = np.array((0, SLIDE_Y_RAD, 0))
BOTTOM_EDGE: Vector3 = np.array((0, -SLIDE_Y_RAD, 0))
LEFT_EDGE: Vector3 = np.array((-SLIDE_X_RAD, 0, 0))
RIGHT_EDGE: Vector3 = np.array((SLIDE_X_RAD, 0, 0))

TL_CORNER: Vector3 = np.array((-SLIDE_X_RAD,  SLIDE_Y_RAD, 0))
TR_CORNER: Vector3 = np.array((SLIDE_X_RAD,  SLIDE_Y_RAD, 0))
BL_CORNER: Vector3 = np.array((-SLIDE_X_RAD, -SLIDE_Y_RAD, 0))
BR_CORNER: Vector3 = np.array((SLIDE_X_RAD, -SLIDE_Y_RAD, 0))

SLIDE_WIDTH_PX: float = config.pixel_width
SLIDE_HEIGHT_PX: float = config.pixel_height
TO_PX: float = SLIDE_WIDTH_PX/SLIDE_WIDTH
