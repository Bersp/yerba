from __future__ import annotations
from mdformat.renderer import MDRenderer
import yaml
import shutil
import os

import manim
from manim import *  # to ensure access to manim from python_yerba

from .base.presentation import make_presentation_from_template
from .utils.parser import get_slides_md_nodes
from .utils.others import check_dependencies, create_folder_structure
from .defaults import parser_params, template_params, colors

# make colors global variables
for k, v in colors.items():
    globals()[k] = v


def exec_and_handle_exeption(func, msg, error_type="inline",
                             verbose=None,
                             **f_kwargs):
    if verbose is None:
        verbose = parser_params["errors.verbose"]
    try:
        return func(**f_kwargs)
    except BaseException as e:
        if verbose:
            manim.console.print_exception()

        elif error_type == "inline":
            t = (msg.replace(r"%20", r" ")
                 .replace(r"%22", r'"')
                 .replace(r"%5B", r"[")
                 .replace(r"%5D", r"]"))
            manim.logger.error(
                f"There seems to be an error with the following line:\n{t}"
                f"\nError: {e}"
            )
        elif error_type == "custom":
            manim.logger.error(msg+f"\nError: {e}")
        else:
            raise ValueError("'error_type' must be 'inline' or 'custom'")

        quit()


class MainRutine:
    def __init__(self, filename) -> None:
        check_dependencies()
        create_folder_structure()

        self.filename: str = filename
        self.renderer: MDRenderer = MDRenderer()
        self.cover_metadata: dict | None = None

        old_filename = f"./media/.old.{filename}"
        if os.path.exists(old_filename):
            for f in os.listdir("./media/slides/"):
                shutil.move(f"./media/slides/{f}", f"./media/old_slides/{f}")
            slides = get_slides_md_nodes(filename, old_filename)
        else:
            slides = get_slides_md_nodes(filename, None)
        self.slides: list[dict] = slides

        self.template_name: str = "nice"
        self.custom_template_name: str | None = None

    def render_md(self, node):
        return self.renderer.render(node.to_tokens(), {}, {})

    @staticmethod
    def use_backup_slide(slide_number):
        os.system(
            f"find ./media/old_slides/ | grep -i 's{slide_number:04g}_'"
            " | xargs mv -t ./media/slides/"
        )

    def initialize_presentation(self):
        Presentation = exec_and_handle_exeption(
            make_presentation_from_template, error_type="custom",
            msg="There seems to be an error loading the template.",
            template_name=self.template_name,
            custom_template_name=self.custom_template_name
        )
        output_filename = str(os.path.splitext(self.filename)[0])+".pdf"

        p = exec_and_handle_exeption(
            Presentation, error_type="custom",
            msg="There seems to be an error initializing the presentation.",
            output_filename=output_filename,
            template_params=template_params,
            colors=colors
        )
        return p

    def create_new_slide(self, slide_number):
        exec_and_handle_exeption(
            self.p.new_slide, error_type="custom",
            msg="There seems to be an error creating a new slide.",
            slide_number=slide_number
        )

    def compute_title(self, title):
        if title and title.lower() != "notitle":
            title = exec_and_handle_exeption(self.p.add_title,
                                             msg=title, text=title)

    def compute_subtitle(self, node):
        subtitle = node.children[0].content
        subtitle = exec_and_handle_exeption(self.p.add_subtitle,
                                            msg=subtitle, text=subtitle)

    def compute_paragraph(self, node):
        paragraph = self.render_md(node)
        exec_and_handle_exeption(self.p.add_paragraph,
                                 msg=paragraph, text=paragraph)

    def compute_front_matter(self, node):
        metadata = yaml.safe_load(node.content)

        def process_metadata(metadata):
            if "parser_params" in metadata:
                parser_params.update(metadata["parser_params"])

            if "template_params" in metadata:
                template_params.update(metadata["template_params"])

            if "colors" in metadata:
                colors.update(metadata["colors"])

        exec_and_handle_exeption(
            process_metadata,
            msg="There seems to be an error in the medatada.",
            error_type="custom",
            metadata=metadata
        )

        if "cover" in metadata:
            self.cover_metadata = metadata.pop("cover")

        if "template" in metadata:
            self.template_name = metadata.pop("template")

        if "custom_template" in metadata:
            self.custom_template_name = metadata.pop("custom_template")

    def compute_blockquote(self, node):
        if node.children:
            text = node.children[0].children[0].content
        else:
            return

        for t in text.split("\n"):
            if t.strip().startswith("! `"):
                # TODO(bersp): Use regex to identify >!`(.*)`
                command = t.replace("!", "").replace("`", "").strip()
                command = "p = self.p; pvars = self.p.pvars;" + command
                exec_and_handle_exeption(lambda self, c: exec(c),
                                         msg=f">{t}", self=self, c=command)

            elif t.strip().startswith("!"):
                command, *args = (t.replace("!", "").strip()
                                  .split("-", maxsplit=1))
                command = command.strip().replace(" ", "_")

                def exec_command(self, command, args):
                    p = self.p
                    pvars = self.p.pvars
                    if args:
                        locals()[command] = eval(
                            f"self.p.{command}({args[0]})"
                        )
                    else:
                        locals()[command] = eval(f"self.p.{command}()")

                exec_and_handle_exeption(exec_command, msg=f">{t}",
                                         self=self, command=command, args=args)

    def compute_python_yerba(self, node):
        p = self.p
        pvars = self.p.pvars
        exec(node.content)

    def run(self):
        slide0 = self.slides[0]

        if slide0["is_new_slide"]:
            parser_params["only_calculate_new_slides"] = False
            manim.logger.info("Loading configuration")
        else:
            slide0["is_new_slide"] = True
            manim.logger.info("Loading configuration")

        if slide0["content"] and slide0["content"][0].type == "front_matter":
            node = self.slides[0]["content"].pop(0)
            self.compute_front_matter(node)

        # Create Presentation
        self.p = self.initialize_presentation()

        if self.cover_metadata is not None:
            exec_and_handle_exeption(
                self.p.add_cover, error_type="custom",
                msg="There seems to be an error creating the cover.",
                **self.cover_metadata
            )

        for n, slide in enumerate(self.slides):
            slide_number = slide["slide_number"]
            self.p.slide_number = slide_number

            if (parser_params["only_calculate_new_slides"]
                    and not slide["is_new_slide"] and n != 0):
                self.use_backup_slide(slide_number)
                title = slide["title"].children[0].content
                manim.logger.info(f"Loading backup of slide '{title}'")
                continue

            if n != 0:
                title = slide["title"].children[0].content
                manim.logger.info(f"Rendering slide '{title}'")
                self.create_new_slide(slide_number)
                self.compute_title(title)

            for node in slide["content"]:
                if node.type == "heading":
                    if node.tag == "h2":
                        self.compute_subtitle(node)
                    else:
                        manim.logger.error(
                            f"{node.tag} is not implemented in the parser")
                elif node.type == "paragraph":
                    self.compute_paragraph(node)
                elif node.type == "blockquote":
                    self.compute_blockquote(node)
                elif (node.type == "fence" and node.tag == "code"
                      and node.info == "python yerba"):
                    self.compute_python_yerba(node)
                else:
                    pass

        self.p.close()
        for f in os.listdir("./media/old_slides/"):
            os.remove(f"./media/old_slides/{f}")
        shutil.copyfile(self.filename, f"./media/.old.{self.filename}")

        manim.logger.info("Ready")
