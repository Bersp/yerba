from __future__ import annotations
import yaml
import shutil
import os

import manim

from .base.presentation import make_presentation_from_template
from .utils.parser import get_slides_md_nodes
from .utils.others import (
    check_dependencies, create_folder_structure, exec_and_handle_exeption
)
from .defaults import parser_params, template_params, colors

# make colors global variables
for k, v in colors.items():
    globals()[k] = v


class MainRutine:
    def __init__(self, filename) -> None:
        check_dependencies()
        create_folder_structure()

        self.filename: str = filename
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
            f_kwargs=dict(
                template_name=self.template_name,
                custom_template_name=self.custom_template_name
            )
        )
        output_filename = str(os.path.splitext(self.filename)[0])+".pdf"

        p = exec_and_handle_exeption(
            Presentation, error_type="custom",
            msg="There seems to be an error initializing the presentation.",
            f_kwargs=dict(
                output_filename=output_filename,
                template_params=template_params,
                colors=colors
            )
        )
        return p

    def create_new_slide(self, slide_number):
        exec_and_handle_exeption(
            self.p.new_slide, error_type="custom",
            msg="There seems to be an error creating a new slide.",
            f_kwargs=dict(slide_number=slide_number)
        )

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
            f_kwargs=dict(metadata=metadata)
        )

        if "cover" in metadata:
            self.cover_metadata = metadata.pop("cover")

        if "template" in metadata:
            self.template_name = metadata.pop("template")

        if "custom_template" in metadata:
            self.custom_template_name = metadata.pop("custom_template")

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
                f_kwargs=self.cover_metadata
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
                self.p.compute_title(title)

            for node in slide["content"]:
                self.p.compute_slide_content(node)

        self.p.close()
        for f in os.listdir("./media/old_slides/"):
            os.remove(f"./media/old_slides/{f}")
        shutil.copyfile(self.filename, f"./media/.old.{self.filename}")

        manim.logger.info("Ready")
