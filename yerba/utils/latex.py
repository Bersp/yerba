import os
import re
import pkg_resources
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

from .constants import *
from ..defaults import colors

# make colors global variables
for k, v in colors.items():
    globals()[k] = v


def parse_props(props: str):
    props = (props.replace(r"%20", r" ")
                  .replace(r"%22", r'"')
                  .replace(r"%5B", r"[")
                  .replace(r"%5D", r"]"))
    return eval(f"dict({props})")


def paragraph_to_md_nodes(text):
    mdparse = (MarkdownIt("commonmark", {"breaks": True})
               .disable(["emphasis"])
               .parse(text))
    if not mdparse:
        return None

    inlines_nodes = SyntaxTreeNode(mdparse).children[0].children[0].children

    return inlines_nodes


def markdown_to_manim_text_and_props(md_nodes):
    props = []
    idx_submo = []
    out_text = ""

    soft_brake_happend = False

    ii = 0
    for node in md_nodes:
        if node.type == "text":
            out_text += node.content
            ii += 1

            if soft_brake_happend:
                soft_brake_happend = False

        # handle substrings with props
        elif node.type == "link":
            pl = node.attrs['href']
            props.append(parse_props(pl))
            out_text += "{{" + node.children[0].content + "}}"

            idx_submo.append(ii)
            ii += 1

            if soft_brake_happend:
                soft_brake_happend = False

        elif node.type == "softbreak":
            out_text += " "
            soft_brake_happend = True

        else:
            raise ValueError(node)

    return out_text, idx_submo, props


def process_enhanced_text(text):
    m = re.search(r"\[\-\]\(([^]]+)\)\s*$", text)
    if m:
        text = text.replace(m.group(0), "")
        general_props = parse_props(m.group(1))
    else:
        general_props = {}

    md_nodes = paragraph_to_md_nodes(text)
    manim_text, idx_submo, props = markdown_to_manim_text_and_props(md_nodes)
    ismo_props_zip = zip([-1]+idx_submo, [general_props]+props)

    return manim_text, ismo_props_zip

# ---


def add_font_to_preamble(preamble, regular, bold, italic, bold_italic,
                         fonts_path=None):

    if fonts_path is None:
        yerba_font_path = pkg_resources.resource_filename(
            __name__, '../templates/fonts/')
        yerba_regular_font_path = os.path.join(yerba_font_path, regular)
        if os.path.exists(yerba_regular_font_path):
            fonts_path_str = f"Path = {yerba_font_path}"
        else:
            fonts_path_str = ""
    else:
        fonts_path_str = f"Path = {fonts_path}"

    t = f"""
    \n\\setmainfont[
        {fonts_path_str},
        BoldFont = {bold},
        ItalicFont = {italic},
        BoldItalicFont = {bold_italic},
    ]{{{regular}}}\n
    """

    preamble.add_to_preamble(t)


def update_tex_enviroment_using_box(box, font_size, tex_template, xmargin=0):
    tex_template = tex_template.copy()
    pt = box.width/SLIDE_WIDTH * 24/font_size * (820-xmargin)
    tex_template.add_to_preamble(fr"""
        \usepackage{{geometry}}
        \geometry{{papersize={{{pt}pt, 20cm}}}}
    """)
    return tex_template
