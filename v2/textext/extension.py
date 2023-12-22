"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2023 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
import contextlib
import logging
import os
import tempfile
from typing import Any, Callable, Tuple, Union
from utils.log_util import logger
from utils.environment import system_env
from utils.settings import Settings
from elements import TexTextSvgEle, TexTextEleMetaData
from converter import TexToPdfConverter
import inkex

with open(os.path.join(os.path.dirname(__file__), "VERSION"), mode="r", encoding="utf-8") as version_file:
    __version__ = version_file.readline().strip()

FORCE_DEBUG = True


@contextlib.contextmanager
def change_to_temp_dir():
    """
    Context manager creating a temporary directory and changes into it.

    Example:
        with change_to_temp_dir()
            do_something_in_temp_dir()
    """
    with tempfile.TemporaryDirectory(prefix="textext_") as temp_dir:
        orig_dir = os.path.abspath(os.path.curdir)
        try:
            os.chdir(temp_dir)
            yield
        finally:
            os.chdir(orig_dir)


class TexText(inkex.EffectExtension):
    # The exit codes
    EXIT_CODE_OK = 0
    EXIT_CODE_EXPECTED_ERROR = 1
    EXIT_CODE_UNEXPECTED_ERROR = 60

    def __init__(self, prev_exit_code=None):

        # Before we do anything we set up the  loggers.
        # By this we ensure that we catch all errors occurring
        # while calling the ctor of the base class.
        self._setup_logging(previous_exit_code=prev_exit_code)

        super().__init__()

        self.config = Settings(directory=system_env.textext_config_path)

        self.arg_parser.add_argument(
            "--text",
            type=str,
            default=None)  # None signals: Show the GUI (i.e. not invoked from command line)

        self.arg_parser.add_argument(
            "--preamble-file",
            type=str,
            default=TexTextEleMetaData.DEFAULT_PREAMBLE
        )

        # "pdflatex", "lualatex", "xelatex"
        self.arg_parser.add_argument(
            "--tex_command",
            type=str,
            default=TexTextEleMetaData.DEFAULT_TEXCMD
        )

        self.arg_parser.add_argument(
            "--scale-factor",
            type=float,
            default=1.0
        )

        self.arg_parser.add_argument(
            "--font-size-pt",
            type=int,
            default=10
        )

        # "top left", "middle center", "bottom right", etc.
        self.arg_parser.add_argument(
            "--alignment",
            type=str,
            default=TexTextEleMetaData.DEFAULT_ALIGNMENT
        )

    def effect(self) -> Any:
        """ Implements the effect

        Depending on how the extension is called, a GUI is shown or not:
        - If called without the `text` argument, a GUI is shown
        - If called with `text` argument (at least set to "") it is assumed that TexText
          has been called from the command line.
        """
        with logger.debug("TexText.effect"):
            logger.debug(f"Starting TexText with tex-command = `{self.options.tex_command}`,"
                         f"text = `{self.options.text}`, "
                         f"preamble = `{self.options.preamble_file}`, "
                         f"font_size = `{self.options.font_size_pt}`, "
                         f"scale = `{self.options.scale_factor}`, "
                         f"alignment = `{self.options.alignment}`.")

            inkscape_version = self._get_inkscape_version()
            svg_ele_old, meta_data_old = self.get_old()

            if self.options.text:  # Command line call
                if self.options.text == "" and meta_data_old.text is not None:
                    # Recompile node with the settings passed in options
                    new_text = meta_data_old.text
                else:
                    # Create new node with the settings passed in options
                    new_text = self.options.text

                self._convert_to_svg(TexTextEleMetaData(text=new_text,
                                                        preamble=self._normalize_preamble_path(
                                                            self.options.preamble_file),
                                                        scale_factor=self.options.scale_factor,
                                                        tex_command=self.options.tex_command,
                                                        alignment=self.options.alignment,
                                                        stroke_to_path=False,
                                                        jacobian_sqrt=1.0,
                                                        textext_version=__version__,
                                                        inkex_version=inkex.__version__,
                                                        inkscape_version=inkscape_version),
                                     meta_data_old, svg_ele_old)
            else:  # GUI call
                pass

    @staticmethod
    def _normalize_preamble_path(preamble_file: str) -> str:
        """ Returns a valid path to the preamble file.

        Checks if the path specified in preamble_file points to a file on this system.
        A relative path is assumed to be relative to the extensions directory and
        is converted to an absolute one. If the file does not exist, the absolute
        path to the default preamble file of TexText is returned.
        """
        preamble_file_path = os.path.abspath(preamble_file)
        if not os.path.isfile(preamble_file_path):
            preamble_file_path = os.path.join(os.path.dirname(__file__), TexTextEleMetaData.DEFAULT_PREAMBLE)
        return str(preamble_file_path)

    def _convert_to_svg(self, meta_data_new: TexTextEleMetaData,
                        meta_data_old: Union[TexTextEleMetaData, None] = None,
                        svg_ele_old: Union[TexTextSvgEle, None] = None):
        """ Changes into a temporary, converts the text to svg and inserts the rendered svg it into the document

        :param meta_data_new: Metadata holding the information for compiling the text
        :param meta_data_old: The metadata of the old node (set to None if a new node is going to be created)
        :param svg_ele_old: The rendered old node (set to None if a new node is going to be created)
        :raises: TexTextConversionError if compilation failed
        """
        with logger.debug("TexText._convert_to_svg"):
            with logger.debug("args:"):
                for key, value in list(locals().items()):
                    logger.debug(f"{key} = {repr(value)}")

            if not meta_data_new.text:
                logger.debug("no text, return")
                return

            # Convert
            with logger.debug("Converting tex to svg"):
                with change_to_temp_dir():
                    if isinstance(meta_data_new.text, bytes):
                        meta_data_new.text = meta_data_new.text.decode("utf-8")

                    converter = TexToPdfConverter(latex_exe=self.config.
                                                  get(key=f"{meta_data_new.tex_command}-executable",
                                                      default=system_env.
                                                      executable_names[meta_data_new.tex_command][0]),
                                                  inkscape_exe=self.config.
                                                  get(key="inkscape-executable",
                                                      default=system_env.executable_names["inkscape"][0]))
                    converter.tex_to_pdf(meta_data_new.text, meta_data_new.preamble)
                    converter.pdf_to_svg()

                    if meta_data_new.stroke_to_path:
                        converter.stroke_to_path()

                    self.svg: inkex.SvgDocumentElement
                    tt_node = TexTextSvgEle(converter.tmp("svg"), self.svg.unit)
                    tt_node.set_meta_data(meta_data_new)

            # Place new node in document
            if svg_ele_old is None:
                self._insert_new_node(tt_node, meta_data_new)
            else:
                self._replace_old_node(tt_node, meta_data_new, svg_ele_old, meta_data_old)

            with logger.debug("Saving global settings"):
                # -- Save settings
                self.config["preamble"] = meta_data_new.preamble
                self.config["scale"] = meta_data_new.scale_factor
                self.config["previous_tex_command"] = meta_data_new.tex_command
                self.config.save()

    def _convert_to_png(self, meta_data_new: TexTextEleMetaData,
                        image_set_fcn: Callable[[str], None], use_white_bg: bool) -> None:
        """ Converts text to png and calls a function to display the png somewhere

        :param meta_data_new:
        :param image_set_fcn:
        :param use_white_bg:
        """
        pass

    def _insert_new_node(self, tt_node: TexTextSvgEle, meta_data_new: TexTextEleMetaData):

        self.svg: inkex.SvgDocumentElement

        with logger.debug("Adding new node to document"):
            # Place new nodes in the view center and scale them according to user request
            node_center = tt_node.bounding_box().center
            view_center = self.svg.namedview.center

            # Since Inkscape 1.2 (= extension API version 1.2.0) view_center is in px,
            # not in doc units! Hence, we need to convert the value to the document unit.
            # so the transform is correct later.
            view_center.x = self.svg.uutounit(view_center.x, self.svg.unit)
            view_center.y = self.svg.uutounit(view_center.y, self.svg.unit)

            # Collect all layers incl. the current layers such that the top layer
            # is the first one in the list
            layers = []
            parent_layer = self.svg.get_current_layer()
            while parent_layer is not None:
                layers.insert(0, parent_layer)
                parent_layer = parent_layer.getparent()

            # Compute the transform mapping the view coordinate system onto the
            # current layer
            full_layer_transform = inkex.Transform()
            for layer in layers:
                full_layer_transform @= layer.transform

            # Place the node in the center of the view. Here we need to be aware of
            # transforms in the layers, hence the inverse layer transformation
            tt_node.transform = (-full_layer_transform @  # map to view coordinate system
                                 inkex.Transform(translate=view_center) @  # place at view center
                                 inkex.Transform(scale=meta_data_new.scale_factor) @  # scale
                                 inkex.Transform(translate=-node_center) @  # place node at origin
                                 tt_node.transform  # use original node transform
                                 )

            tt_node.set_meta("jacobian_sqrt", str(tt_node.get_jacobian_sqrt()))

            tt_node.set_none_strokes_to_0pt()

            self.svg.get_current_layer().add(tt_node)

    def _replace_old_node(self, new_node: TexTextSvgEle, meta_data_new: TexTextEleMetaData,
                          old_node: TexTextSvgEle, meta_data_old: TexTextEleMetaData):
        with logger.debug("Replacing node in document"):
            # Rescale existing nodes according to user request
            relative_scale = meta_data_new.scale_factor / meta_data_old.scale_factor
            new_node.align_to_node(old_node, meta_data_new.alignment, relative_scale)

            # If no non-black color has been explicitly set by TeX we copy the color information
            # from the old node so that coloring done in Inkscape is preserved.
            if not new_node.is_colorized():
                new_node.import_group_color_style(old_node)

            parent = old_node.getparent()
            old_id = old_node.get_id()
            parent.remove(old_node)
            parent.append(new_node)
            new_node.set_id(old_id)
            self._copy_style(old_node, new_node)

    @staticmethod
    def _copy_style(old_node, new_node):
        # pylint: disable=unused-argument
        # ToDo: Implement this later depending on the choice of the user (keep Inkscape colors vs. Tex colors)
        return

    def _get_inkscape_version(self):
        try:
            inkscape_version = self.document.getroot().get("inkscape:version")
        except AttributeError as _:
            # Unfortunately when this node comes from an Inkscape document that
            # has never been saved no version attribute is provided :-(
            inkscape_version = "0.0"
        return inkscape_version

    def _setup_logging(self, previous_exit_code=None):
        if FORCE_DEBUG:
            logging.disable(logging.NOTSET)
            logger.debug("Programmatically enforced DEBUG mode.")
        else:
            if previous_exit_code is None:
                logging.disable(logging.NOTSET)
                logger.debug("First run of TexText. Enforcing DEBUG mode.")
            elif previous_exit_code == self.EXIT_CODE_UNEXPECTED_ERROR:
                logging.disable(logging.NOTSET)
                logger.debug("Enforcing DEBUG mode due to unexpected error in previous run.")
            elif previous_exit_code == self.EXIT_CODE_EXPECTED_ERROR:
                logging.disable(logging.DEBUG)
                logger.debug("Extended logging due to expected error in previous run")
            else:
                logging.disable(logging.CRITICAL)  # No logging in case everything went well in previous run

    def get_old(self) -> Tuple[Union[TexTextSvgEle, None], Union[TexTextSvgEle, None]]:
        """

        :return (TexTextEle, TexTextEleMetaData): In case
        """
        self.svg: inkex.SvgDocumentElement

        for node in self.svg.selected.values():

            # TexText node must be a group
            if node.tag_name != 'g':
                continue

            node.__class__ = TexTextSvgEle

            try:
                meta_data = node.get_meta_data()

                logger.debug(f"Old node from TexText {meta_data.textext_version}")
                logger.debug(f"Old node text = {meta_data.text}")
                logger.debug(f"Old node scale = {meta_data.scale_factor}")

                if not meta_data.preamble:
                    logger.debug(f"Using default preamble file `{self.options.preamble_file}`")
                    meta_data.preamble = self.options.preamble_file
                else:
                    logger.debug(f"Using node preamble file `{meta_data.preamble}`")

                # This is very important when re-editing nodes which have been created using
                # TexText <= 0.7. It ensures that the scale factor which is displayed in the
                # TexTextGuiBase dialog is adjusted in such a way that the size of the node
                # is preserved when recompiling the LaTeX code.
                # ("version" attribute introduced in 0.7.1)
                if meta_data.textext_version == TexTextEleMetaData.DEFAULT_TEXTEXT_VERSION:
                    logger.debug("Adjust scale factor for node created with TexText <= 0.7")
                    meta_data.scale_factor *= self.svg.uutounit(1, "pt")

                if meta_data.jacobian_sqrt != 1.0:
                    logger.debug("Adjust scale factor to account transformations in inkscape")
                    meta_data.scale_factor *= node.get_jacobian_sqrt() / meta_data.jacobian_sqrt

                return node, meta_data

            except (TypeError, AttributeError):
                pass

        return None, None
