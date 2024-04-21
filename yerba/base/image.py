import os
import re
import subprocess
import shutil
from manim import VGroup, Rectangle
from xml.etree import ElementTree
from PIL import Image

from ..utils.constants import SLIDE_X_RAD, SLIDE_Y_RAD, TO_PX, UL
from ..defaults import colors
from ..base.ptext import Ptex


class ImageSvgBase(VGroup):
    # TODO(bersp): Implement .rotate to imgs
    def __init__(self, filename, width, height, draft_mode):

        self.filename = filename
        self.basename = os.path.basename(filename)
        self.draft_mode = draft_mode

        rec = (Rectangle(width=width, height=height)
               .set_stroke(opacity=0)
               .set_fill(color=colors["BLACK"], opacity=0.8))

        if draft_mode:
            tex_filename = filename.replace("_", r"\\_")
            tex_filename = fr"\\texttt{{{tex_filename}}}"
            super().__init__(
                rec,
                Ptex(tex_filename, color=colors["BLACK"]).move_to(
                    rec).set(width=width*0.9)
            )
        else:
            super().__init__(rec)

    def _manim_to_svg_coords(self):
        x0, y0 = self.get_corner(UL)[:2]
        x0 = (SLIDE_X_RAD+x0)*TO_PX
        y0 = (SLIDE_Y_RAD-y0)*TO_PX
        w = self.width*TO_PX
        h = self.height*TO_PX

        return x0, y0, w, h

    def _get_width_and_height(self, width, height,
                              file_width, file_height):

        ERR = ValueError(
            r"width or height must be numbers or percentages like '90%'"
        )

        porcentage_pattern = r"(^\d+(\.\d+)?)%$"

        if isinstance(width, str):
            m = re.match(porcentage_pattern, width)
            if m:
                self.width_units = "box"
                width = float(m[1])/100
            else:
                raise ERR

        if isinstance(height, str):
            m = re.match(porcentage_pattern, height)
            if m:
                self.height_units = "box"
                height = float(m[1])/100
            else:
                raise ERR

        if not ((isinstance(width, (int, float)) or width is None) and
                (isinstance(height, (int, float)) or height is None)):
            raise ERR

        if width is not None and height is None:
            height = file_height/file_width*width
        elif width is None and height is not None:
            width = file_width/file_height*height
        else:
            raise ValueError(
                "You have to specify either 'width' or 'height', not both")

        return width, height


class ImageSvg(ImageSvgBase):
    def __init__(self, filename, width=None, height=None,
                 draft_mode=False, **_):

        fw, fh = Image.open(filename).size
        width, height = self._get_width_and_height(width, height, fw, fh)

        super().__init__(filename, width, height, draft_mode)

    def get_svg_str(self):
        x0, y0, w, h = self._manim_to_svg_coords()
        img_base64 = (
            subprocess.run(["base64", self.filename],
                           stdout=subprocess.PIPE)
            .stdout.decode("utf-8").replace("\n", "")
        )
        s = (f'<image width="{w}" height="{h}" x="{x0}" y="{y0}" '
             f'href="data:image/png;base64,{img_base64}"/>')

        return s


class ImagePDFSvg(ImageSvgBase):
    def __init__(self, filename, width=None, height=None,
                 backend='poppler', draft_mode=False, **_):
        if not shutil.which("inkscape"):
            raise FileNotFoundError("Inkscape is required to use PDF images.")

        svg_str_raw = self._get_svg_str_raw(filename, backend)
        self.xml_tree = ElementTree.fromstring(svg_str_raw)

        fw = float(self.xml_tree.get('width').replace("pt", ""))
        fh = float(self.xml_tree.get('height').replace("pt", ""))
        width, height = self._get_width_and_height(width, height, fw, fh)

        super().__init__(filename, width, height, draft_mode)

    def get_svg_str(self):
        x0, y0, w, h = self._manim_to_svg_coords()

        self.xml_tree.set("x", str(x0))
        self.xml_tree.set("y", str(y0))
        self.xml_tree.set("width", str(w))
        self.xml_tree.set("height", str(h))

        s = ElementTree.tostring(self.xml_tree, encoding='unicode')
        return s

    def _get_svg_str_raw(self, filename, backend):
        assert backend == "poppler" or backend == "internal", (
            "Backend must be 'poppler' or 'internal'"
        )
        opts = ["--export-plain-svg",
                "--export-type=svg",
                "--export-filename=-"]
        if backend == "poppler":
            opts.append("--pdf-poppler")
        s = subprocess.run(["inkscape", *opts, filename],
                           stdout=subprocess.PIPE, stderr=open(os.devnull, "w")
                           ).stdout.decode("utf-8")

        return s
