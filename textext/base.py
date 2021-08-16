"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2021 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
from __future__ import print_function
import hashlib
import logging
import logging.handlers
import math
import re
import os
import platform
import sys
import uuid
from io import open # ToDo: For open utf8, remove when Python 2 support is skipped

from .requirements_check import defaults, set_logging_levels, TexTextRequirementsChecker
from .utility import ChangeToTemporaryDirectory, CycleBufferHandler, MyLogger, NestedLoggingGuard, Settings, Cache, \
    exec_command
from .errors import *

with open(os.path.join(os.path.dirname(__file__), "VERSION")) as version_file:
    __version__ = version_file.readline().strip()
__docformat__ = "restructuredtext en"

EXIT_CODE_OK = 0
EXIT_CODE_EXPECTED_ERROR = 1
EXIT_CODE_UNEXPECTED_ERROR = 60

LOG_LOCATION = os.path.join(os.path.dirname(__file__))
if not os.path.isdir(LOG_LOCATION):
    os.makedirs(LOG_LOCATION)
LOG_FILENAME = os.path.join(LOG_LOCATION, "textext.log")  # todo: check destination is writeable

# There are two channels `file_log_channel` and `user_log_channel`
# `file_log_channel` dumps detailed log to a file
# `user_log_channel` accumulates log messages to show them to user via .show_messages() function
#
set_logging_levels()
logging.setLoggerClass(MyLogger)
__logger = logging.getLogger('TexText')
logger = NestedLoggingGuard(__logger)
__logger.setLevel(logging.DEBUG)

log_formatter = logging.Formatter('[%(asctime)s][%(levelname)8s]: %(message)s          //  %(filename)s:%(lineno)-5d')

file_log_channel = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                                        maxBytes=500 * 1024,  # up to 500 kB
                                                        backupCount=2,  # up to two log files
                                                        encoding="utf-8"
                                                        )
file_log_channel.setLevel(logging.NOTSET)
file_log_channel.setFormatter(log_formatter)

user_formatter = logging.Formatter('[%(name)s][%(levelname)6s]: %(message)s')
user_log_channel = CycleBufferHandler(capacity=1024)  # store up to 1024 messages
user_log_channel.setLevel(logging.DEBUG)
user_log_channel.setFormatter(user_formatter)

__logger.addHandler(file_log_channel)
__logger.addHandler(user_log_channel)

import inkex
from lxml import etree

TEXTEXT_NS = u"http://www.iki.fi/pav/software/textext/"
SVG_NS = u"http://www.w3.org/2000/svg"
XLINK_NS = u"http://www.w3.org/1999/xlink"

ID_PREFIX = "textext-"

NSS = {
    u'textext': TEXTEXT_NS,
    u'svg': SVG_NS,
    u'xlink': XLINK_NS,
}


# ------------------------------------------------------------------------------
# Inkscape plugin functionality
# ------------------------------------------------------------------------------

class TexText(inkex.EffectExtension):

    DEFAULT_ALIGNMENT = "middle center"
    DEFAULT_TEXCMD = "pdflatex"

    def __init__(self):

        self.config = Settings(directory=os.path.dirname(os.path.realpath(__file__)))
        self.cache = Cache()
        previous_exit_code = self.cache.get("previous_exit_code", None)

        if previous_exit_code is None:
            logging.disable(logging.NOTSET)
            logger.debug("First run of TexText. Enforcing DEBUG mode.")
        elif previous_exit_code == EXIT_CODE_OK:
            logging.disable(logging.CRITICAL)
        elif previous_exit_code == EXIT_CODE_UNEXPECTED_ERROR:
            logging.disable(logging.NOTSET)
            logger.debug("Enforcing DEBUG mode due to previous exit code `%d`" % previous_exit_code)
        else:
            logging.disable(logging.DEBUG)

        logger.debug("TexText initialized")
        with open(__file__, "rb") as fhl:
            logger.debug("TexText version = %s (md5sum = %s)" %
                         (repr(__version__), hashlib.md5(fhl.read()).hexdigest())
                         )
        logger.debug("platform.system() = %s" % repr(platform.system()))
        logger.debug("platform.release() = %s" % repr(platform.release()))
        logger.debug("platform.version() = %s" % repr(platform.version()))

        logger.debug("platform.machine() = %s" % repr(platform.machine()))
        logger.debug("platform.uname() = %s" % repr(platform.uname()))
        logger.debug("platform.mac_ver() = %s" % repr(platform.mac_ver()))

        logger.debug("sys.executable = %s" % repr(sys.executable))
        logger.debug("sys.version = %s" % repr(sys.version))
        logger.debug("os.environ = %s" % repr(os.environ))

        self.requirements_checker = TexTextRequirementsChecker(logger, self.config)

        if previous_exit_code == EXIT_CODE_OK and "requirements_checker" in self.cache.values:
            self.requirements_checker.inkscape_executable = self.cache["requirements_checker"][
                "inkscape_executable"]
            self.requirements_checker.available_tex_to_pdf_converters = self.cache["requirements_checker"][
                "available_tex_to_pdf_converters"]
            self.requirements_checker.available_pdf_to_svg_converters = self.cache["requirements_checker"][
                "available_pdf_to_svg_converters"]
        else:
            if self.requirements_checker.check() == False:
                raise TexTextFatalError("TexText requirements are not met. "
                                        "Please follow instructions "
                                        "https://textext.github.io/textext/")
            else:
                self.cache["requirements_checker"] = {
                    "inkscape_executable": self.requirements_checker.inkscape_executable,
                    "available_tex_to_pdf_converters": self.requirements_checker.available_tex_to_pdf_converters,
                    "available_pdf_to_svg_converters": self.requirements_checker.available_pdf_to_svg_converters,
                }

        super(TexText, self).__init__()

        self.arg_parser.add_argument(
            "--text",
            type=str,
            default=None)

        self.arg_parser.add_argument(
            "--preamble-file",
            type=str,
            default=self.config.get('preamble', "default_packages.tex"))

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
        from .asktext import AskTextDefault

        with logger.debug("TexText.effect"):

            # Find root element
            old_svg_ele, text, preamble_file, current_scale, current_convert_strokes_to_path = self.get_old()

            alignment = TexText.DEFAULT_ALIGNMENT

            preferred_tex_cmd = self.config.get("previous_tex_command", TexText.DEFAULT_TEXCMD)

            if preferred_tex_cmd in self.requirements_checker.available_tex_to_pdf_converters.keys():
                current_tex_command = preferred_tex_cmd
            else:
                current_tex_command = list(self.requirements_checker.available_tex_to_pdf_converters.keys())[0]

            if text:
                logger.debug("Old node text = %s" % repr(text))
                logger.debug("Old node scale = %s" % repr(current_scale))

            # This is very important when re-editing nodes which have been created using TexText <= 0.7. It ensures that
            # the scale factor which is displayed in the AskText dialog is adjusted in such a way that the size of the node
            # is preserved when recompiling the LaTeX code. ("version" attribute introduced in 0.7.1)
            if old_svg_ele is not None:

                if old_svg_ele.get_meta("version", '<=0.7') == '<=0.7':
                    logger.debug("Adjust scale factor for node created with TexText<=0.7")
                    current_scale *= self.svg.uutounit(1, "pt")

                jac_sqrt = float(old_svg_ele.get_meta("jacobian_sqrt", 1.0))

                if jac_sqrt != 1.0:
                    logger.debug("Adjust scale factor to account transformations in inkscape")
                    current_scale *= old_svg_ele.get_jacobian_sqrt() / jac_sqrt

                alignment = old_svg_ele.get_meta("alignment", TexText.DEFAULT_ALIGNMENT)

                current_tex_command = old_svg_ele.get_meta("texconverter", current_tex_command)

            gui_config = self.config.get("gui", {})

            # Ask for TeX code
            if self.options.text is None:
                global_scale_factor = self.options.scale_factor

                if not preamble_file:
                    logger.debug("Using default preamble file `%s`" % self.options.preamble_file)
                    preamble_file = self.options.preamble_file
                else:
                    logger.debug("Using node preamble file")
                    # Check if preamble file exists at the specified absolute path location. If not, check to find
                    # the file in the default path. If this fails, too, fallback to the default.
                    if not os.path.exists(preamble_file):
                        logger.debug("Preamble file is NOT found by absolute path")
                        preamble_file = os.path.join(os.path.dirname(self.options.preamble_file),
                                                     os.path.basename(preamble_file))
                        if not os.path.exists(preamble_file):
                            logger.debug("Preamble file is NOT found along with default preamble file")
                            preamble_file = self.options.preamble_file
                        else:
                            logger.debug("Preamble file is found along with default preamble file")
                    else:
                        logger.debug("Preamble file found by absolute path")

                if not os.path.isfile(preamble_file):
                    logger.debug("Preamble file is not found")
                    preamble_file = ""

                asker = AskTextDefault(__version__, text, preamble_file, global_scale_factor, current_scale,
                                       current_alignment=alignment, current_texcmd=current_tex_command,
                                       current_convert_strokes_to_path=current_convert_strokes_to_path,
                                       tex_commands=sorted(list(
                                         self.requirements_checker.available_tex_to_pdf_converters.keys())),
                                       gui_config=gui_config)

                def save_callback(_text, _preamble, _scale, alignment=TexText.DEFAULT_ALIGNMENT,
                                  tex_cmd=TexText.DEFAULT_TEXCMD, conv_stroke_to_path=False):
                    return self.do_convert(_text, _preamble, _scale, old_svg_ele,
                                           alignment,
                                           tex_command=tex_cmd,
                                           convert_stroke_to_path=conv_stroke_to_path,
                                           original_scale=current_scale)

                def preview_callback(_text, _preamble, _preview_callback, _tex_command, _white_bg):
                    return self.preview_convert(_text,
                                                _preamble,
                                                _preview_callback,
                                                _tex_command,
                                                _white_bg
                                                )

                with logger.debug("Run TexText GUI"):
                    gui_config = asker.ask(save_callback, preview_callback)

                with logger.debug("Saving global GUI settings"):
                    self.config["gui"] = gui_config
                    self.config.save()

            else:
                # In case TT has been called with --text="" the old node is
                # just re-compiled if one exists
                if self.options.text == "" and text is not None:
                    new_text = text
                else:
                    new_text = self.options.text
                self.do_convert(new_text,
                                self.options.preamble_file,
                                self.options.scale_factor,
                                old_svg_ele,
                                self.options.alignment,
                                self.options.tex_command,
                                convert_stroke_to_path=False,
                                original_scale=current_scale
                                )

    def preview_convert(self, text, preamble_file, image_setter, tex_command, white_bg):
        """
        Generates a preview PNG of the LaTeX output using the selected converter.

        :param text:
        :param preamble_file:
        :param image_setter: A callback to execute with the file path of the generated PNG
        :param tex_command: Command for tex -> pdf
        :param (bool) white_bg: set background to white if True
        """

        tex_executable = self.requirements_checker.available_tex_to_pdf_converters[tex_command]

        with logger.debug("TexText.preview"):
            with logger.debug("args:"):
                for k, v in list(locals().items()):
                    logger.debug("%s = %s" % (k, repr(v)))

            if not text:
                logger.debug("no text, return")
                return

            if isinstance(text, bytes):
                text = text.decode('utf-8')

            with ChangeToTemporaryDirectory():
                with logger.debug("Converting tex to pdf"):
                    converter = TexToPdfConverter(self.requirements_checker)
                    converter.tex_to_pdf(tex_executable, text, preamble_file)
                    converter.pdf_to_png(white_bg=white_bg)
                    image_setter(converter.tmp('png'))

    def do_convert(self, text, preamble_file, user_scale_factor, old_svg_ele, alignment, tex_command,
                   convert_stroke_to_path, original_scale=None):
        """
        Does the conversion using the selected converter.

        :param text:
        :param preamble_file:
        :param user_scale_factor:
        :param old_svg_ele:
        :param alignment:
        :param tex_command: The tex command to be used for tex -> pdf ("pdflatex", "xelatex", "lualatex")
        :param convert_stroke_to_path: Determines if converter.stroke_to_path() is called
        :param original_scale Scale factor of old node
        """
        from inkex import Transform

        tex_executable = self.requirements_checker.available_tex_to_pdf_converters[tex_command]

        with logger.debug("TexText.do_convert"):
            with logger.debug("args:"):
                for k, v in list(locals().items()):
                    logger.debug("%s = %s" % (k, repr(v)))

            if not text:
                logger.debug("no text, return")
                return

            if isinstance(text, bytes):
                text = text.decode('utf-8')

            # Convert
            with logger.debug("Converting tex to svg"):
                with ChangeToTemporaryDirectory():
                    converter = TexToPdfConverter(self.requirements_checker)
                    converter.tex_to_pdf(tex_executable, text, preamble_file)
                    converter.pdf_to_svg()

                    if convert_stroke_to_path:
                        converter.stroke_to_path()

                    tt_node = TexTextElement(converter.tmp("svg"), self.svg.unittouu("1mm"))

            # -- Store textext attributes
            tt_node.set_meta("version", __version__)
            tt_node.set_meta("texconverter", tex_command)
            tt_node.set_meta("pdfconverter", 'inkscape')
            tt_node.set_meta_text(text)
            tt_node.set_meta("preamble", preamble_file)
            tt_node.set_meta("scale", str(user_scale_factor))
            tt_node.set_meta("alignment", str(alignment))
            tt_node.set_meta("stroke-to-path", str(int(convert_stroke_to_path)))
            try:
                inkscape_version = self.document.getroot().get('inkscape:version')
                tt_node.set_meta("inkscapeversion", inkscape_version.split(' ')[0])
            except AttributeError as ignored:
                # Unfortunately when this node comes from an Inkscape document that has never been saved before
                # no version attribute is provided by Inkscape :-(
                pass

            # Place new node in document
            if old_svg_ele is None:
                with logger.debug("Adding new node to document"):
                    # Place new nodes in the view center and scale them according to user request

                    # ToDo: Remove except block as far as new center props are available in official beta releases
                    try:
                        node_center = tt_node.bounding_box().center
                        view_center = self.svg.namedview.center
                    except AttributeError:
                        node_center = tt_node.bounding_box().center()
                        view_center = self.svg.get_center_position()

                    tt_node.transform = (Transform(translate=view_center) *    # place at view center
                                         Transform(scale=user_scale_factor) *  # scale
                                         Transform(translate=-node_center) *   # place node at origin
                                         tt_node.transform                     # use original node transform
                                         )

                    tt_node.set_meta('jacobian_sqrt', str(tt_node.get_jacobian_sqrt()))

                    tt_node.set_none_strokes_to_0pt()

                    self.svg.get_current_layer().add(tt_node)
            else:
                with logger.debug("Replacing node in document"):
                    # Rescale existing nodes according to user request
                    relative_scale = user_scale_factor / original_scale
                    tt_node.align_to_node(old_svg_ele, alignment, relative_scale)

                    # If no non-black color has been explicitily set by TeX we copy the color information
                    # from the old node so that coloring done in Inkscape is preserved.
                    if not tt_node.is_colorized():
                        tt_node.import_group_color_style(old_svg_ele)

                    self.replace_node(old_svg_ele, tt_node)

            with logger.debug("Saving global settings"):
                # -- Save settings
                if os.path.isfile(preamble_file):
                    self.config['preamble'] = preamble_file
                else:
                    self.config['preamble'] = ''

                self.config['scale'] = user_scale_factor

                self.config["previous_tex_command"] = tex_command

                self.config.save()

    def get_old(self):
        """
        Dig out LaTeX code and name of preamble file from old
        TexText-generated objects.

        :return: (old_svg_ele, latex_text, preamble_file_name, scale, conv_stroke_to_path)
        :rtype: (TexTextElement, str, str, float, bool)
        """

        for node in self.svg.selected.values():

            # TexText node must be a group
            if node.tag_name != 'g':
                continue

            node.__class__ = TexTextElement

            try:
                text = node.get_meta_text()
                preamble = node.get_meta('preamble')
                scale = float(node.get_meta('scale', 1.0))
                conv_stroke_to_path = bool(int(node.get_meta('stroke-to-path', 0)))

                return node, text, preamble, scale, conv_stroke_to_path

            except (TypeError, AttributeError) as ignored:
                pass

        return None, "", "", None, False

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
        # ToDo: Implement this later depending on the choice of the user (keep Inkscape colors vs. Tex colors)
        return


class TexToPdfConverter:
    """
    Base class for Latex -> SVG converters
    """
    DOCUMENT_TEMPLATE = r"""
    \documentclass{article}
    %s
    \pagestyle{empty}
    \begin{document}
    %s
    \end{document}
    """

    LATEX_OPTIONS = ['-interaction=nonstopmode',
                     '-halt-on-error']

    def __init__(self, checker):
        self.tmp_base = 'tmp'
        self.checker = checker  # type: requirements_check.TexTextRequirementsChecker

    # --- Internal
    def tmp(self, suffix):
        """
        Return a file name corresponding to given file suffix,
        and residing in the temporary directory.
        """
        return self.tmp_base + '.' + suffix

    def tex_to_pdf(self, tex_command, latex_text, preamble_file):
        """
        Create a PDF file from latex text
        """

        with logger.debug("Converting .tex to .pdf"):
            # Read preamble
            preamble_file = os.path.abspath(preamble_file)
            preamble = ""

            if os.path.isfile(preamble_file):
                with open(preamble_file, 'r') as f:
                    preamble += f.read()

            # Options pass to LaTeX-related commands

            texwrapper = self.DOCUMENT_TEMPLATE % (preamble, latex_text)

            # Convert TeX to PDF

            # Write tex
            with open(self.tmp('tex'), mode='w', encoding='utf-8') as f_tex:
                f_tex.write(texwrapper)

            # Exec tex_command: tex -> pdf
            try:
                exec_command([tex_command, self.tmp('tex')] + self.LATEX_OPTIONS)
            except TexTextCommandFailed as error:
                if os.path.exists(self.tmp('log')):
                    parsed_log = self.parse_pdf_log()
                    raise TexTextConversionError(parsed_log, error.return_code, error.stdout, error.stderr)
                else:
                    raise TexTextConversionError(str(error), error.return_code, error.stdout, error.stderr)

            if not os.path.exists(self.tmp('pdf')):
                raise TexTextConversionError("%s didn't produce output %s" % (tex_command, self.tmp('pdf')))

    def pdf_to_svg(self):
        """Convert the PDF file to a SVG file"""
        exec_command([
            self.checker.inkscape_executable,
            "--pdf-poppler",
            "--pdf-page=1",
            "--export-type=svg",
            "--export-text-to-path",
            "--export-area-drawing",
            "--export-filename", self.tmp('svg'),
            self.tmp('pdf')
        ]
        )

    def stroke_to_path(self):
        """
        Convert stroke elements to path elements for easier colorization and scaling in Inkscape

        E.g. $\\overline x$ -> the line above x is converted from stroke to path
        """
        try:
            exec_command([
                self.checker.inkscape_executable,
                "-g",
                "--batch-process",
                "--actions=EditSelectAll;StrokeToPath;export-filename:{0};export-do;EditUndo;FileClose".format(self.tmp('svg')),
                self.tmp('svg')
            ]
            )
        except (TexTextCommandNotFound, TexTextCommandFailed):
            pass

    def pdf_to_png(self, white_bg):
        """Convert the PDF file to a SVG file"""
        cmd = [
            self.checker.inkscape_executable,
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

        exec_command(cmd)

    def parse_pdf_log(self):
        """
        Strip down tex output to only the first error etc. and discard all the noise
        :return: string containing the error message and some context lines after it
        """
        with logger.debug("Parsing LaTeX log file"):
            from .texoutparse import LatexLogParser
            parser = LatexLogParser()

            try:
                with open(self.tmp('log'), encoding='utf8') as f:
                    parser.process(f)
                return parser.errors[0]
            except Exception as ignored:
                return "TeX compilation failed. See stdout output for more details"


class TexTextElement(inkex.Group):
    tag_name = "g"

    def __init__(self, svg_filename, uu_in_mm):
        """
        :param svg_filename: The name of the file containing the svg-snippet
        :param uu_in_mm: The units of the document into which the node is going to be placed into
                         expressed in mm
        """
        super(TexTextElement, self).__init__()
        self._svg_to_textext_node(svg_filename, uu_in_mm)

    def _svg_to_textext_node(self, svg_filename, doc_unit_to_mm):
        from inkex import ShapeElement, Defs, SvgDocumentElement
        doc = etree.parse(svg_filename, parser=inkex.SVG_PARSER)

        root = doc.getroot()

        TexTextElement._expand_defs(root)

        shape_elements = [el for el in root if isinstance(el, (ShapeElement, Defs))]
        root.append(self)

        for el in shape_elements:
            self.append(el)

        self.make_ids_unique()

        # Ensure that snippet is correctly scaled according to the units of the document
        self.transform.add_scale(doc_unit_to_mm/root.unittouu("1mm"))

    @staticmethod
    def _expand_defs(root):
        from inkex import Transform, ShapeElement
        from copy import deepcopy
        for el in root:
            if isinstance(el, inkex.Use):
                # <group> element will replace <use> node
                group = inkex.Group()

                # add all objects from symbol node
                for obj in el.href:
                    group.append(deepcopy(obj))

                # translate group
                group.transform = Transform(translate=(float(el.attrib["x"]), float(el.attrib["y"])))

                # replace use node with group node
                parent = el.getparent()
                parent.remove(el)
                parent.add(group)

                el = group  # required for recursive defs

            # expand children defs
            TexTextElement._expand_defs(el)

    def make_ids_unique(self):
        """
        PDF->SVG converters tend to use same ids.
        To avoid confusion between objects with same id from two or more TexText objects we replace auto-generated
        ids with random unique values
        """
        rename_map = {}

        # replace all ids with unique random uuid
        for el in self.iterfind('.//*[@id]'):
            old_id = el.attrib["id"]
            new_id = 'id-' + str(uuid.uuid4())
            el.attrib["id"] = new_id
            rename_map[old_id] = new_id

        # find usages of old ids and replace them
        def replace_old_id(m):
            old_name = m.group(1)
            try:
                replacement = rename_map[old_name]
            except KeyError:
                replacement = old_name
            return "url(#{})".format(replacement)
        regex = re.compile(r"url\(#([^)(]*)\)")

        for el in self.iter():
            for name, value in el.items():
                new_value = regex.sub(replace_old_id, value)
                el.attrib[name] = new_value

    def get_jacobian_sqrt(self):
        from inkex import Transform
        (a, b, c), (d, e, f) = Transform(self.transform).matrix
        det = a * e - d * b
        assert det != 0
        return math.sqrt(math.fabs(det))

    def set_meta(self, key, value):
        ns_key = '{{{ns}}}{key}'.format(ns=TEXTEXT_NS, key=key)
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
        else:
            return encoded_text

    def get_meta(self, key, default=None):
        try:
            ns_key = '{{{ns}}}{key}'.format(ns=TEXTEXT_NS, key=key)
            value = self.get(ns_key)
            if value is None:
                raise AttributeError('{} has no attribute `{}`'.format(self, key))
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
        from inkex import Transform
        scale_transform = Transform("scale(%f)" % relative_scale)

        old_transform = Transform(ref_node.transform)

        # Account for vertical flipping of nodes created via pstoedit in TexText <= 0.11.x
        revert_flip = Transform("scale(1)")
        if ref_node.get_meta("pdfconverter", "pstoedit") == "pstoedit":
            revert_flip = Transform(matrix=((1, 0, 0), (0, -1, 0)))  # vertical reflection

        composition = scale_transform * old_transform * revert_flip

        # keep alignment point of drawing intact, calculate required shift
        self.transform = composition

        ref_bb = ref_node.bounding_box()
        x, y, w, h = ref_bb.left,  ref_bb.top, ref_bb.width, ref_bb.height
        bb = self.bounding_box()
        new_x, new_y, new_w, new_h = bb.left,  bb.top, bb.width, bb.height

        p_old = self._get_pos(x, y, w, h, alignment)
        p_new = self._get_pos(new_x, new_y, new_w, new_h, alignment)

        dx = p_old[0] - p_new[0]
        dy = p_old[1] - p_new[1]

        composition = Transform(translate=(dx, dy)) * composition

        self.transform = composition
        self.set_meta("jacobian_sqrt", str(self.get_jacobian_sqrt()))

    @staticmethod
    def _get_pos(x, y, w, h, alignment):
        """ Returns the alignment point of a frame according to the required defined in alignment

        :param x, y, w, h: Position of top left corner, width and height of the frame
        :param alignment: String describing the required alignment, e.g. "top left", "middle right", etc.
        """
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
                if attrib in it_node.attrib and it_node.attrib[attrib].lower().replace(" ", "") not in [
                    "rgb(0%,0%,0%)",
                    "black", "none",
                    "#000000"]:
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

            for it in self.iter():
                # Update style
                it.style.update(color_style_dict)

                # Ensure that simple strokes are also colored if the the group has a fill color
                # ToDo: Check if this really can be put outside of the loop
                if "stroke" in it.style and "fill" in color_style_dict:
                    it.style["stroke"] = color_style_dict["fill"]

                # Remove style-duplicating attributes
                for prop in ("stroke", "fill"):
                    if prop in style:
                        it.pop(prop)

                # Avoid unintentional bolded letters
                if "stroke-width" not in it.style:
                    it.style["stroke-width"] = "0"

    def set_none_strokes_to_0pt(self):
        """
        Iterates over all elements of the node. For each element which has the style attribute
        "stroke" set to "none" a style attribute "stroke-width" with value "0" is added. This
        ensures that when colorizing the node later in inkscape by setting the node and
        stroke colors letters do not become bold (letters have "stroke" set to "none" but e.g.
        horizontal lines in fraction bars and square roots are only affected by stroke colors
        so for full colorization of a node you need to set the fill as well as the stroke color!).
        """
        for it in self.iter():
            if it.style.get("stroke", "").lower() == "none":
                it.style["stroke-width"] = "0"
