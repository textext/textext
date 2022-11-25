"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
import hashlib
import logging
import logging.handlers
import math
import re
import os
import platform
import uuid
import subprocess
from copy import deepcopy
from .environment import system_env
from .log_util import setup_logging
from .settings import Settings, Cache
from .utility import change_to_temp_dir
from .errors import TexTextCommandNotFound, TexTextCommandFailed, TexTextConversionError
from .texoutparse import LatexLogParser

# Open logger before accessing Inkscape modules, so we can catch properly any errors thrown by them
logger, log_console_handler = setup_logging(logfile_dir=os.path.join(system_env.textext_logfile_path),
                                            logfile_name="textext.log", cached_console_logging=True)
import inkex  # noqa # pylint: disable=wrong-import-position,wrong-import-order
from lxml import etree  # noqa # pylint: disable=wrong-import-position,wrong-import-order

EXIT_CODE_OK = 0
EXIT_CODE_EXPECTED_ERROR = 1
EXIT_CODE_UNEXPECTED_ERROR = 60
TEXTEXT_NS = "http://www.iki.fi/pav/software/textext/"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ID_PREFIX = "textext-"
NSS = {
    "textext": TEXTEXT_NS,
    "svg": SVG_NS,
    "xlink": XLINK_NS,
}

with open(os.path.join(os.path.dirname(__file__), "VERSION"), mode="r", encoding="utf-8") as version_file:
    __version__ = version_file.readline().strip()


# ------------------------------------------------------------------------------
# Inkscape plugin functionality
# ------------------------------------------------------------------------------
class TexText(inkex.EffectExtension):

    DEFAULT_ALIGNMENT = "middle center"
    DEFAULT_TEXCMD = "pdflatex"
    DEFAULT_PREAMBLE = "default_packages.tex"

    def __init__(self):

        self.config = Settings(directory=system_env.textext_config_path)
        self.cache = Cache(directory=system_env.textext_config_path)
        previous_exit_code = self.cache.get("previous_exit_code", None)

        if previous_exit_code is None:
            logging.disable(logging.NOTSET)
            logger.debug("First run of TexText. Enforcing DEBUG mode.")
        elif previous_exit_code == EXIT_CODE_OK:
            logging.disable(logging.CRITICAL)
        elif previous_exit_code == EXIT_CODE_UNEXPECTED_ERROR:
            logging.disable(logging.NOTSET)
            logger.debug(f"Enforcing DEBUG mode due to previous exit code `{previous_exit_code}`")
        else:
            logging.disable(logging.DEBUG)

        logger.debug("TexText initialized")
        with open(__file__, "rb") as fhl:
            logger.debug(f"TexText version = {repr(__version__)} (md5sum = {hashlib.md5(fhl.read()).hexdigest()}")
        logger.log_system_info()

        super().__init__()

        self.arg_parser.add_argument(
            "--text",
            type=str,
            default=None)

        self.arg_parser.add_argument(
            "--preamble-file",
            type=str,
            default=self.config.get('preamble', self.DEFAULT_PREAMBLE))

        self.arg_parser.add_argument(
            "--scale-factor",
            type=float,
            default=self.config.get('scale', 1.0)
        )

        self.arg_parser.add_argument(
            "--alignment",
            type=str,
            default=self.DEFAULT_ALIGNMENT
        )

        self.arg_parser.add_argument(
            "--tex_command",
            type=str,
            default=self.DEFAULT_TEXCMD
        )

    def effect(self):
        """Perform the effect: create/modify TexText objects"""
        with logger.debug("TexText.effect"):

            # Find root element
            old_svg_ele, old_meta_data = self.get_old()

            # Ask for TeX code via GUI if no text is passed via command line argument
            if self.options.text is None:
                old_meta_data.preamble = self.check_preamble_file(old_meta_data.preamble)

                def save_callback_new(_new_node_meta_data):
                    return self.do_convert(_new_node_meta_data, old_meta_data, old_svg_ele)

                def preview_callback_new(_new_node_meta_data, _preview_callback, _white_bg):
                    return self.preview_convert(_new_node_meta_data, _preview_callback, _white_bg)

                with logger.debug("Run TexText GUI"):
                    from .gui import TexTextGui  # pylint: disable=import-outside-toplevel
                    tt_gui = TexTextGui(version_str=__version__, node_meta_data=old_meta_data, config=self.config)
                    self.config = tt_gui.show(save_callback_new, preview_callback_new)

                with logger.debug("Saving global GUI settings"):
                    self.config.save()

            # when run from command line
            else:
                # In case TT has been called with --text="" the old node is
                # just re-compiled if one exists
                if self.options.text == "" and old_meta_data.text is not None:
                    new_text = old_meta_data.text
                else:
                    new_text = self.options.text
                self.do_convert(TexTextEleMetaData(new_text, self.options.preamble_file, self.options.scale_factor,
                                                   self.options.tex_command, self.options.alignment,
                                                   False, 1.0, __version__),
                                old_meta_data, old_svg_ele)

    def do_convert(self, new_node_meta_data, old_node_meta_data, old_svg_node):
        """
        Does the conversion using the selected converter.

        :param new_node_meta_data:
        :type new_node_meta_data: TexTextEleMetaData

        :param old_node_meta_data:
        :type old_node_meta_data: TexTextEleMetaData

        :param old_svg_node:
        :type old_svg_node: TexTextElement

        :return:
        """
        with logger.debug("TexText.do_convert"):
            with logger.debug("args:"):
                for key, value in list(locals().items()):
                    logger.debug(f"{key} = {repr(value)}")

            if not new_node_meta_data.text:
                logger.debug("no text, return")
                return

            try:
                inkscape_version = self.document.getroot().get('inkscape:version')
            except AttributeError as _:
                # Unfortunately when this node comes from an Inkscape document that
                # has never been saved no version attribute is provided :-(
                inkscape_version = "0.0"
            new_node_meta_data.inkscape_version = inkscape_version
            new_node_meta_data.inkex_version = inkex.__version__

            # Convert
            with logger.debug("Converting tex to svg"):
                with change_to_temp_dir():
                    if isinstance(new_node_meta_data.text, bytes):
                        new_node_meta_data.text = new_node_meta_data.text.decode('utf-8')

                    converter = TexToPdfConverter(latex_exe=self.config.
                                                  get(f"{new_node_meta_data.tex_command}-executable"),
                                                  inkscape_exe=self.config.
                                                  get("inkscape-executable"))
                    converter.tex_to_pdf(new_node_meta_data.text, new_node_meta_data.preamble)
                    converter.pdf_to_svg()

                    if new_node_meta_data.stroke_to_path:
                        converter.stroke_to_path()

                    tt_node = TexTextElement(converter.tmp("svg"), self.svg.unit)

            tt_node.set_meta_data(new_node_meta_data)

            # Place new node in document
            if old_svg_node is None:
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
                    tt_node.transform = (-full_layer_transform @               # map to view coordinate system
                                         inkex.Transform(translate=view_center) @    # place at view center
                                         inkex.Transform(scale=new_node_meta_data.scale_factor) @  # scale
                                         inkex.Transform(translate=-node_center) @   # place node at origin
                                         tt_node.transform                     # use original node transform
                                         )

                    tt_node.set_meta('jacobian_sqrt', str(tt_node.get_jacobian_sqrt()))

                    tt_node.set_none_strokes_to_0pt()

                    self.svg.get_current_layer().add(tt_node)
            else:
                with logger.debug("Replacing node in document"):
                    # Rescale existing nodes according to user request
                    relative_scale = new_node_meta_data.scale_factor / old_node_meta_data.scale_factor
                    tt_node.align_to_node(old_svg_node, new_node_meta_data.alignment, relative_scale)

                    # If no non-black color has been explicitly set by TeX we copy the color information
                    # from the old node so that coloring done in Inkscape is preserved.
                    if not tt_node.is_colorized():
                        tt_node.import_group_color_style(old_svg_node)

                    self.replace_node(old_svg_node, tt_node)

            with logger.debug("Saving global settings"):
                # -- Save settings
                self.config['preamble'] = new_node_meta_data.preamble
                self.config['scale'] = new_node_meta_data.scale_factor
                self.config["previous_tex_command"] = new_node_meta_data.tex_command
                self.config.save()

    def preview_convert(self, new_node_meta_data, image_set_fcn, use_white_bg):
        """
        Generates a preview PNG of the LaTeX output using the selected converter.

        :param new_node_meta_data: The meta data of the node to be compiled
        :type new_node_meta_data: TexTextEleMetaData

        :param image_set_fcn: A callback to execute with the file path of the generated PNG
        :type image_set_fcn: function

        :param use_white_bg: set background to white if True
        :type use_white_bg: bool
        """
        with logger.debug("TexText.preview"):
            with logger.debug("args:"):
                for key, value in list(locals().items()):
                    logger.debug(f"{key} = {repr(value)}")

            if not new_node_meta_data.text:
                logger.debug("no text, return")
                return

            if isinstance(new_node_meta_data.text, bytes):
                new_node_meta_data.text = new_node_meta_data.text.decode('utf-8')

            with change_to_temp_dir():
                with logger.debug("Converting tex to pdf"):
                    converter = TexToPdfConverter(latex_exe=self.config.
                                                  get(f"{new_node_meta_data.tex_command}-executable"),
                                                  inkscape_exe=self.config.
                                                  get("inkscape-executable"))
                    converter.tex_to_pdf(new_node_meta_data.text, new_node_meta_data.preamble)
                    converter.pdf_to_png(white_bg=use_white_bg)
                    image_set_fcn(converter.tmp('png'))

    def get_old(self):
        """
        Dig out LaTeX code and name of preamble file from old
        TexText-generated objects.

        :return: The digged out svg note and the meta data of the node
        :rtype: (TexTextElement, TexTextEleMetaData)
        """

        for node in self.svg.selected.values():

            # TexText node must be a group
            if node.tag_name != 'g':
                continue

            node.__class__ = TexTextElement

            try:
                meta_data = node.get_meta_data(default_scale=self.config.get("scale", 1.0),
                                               default_alignment=TexText.DEFAULT_ALIGNMENT,
                                               default_texcmd=self.config.get("previous_tex_command",
                                                                              TexText.DEFAULT_TEXCMD))

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
                if meta_data.textext_version == '<=0.7':
                    logger.debug("Adjust scale factor for node created with TexText <= 0.7")
                    meta_data.scale_factor *= self.svg.uutounit(1, "pt")

                if meta_data.jacobian_sqrt != 1.0:
                    logger.debug("Adjust scale factor to account transformations in inkscape")
                    meta_data.scale_factor *= node.get_jacobian_sqrt() / meta_data.jacobian_sqrt

                return node, meta_data

            except (TypeError, AttributeError):
                pass

        return None, TexTextEleMetaData()

    def check_preamble_file(self, preamble_file):
        """
        Check if preamble file exists at the specified absolute path location. If not, check to find
        the file in the default path. If this fails, too, fallback to the default.

        :param preamble_file: The path to the preamble file to be checked
        :type: str

        :return: A valid path to the determined preamble file. If nothing is found, an empty string.
        :rtype: str
        """
        if not os.path.exists(preamble_file):
            logger.debug("Preamble file is NOT found by absolute path")
            preamble_file_guess = os.path.join(os.path.dirname(self.options.preamble_file),
                                               os.path.basename(preamble_file))
            if not os.path.exists(preamble_file_guess):
                logger.debug("Preamble file is NOT found along with configured default preamble file")
                preamble_file_guess = self.options.preamble_file
                if not os.path.exists(preamble_file_guess):
                    logger.debug("Configured default preamble file is also NOT found")
                    preamble_file = os.path.join(os.getcwd(), self.DEFAULT_PREAMBLE)
                else:
                    logger.debug("Using configured preamble file")
                    preamble_file = preamble_file_guess
            else:
                logger.debug("Preamble file is found along with default preamble file")
                preamble_file = preamble_file_guess
        else:
            logger.debug("Preamble file found by absolute path")

        if not os.path.isfile(preamble_file):
            logger.debug("Preamble file is not found")
            preamble_file = ""

        return preamble_file

    def replace_node(self, old_node, new_node):
        """
        Replace an XML node old_node with new_node
        """
        parent = old_node.getparent()
        old_id = old_node.get_id()
        parent.remove(old_node)
        parent.append(new_node)
        new_node.set_id(old_id)
        self.copy_style(old_node, new_node)

    @staticmethod
    def copy_style(old_node, new_node):
        # pylint: disable=unused-argument
        # ToDo: Implement this later depending on the choice of the user (keep Inkscape colors vs. Tex colors)
        return


class TexToPdfConverter:
    """
    Base class for Latex -> SVG converters
    """
    DEFAULT_DOCUMENT_CLASS = r"\documentclass{article}"
    DOCUMENT_TEMPLATE = r"""
    {0}
    \pagestyle{{empty}}
    \begin{{document}}
    {1}
    \end{{document}}
    """

    LATEX_OPTIONS = ['-interaction=nonstopmode',
                     '-halt-on-error']

    def __init__(self, inkscape_exe: str, latex_exe: str):
        self.tmp_base = 'tmp'
        self._inkscape_exe = inkscape_exe
        self._latex_exe = latex_exe

    # --- Internal
    def tmp(self, suffix):
        """
        Return a file name corresponding to given file suffix,
        and residing in the temporary directory.
        """
        return self.tmp_base + '.' + suffix

    @staticmethod
    def exec_command(cmd, ok_return_value=0):
        """
        Run given command, check return value, and return
        concatenated stdout and stderr.
        :param cmd: Command to execute
        :param ok_return_value: The expected return value after successful completion
        :raises: TexTextCommandNotFound, TexTextCommandFailed
        """

        try:
            # hides the command window for cli tools that are run (in Windows)
            info = None
            if platform.system() == "Windows":
                info = subprocess.STARTUPINFO()
                info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                info.wShowWindow = subprocess.SW_HIDE
            with subprocess.Popen(cmd,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  startupinfo=info) as proc:
                out, err = proc.communicate()

        except OSError as err:
            raise TexTextCommandNotFound(f"Command {' '.join(cmd)} failed: {err}") from err

        if ok_return_value is not None and proc.returncode != ok_return_value:
            raise TexTextCommandFailed(message=f"Command {' '.join(cmd)} failed (code {proc.returncode})",
                                       return_code=proc.returncode,
                                       stdout=out,
                                       stderr=err)
        return out + err

    def tex_to_pdf(self, latex_text, preamble_file):
        """
        Create a PDF file from latex text. Raises TexTextCommandNotFound or TexTextConversionError.
        """

        with logger.debug("Converting .tex to .pdf"):
            # Read preamble
            preamble_file = os.path.abspath(preamble_file)
            preamble = ""

            if os.path.isfile(preamble_file):
                with open(preamble_file, 'r', encoding="utf-8") as f_handle:
                    preamble += f_handle.read()

            # Add default document class to preamble if necessary
            if not _contains_document_class(preamble):
                preamble = self.DEFAULT_DOCUMENT_CLASS + preamble

            # Options pass to LaTeX-related commands

            texwrapper = self.DOCUMENT_TEMPLATE.format(preamble, latex_text)

            # Convert TeX to PDF

            # Write tex
            with open(self.tmp('tex'), mode='w', encoding='utf-8') as f_tex:
                f_tex.write(texwrapper)

            # Exec tex_command: tex -> pdf
            try:
                self.exec_command([self._latex_exe, self.tmp('tex')] + self.LATEX_OPTIONS)
            except TexTextCommandFailed as error:
                if os.path.exists(self.tmp('log')):
                    parsed_log = self.parse_pdf_log()
                    raise TexTextConversionError(parsed_log, error.return_code, error.stdout, error.stderr) from error
                else:
                    raise TexTextConversionError(str(error), error.return_code, error.stdout, error.stderr) from error

            if not os.path.exists(self.tmp('pdf')):
                raise TexTextConversionError(f"{self._latex_exe} didn't produce output {self.tmp('pdf')}")

    def pdf_to_svg(self):
        """
        Convert the PDF file into an SVG file. Raises TexTextCommandNotFound or TexTextConversionError.
        """
        self.exec_command([self._inkscape_exe, "--pdf-poppler", "--pdf-page=1", "--export-type=svg",
                           "--export-text-to-path", "--export-area-drawing", "--export-filename",
                           self.tmp('svg'), self.tmp('pdf')])

    def stroke_to_path(self):
        """
        Convert stroke elements to path elements for easier colorization and scaling in Inkscape

        E.g. $\\overline x$ -> the line above x is converted from stroke to path
        """
        try:
            self.exec_command([
                self._inkscape_exe,
                "-g",
                "--batch-process",
                f"--actions=EditSelectAll;StrokeToPath;export-filename:{self.tmp('svg')};export-do;EditUndo;FileClose",
                self.tmp('svg')
            ]
            )
        except (TexTextCommandNotFound, TexTextCommandFailed):
            pass

    def pdf_to_png(self, white_bg):
        """Convert the PDF file to a SVG file"""
        cmd = [
            self._inkscape_exe,
            "--pdf-poppler",
            "--pdf-page=1",
            "--export-type=png",
            "--export-area-drawing",
            "--export-dpi=300",
            "--export-filename", self.tmp('png'),
            self.tmp('pdf')
        ]

        if white_bg:
            cmd.extend([
                "--export-background=#FFFFFF",
                "--export-background-opacity=1.0"
            ])

        self.exec_command(cmd)

    def parse_pdf_log(self):
        """
        Strip down tex output to only the first error etc. and discard all the noise
        :return: string containing the error message and some context lines after it
        """
        with logger.debug("Parsing LaTeX log file"):
            parser = LatexLogParser()

            # noinspection PyBroadException
            try:
                with open(self.tmp('log'), mode='r', encoding='utf8') as f_handle:
                    parser.process(f_handle)
                return parser.errors[0]
            except Exception:
                return "TeX compilation failed. See stdout output for more details"


def _contains_document_class(preamble):
    """Return True if `preamble` contains a documentclass-like command.

    Also, checks and considers if the command is commented out or not.
    """
    lines = preamble.split("\n")
    document_commands = [r"\documentclass{", r"\documentclass[",
                         r"\documentstyle{", r"\documentstyle["]
    for line in lines:
        for document_command in document_commands:
            if document_command in line and "%" not in line.split(document_command)[0]:
                return True
    return False


class TexTextEleMetaData:
    def __init__(self, text="", preamble="", scale_factor=1.0, tex_command=TexText.DEFAULT_TEXCMD,
                 alignment=TexText.DEFAULT_ALIGNMENT, stroke_to_path=False, jacobian_sqrt=1.0,
                 textext_version="0.7", inkscape_version="0.0", inkex_version="0.0"):
        self.text = text
        self.preamble = preamble
        self.scale_factor = scale_factor
        self.tex_command = tex_command
        self.alignment = alignment
        self.stroke_to_path = stroke_to_path
        self.jacobian_sqrt = jacobian_sqrt
        self.textext_version = textext_version  # Introduced in 0.7.1
        self.inkscape_version = inkscape_version
        self.inkex_version = inkex_version


class TexTextElement(inkex.Group):
    tag_name = "g"

    KEY_VERSION = "version"
    KEY_TEXCONVERTER = "texconverter"
    KEY_PDFCONVERTER = "pdfconverter"
    KEY_TEXT = "text"
    KEY_PREAMBLE = "preamble"
    KEY_SCALE = "scale"
    KEY_ALIGNMENT = "alignment"
    KEY_JACOBIAN_SQRT ="jacobian_sqrt"
    KEY_STROKE2PATH = "stroke-to-path"
    KEY_INKSCAPE_VERSION = "inkscapeversion"
    KEY_INKEX_VERSION = "inkexversion"

    def __init__(self, svg_filename, document_unit):
        """
        :param svg_filename: The name of the file containing the svg-snippet
        :param document_unit: String specifyling the unit of the document into which the node is going
                              to be placed ("mm", "pt", ...)
        """
        super().__init__()
        self._svg_to_textext_node(svg_filename, document_unit)
        self.transform = inkex.Transform()

    def _svg_to_textext_node(self, svg_filename, document_unit):
        doc = etree.parse(svg_filename, parser=inkex.SVG_PARSER)

        root = doc.getroot()

        TexTextElement._expand_defs(root)

        shape_elements = [el for el in root if isinstance(el, (inkex.ShapeElement, inkex.Defs))]
        root.append(self)

        for ele in shape_elements:
            self.append(ele)

        self.make_ids_unique()

        # Ensure that snippet is correctly scaled according to the units of the document
        # We scale it here such that its size is correct in the document units
        # (Usually pt returned from poppler to mm in the main document)
        self.transform.add_scale(root.uutounit(f"1{root.unit}", document_unit))

    @staticmethod
    def _expand_defs(root):
        for ele in root:
            if isinstance(ele, inkex.Use):
                # <group> element will replace <use> node
                group = inkex.Group()

                # add all objects from symbol node
                for obj in ele.href:
                    group.append(deepcopy(obj))

                # translate group
                group.transform = inkex.Transform(translate=(float(ele.attrib["x"]), float(ele.attrib["y"])))

                # replace use node with group node
                parent = ele.getparent()
                parent.remove(ele)
                parent.add(group)

                ele = group  # required for recursive defs

            # expand children defs
            TexTextElement._expand_defs(ele)

    def set_meta_data(self, meta_data):
        """
        Writes the meta data as attributes into the svg node

        :param (TexTextEleMetaData) meta_data: The meta data set in the node

        """
        self.set_meta(self.KEY_VERSION, meta_data.textext_version)
        self.set_meta(self.KEY_TEXCONVERTER, meta_data.tex_command)
        self.set_meta(self.KEY_PDFCONVERTER, 'inkscape')
        self.set_meta_text(meta_data.text)
        self.set_meta(self.KEY_PREAMBLE, meta_data.preamble)
        self.set_meta(self.KEY_SCALE, str(meta_data.scale_factor))
        self.set_meta(self.KEY_ALIGNMENT, str(meta_data.alignment))
        self.set_meta(self.KEY_STROKE2PATH, str(int(meta_data.stroke_to_path)))
        self.set_meta(self.KEY_INKSCAPE_VERSION, str(meta_data.inkscape_version))
        self.set_meta(self.KEY_INKEX_VERSION, str(meta_data.inkex_version))

    def get_meta_data(self, default_scale=1.0, default_alignment=TexText.DEFAULT_ALIGNMENT,
                      default_texcmd=TexText.DEFAULT_TEXCMD):
        """
        Reads the TexText relevant attributes from the svg node and return them as a
        TexTextEleMetaData structure. If no text and no preamble attribute is found
        an AttributeNotFound error is raised.

        :param (float) default_scale: The default scale
        :param (str) default_alignment: The default alignment
        :param (str) default_texcmd: The default tex command

        :return (TexTextEleMetaData): The extracted meta data
        """
        meta_data = TexTextEleMetaData()
        meta_data.text = self.get_meta_text()
        meta_data.preamble = self.get_meta(self.KEY_PREAMBLE)
        meta_data.scale_factor = float(self.get_meta(self.KEY_SCALE, default_scale))
        meta_data.alignment = self.get_meta(self.KEY_ALIGNMENT, default_alignment)
        meta_data.tex_command = self.get_meta(self.KEY_TEXCONVERTER, default_texcmd)
        meta_data.stroke_to_path = bool(int(self.get_meta(self.KEY_STROKE2PATH, 0)))
        meta_data.jacobian_sqrt = float(self.get_meta(self.KEY_JACOBIAN_SQRT, 1.0))
        meta_data.textext_version = self.get_meta(self.KEY_VERSION, "<=0.7")  # introduced in 0.7.1
        meta_data.inkscape_version = self.get_meta(self.KEY_INKSCAPE_VERSION, "0.0")
        meta_data.inkex_version = self.get_meta(self.KEY_INKEX_VERSION, "0.0")

        return meta_data

    def make_ids_unique(self):
        """
        PDF->SVG converters tend to use same ids.
        To avoid confusion between objects with same id from two or more TexText objects we replace auto-generated
        ids with random unique values
        """
        rename_map = {}

        # replace all ids with unique random uuid
        for ele in self.iterfind('.//*[@id]'):
            old_id = ele.attrib["id"]
            new_id = 'id-' + str(uuid.uuid4())
            ele.attrib["id"] = new_id
            rename_map[old_id] = new_id

        # find usages of old ids and replace them
        def replace_old_id(match):
            old_name = match.group(1)
            try:
                replacement = rename_map[old_name]
            except KeyError:
                replacement = old_name
            return f"url(#{replacement})"
        regex = re.compile(r"url\(#([^)(]*)\)")

        for ele in self.iter():
            for name, value in ele.items():
                new_value = regex.sub(replace_old_id, value)
                ele.attrib[name] = new_value

    def get_jacobian_sqrt(self):
        # pylint: disable=invalid-name
        (a, b, _), (d, e, _) = inkex.Transform(self.transform).matrix
        det = a * e - d * b
        assert det != 0
        return math.sqrt(math.fabs(det))

    def set_meta(self, key, value):
        ns_key = f'{{{TEXTEXT_NS}}}{key}'
        self.set(ns_key, value)
        assert self.get_meta(key) == value, (self.get_meta(key), value)

    def set_meta_text(self, value):
        encoded_value = value.encode('unicode_escape').decode('utf-8')
        self.set_meta('text', encoded_value)

    def get_meta_text(self):
        node_version = self.get_meta("version", '0.7')
        encoded_text = self.get_meta('text')

        if node_version != '1.2.0':
            return encoded_text.encode('utf-8').decode('unicode_escape')
        return encoded_text

    def get_meta(self, key, default=None):
        try:
            ns_key = f'{{{TEXTEXT_NS}}}{key}'
            value = self.get(ns_key)
            if value is None:
                raise AttributeError(f'{self} has no attribute `{key}`')
            return value
        except AttributeError as attr_error:
            if default is not None:
                return default
            raise attr_error

    def align_to_node(self, ref_node, alignment, relative_scale):
        """
        Aligns the node represented by self to a reference node according to the settings defined by the user
        :param (TexTextElement) ref_node: Reference node subclassed from SvgElement to which self is going to be aligned
        :param (str) alignment: A 2-element string list defining the alignment
        :param (float) relative_scale: Scaling of the new node relative to the scale of the reference node
        """
        scale_transform = inkex.Transform(f"scale({relative_scale})")

        old_transform = inkex.Transform(ref_node.transform)

        # Account for vertical flipping of nodes created via pstoedit in TexText <= 0.11.x
        revert_flip = inkex.Transform("scale(1)")
        if ref_node.get_meta("pdfconverter", "pstoedit") == "pstoedit":
            revert_flip = inkex.Transform(matrix=((1, 0, 0), (0, -1, 0)))  # vertical reflection

        composition = scale_transform * old_transform * revert_flip

        # keep alignment point of drawing intact, calculate required shift
        self.transform = composition

        ref_bb = ref_node.bounding_box()
        old_x, old_y, old_w, old_h = ref_bb.left, ref_bb.top, ref_bb.width, ref_bb.height
        bbox = self.bounding_box()
        new_x, new_y, new_w, new_h = bbox.left,  bbox.top, bbox.width, bbox.height

        p_old = self._get_pos(old_x, old_y, old_w, old_h, alignment)
        p_new = self._get_pos(new_x, new_y, new_w, new_h, alignment)

        d_x = p_old[0] - p_new[0]
        d_y = p_old[1] - p_new[1]

        composition = inkex.Transform(translate=(d_x, d_y)) * composition

        self.transform = composition
        self.set_meta("jacobian_sqrt", str(self.get_jacobian_sqrt()))

    @staticmethod
    def _get_pos(x, y, w, h, alignment):
        """ Returns the alignment point of a frame according to the required alignment

        :param x, y, w, h: Position of top left corner, width and height of the frame
        :param alignment: String describing the required alignment, e.g. "top left", "middle right", etc.
        """
        # pylint: disable=invalid-name
        v_alignment, h_alignment = alignment.split(" ")
        if v_alignment == "top":
            ypos = y
        elif v_alignment == "middle":
            ypos = y + h / 2
        elif v_alignment == "bottom":
            ypos = y + h
        else:
            # fallback -> middle
            ypos = y + h / 2

        if h_alignment == "left":
            xpos = x
        elif h_alignment == "center":
            xpos = x + w / 2
        elif h_alignment == "right":
            xpos = x + w
        else:
            # fallback -> center
            xpos = x + w / 2
        return [xpos, ypos]

    def is_colorized(self):
        """ Returns true if at least one element of the managed node contains a non-black fill or stroke color """
        return self.has_colorized_attribute() or self.has_colorized_style()

    def has_colorized_attribute(self):
        """ Returns true if at least one element of node contains a non-black fill or stroke attribute """
        for it_node in self.iter():
            for attrib in ["stroke", "fill"]:
                if attrib in it_node.attrib and it_node.attrib[attrib].lower().replace(" ", "") not in \
                        ["rgb(0%,0%,0%)", "black", "none", "#000000"]:
                    return True
        return False

    def has_colorized_style(self):
        """ Returns true if at least one element of node contains a non-black fill or stroke style """
        for it_node in self.iter():
            style = it_node.style  # type: inkex.Style
            for style_attrib in ["stroke", "fill"]:
                if style_attrib in style and \
                        style[style_attrib].lower().replace(" ", "") not in ["rgb(0%,0%,0%)",
                                                                             "black",
                                                                             "none",
                                                                             "#000000"]:
                    return True
        return False

    def import_group_color_style(self, src_svg_ele):
        """
        Extracts the color relevant style attributes of src_svg_ele (of class TexTextElement) and
        applies them to all items  of self. Ensures that non color relevant style
        attributes are not overwritten.
        """

        # Take the top level style information which is set when coloring the group in Inkscape
        style = src_svg_ele.style  # type: inkex.Style

        # If a style attribute exists we can copy the style, if not, there is nothing to do here
        if len(style):
            # Fetch the part of the source dict which is interesting for colorization
            color_style_dict = {key: value for key, value in style.items() if
                                key.lower() in ["fill", "stroke", "opacity", "stroke-opacity",
                                                "fill-opacity"] and value.lower() != "none"}

            for ele in self.iter():
                # Update style
                ele.style.update(color_style_dict)

                # Ensure that simple strokes are also colored if the the group has a fill color
                # ToDo: Check if this really can be put outside of the loop
                if "stroke" in ele.style and "fill" in color_style_dict:
                    ele.style["stroke"] = color_style_dict["fill"]

                # Remove style-duplicating attributes
                for prop in ("stroke", "fill"):
                    if prop in style:
                        ele.pop(prop)

                # Avoid unintentional bolded letters
                if "stroke-width" not in ele.style:
                    ele.style["stroke-width"] = "0"

    def set_none_strokes_to_0pt(self):
        """
        Iterates over all elements of the node. For each element which has the style attribute
        "stroke" set to "none" a style attribute "stroke-width" with value "0" is added. This
        ensures that when colorizing the node later in inkscape by setting the node and
        stroke colors letters do not become bold (letters have "stroke" set to "none" but e.g.
        horizontal lines in fraction bars and square roots are only affected by stroke colors
        so for full colorization of a node you need to set the fill as well as the stroke color!).
        """
        for ele in self.iter():
            if ele.style.get("stroke", "").lower() == "none":
                ele.style["stroke-width"] = "0"
