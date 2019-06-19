#!/usr/bin/env python
"""
=======
textext
=======

:Author: Pauli Virtanen <pav@iki.fi>
:Date: 2008-04-26
:Author: Pit Garbe <piiit@gmx.de>
:Date: 2014-02-03
:Author: TexText developers
:Date: 2019-04-05
:License: BSD

Textext is an extension for Inkscape_ that allows adding
LaTeX-generated text objects to your SVG drawing. What's more, you can
also *edit* these text objects after creating them.

This brings some of the power of TeX typesetting to Inkscape.

Textext was initially based on InkLaTeX_ written by Toru Araki,
but is now rewritten.

Thanks to Sergei Izmailov, Robert Szalai, Rafal Kolanski, Brian Clarke,
Florent Becker and Vladislav Gavryusev for contributions.

.. note::
   Unfortunately, the TeX input dialog is modal. That is, you cannot
   do anything else with Inkscape while you are composing the LaTeX
   text snippet.

   This is because I have not yet worked out whether it is possible to
   write asynchronous extensions for Inkscape.

.. note::
   Textext requires Pdflatex and Pstoedit_ compiled with the ``plot-svg`` back-end

.. _Pstoedit: http://www.pstoedit.net/pstoedit
.. _Inkscape: http://www.inkscape.org/
.. _InkLaTeX: http://www.kono.cis.iwate-u.ac.jp/~arakit/inkscape/inklatex.html
"""

from __future__ import print_function
import abc
import copy
import hashlib
import logging
import logging.handlers
import math
import os
import platform
import sys
import traceback

from requirements_check import defaults, set_logging_levels, TexTextRequirementsChecker
from utility import ChangeToTemporaryDirectory, CycleBufferHandler, MyLogger, NestedLoggingGuard, Settings, Cache, \
    exec_command
from errors import *

__version__ = open(os.path.join(os.path.dirname(__file__), "VERSION")).readline().strip()
__docformat__ = "restructuredtext en"

EXIT_CODE_OK = 0
EXIT_CODE_EXPECTED_ERROR = 1
EXIT_CODE_UNEXPECTED_ERROR = 60

LOG_LOCATION = os.path.join(defaults.inkscape_extensions_path, "textext")
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
                                                        backupCount=2  # up to two log files
                                                        )
file_log_channel.setLevel(logging.NOTSET)
file_log_channel.setFormatter(log_formatter)

user_formatter = logging.Formatter('[%(name)s][%(levelname)6s]: %(message)s')
user_log_channel = CycleBufferHandler(capacity=1024)  # store up to 1024 messages
user_log_channel.setLevel(logging.DEBUG)
user_log_channel.setFormatter(user_formatter)

__logger.addHandler(file_log_channel)
__logger.addHandler(user_log_channel)

try:

    version_is_good = (2, 7) <= sys.version_info < (3, 0)
    if not version_is_good:
        raise TexTextFatalError("Python 2.7 is required, but found %s" % sys.version.split("\n")[0])

    import inkex
    import inkex.elements
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

    # Due to Inkscape 0.92.2 path problem placed here and not in LatexConverterBase.parse_pdf_log
    from typesetter import Typesetter


    # ------------------------------------------------------------------------------
    # Inkscape plugin functionality
    # ------------------------------------------------------------------------------

    class TexText(inkex.EffectExtension):

        DEFAULT_ALIGNMENT = "middle center"
        DEFAULT_TEXCMD = "pdflatex"

        def __init__(self):

            self.config = Settings("config.json")
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
            logger.debug("TexText version = %s (md5sum = %s)" %
                         (repr(__version__), hashlib.md5(open(__file__).read()).hexdigest())
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

            if self.requirements_checker.check() == False:
                raise TexTextFatalError("TexText requirements are not met. "
                                        "Please follow instructions "
                                        "https://textext.github.io/textext/")

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

        # Identical to inkex.Effect.getDocumentWidth() in Inkscape >= 0.91, but to provide compatibility with
        # Inkscape 0.48 we implement it here explicitly again as long as we provide compatibility with that version
        def get_document_width(self):
            width = self.document.getroot().get('width')
            if width:
                return width
            else:
                viewbox = self.document.getroot().get('viewBox')
                if viewbox:
                    return viewbox.split()[2]
                else:
                    return '0'

        # Identical to inkex.Effect.getDocumentHeight() in Inkscape >= 0.91, but to provide compatibility with
        # Inkscape 0.48 we implement it here explicitly again as long as we provide compatibility with that version
        def get_document_height(self):
            height = self.document.getroot().get('height')
            if height:
                return height
            else:
                viewbox = self.document.getroot().get('viewBox')
                if viewbox:
                    return viewbox.split()[3]
                else:
                    return '0'

        def effect(self):
            """Perform the effect: create/modify TexText objects"""
            from asktext import AskerFactory


            with logger.debug("TexText.effect"):

                # Find root element
                old_svg_ele, text, preamble_file, current_scale = self.get_old()

                # print(old_svg_ele)

                alignment = TexText.DEFAULT_ALIGNMENT

                preferred_tex_cmd = self.config.get("previous_tex_command", TexText.DEFAULT_TEXCMD)

                if preferred_tex_cmd in self.requirements_checker.available_tex_to_pdf_converters.keys():
                    current_tex_command = preferred_tex_cmd
                else:
                    current_tex_command = self.requirements_checker.available_tex_to_pdf_converters.keys()[0]

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

                    asker = AskerFactory().asker(__version__, text, preamble_file, global_scale_factor, current_scale,
                                                 current_alignment=alignment, current_texcmd=current_tex_command,
                                                 tex_commands=sorted(list(
                                                     self.requirements_checker.available_tex_to_pdf_converters.keys())),
                                                 gui_config=gui_config)

                    def save_callback(_text, _preamble, _scale, alignment=TexText.DEFAULT_ALIGNMENT,
                                      tex_cmd=TexText.DEFAULT_TEXCMD):
                        return self.do_convert(_text, _preamble, _scale, old_svg_ele,
                                               alignment,
                                               tex_command=tex_cmd,
                                               original_scale=current_scale)

                    def preview_callback(_text, _preamble, _preview_callback, _tex_command):
                        return self.preview_convert(_text,
                                                    _preamble,
                                                    _preview_callback,
                                                    _tex_command)

                    with logger.debug("Run TexText GUI"):
                        gui_config = asker.ask(save_callback, preview_callback)

                    with logger.debug("Saving global GUI settings"):
                        self.config["gui"] = gui_config
                        self.config.save()

                else:
                    # ToDo: I think this is completely broken...
                    self.do_convert(self.options.text,
                                    self.options.preamble_file,
                                    self.options.scale_factor,
                                    old_svg_ele,
                                    self.DEFAULT_ALIGNMENT,
                                    self.DEFAULT_TEXCMD,
                                    original_scale=current_scale
                                    )

        def preview_convert(self, text, preamble_file, image_setter, tex_command):
            """
            Generates a preview PNG of the LaTeX output using the selected converter.

            :param text:
            :param preamble_file:
            :param image_setter: A callback to execute with the file path of the generated PNG
            :param tex_command: Command for tex -> pdf
            """

            tex_executable = self.requirements_checker.available_tex_to_pdf_converters[tex_command]

            with logger.debug("TexText.preview"):
                with logger.debug("args:"):
                    for k, v in locals().items():
                        logger.debug("%s = %s" % (k, repr(v)))

                if not text:
                    logger.debug("no text, return")
                    return

                if isinstance(text, unicode):
                    text = text.encode('utf-8')

                with ChangeToTemporaryDirectory():
                    with logger.debug("Converting tex to pdf"):
                        converter = TexToPdfConverter(self.requirements_checker)
                        converter.tex_to_pdf(tex_executable, text, preamble_file)
                        converter.pdf_to_png()
                        image_setter(converter.tmp('png'))

        def do_convert(self, text, preamble_file, user_scale_factor, old_svg_ele, alignment, tex_command,
                       original_scale=None):
            """
            Does the conversion using the selected converter.

            :param text:
            :param preamble_file:
            :param user_scale_factor:
            :param old_svg_ele:
            :param alignment:
            :param tex_cmd: The tex command to be used for tex -> pdf ("pdflatex", "xelatex", "lualatex")
            """
            from inkex.transforms import Transform, TranslateTransform

            tex_executable = self.requirements_checker.available_tex_to_pdf_converters[tex_command]

            with logger.debug("TexText.do_convert"):
                with logger.debug("args:"):
                    for k, v in locals().items():
                        logger.debug("%s = %s" % (k, repr(v)))

                if not text:
                    logger.debug("no text, return")
                    return

                if isinstance(text, unicode):
                    text = text.encode('utf-8')

                # Coordinates in node from converter are always in pt, we have to scale them such that the node size is correct
                # even if the document user units are not in pt
                scale_factor = user_scale_factor * self.svg.unittouu("1pt")

                # Convert
                with logger.debug("Converting tex to svg"):
                    with ChangeToTemporaryDirectory():
                        converter = TexToPdfConverter(self.requirements_checker)
                        converter.tex_to_pdf(tex_executable, text, preamble_file)
                        converter.pdf_to_svg()
                        tt_node = TexTextElement(converter.tmp("svg"))

                # -- Store textext attributes
                tt_node.set_meta("version", __version__)
                tt_node.set_meta("texconverter", tex_command)
                tt_node.set_meta("pdfconverter", 'inkscape')
                tt_node.set_meta("text", text)
                tt_node.set_meta("preamble", preamble_file)
                tt_node.set_meta("scale", str(user_scale_factor))
                tt_node.set_meta("alignment", str(alignment))

                try:
                    inkscape_version = self.svg.getroot().get('version')
                    tt_node.set("inkscapeversion", inkscape_version.split(' ')[0])
                except AttributeError as ignored:
                    # Unfortunately when this node comes from an Inkscape document that has never been saved before
                    # no version attribute is provided by Inkscape :-(
                    pass

                # -- Copy style
                if old_svg_ele is None:
                    with logger.debug("Adding new node to document"):
                        root = self.document.getroot()
                        width = self.svg.unittouu(self.get_document_width())
                        height = self.svg.unittouu(self.get_document_height())

                        x, y, w, h = tt_node.bounding_box()
                        tt_node.transform = Transform(tt_node.transform) * TranslateTransform(-x + width / 2 - w / 2,
                                                                                              -y + height / 2 - h / 2)
                        tt_node.set_meta('jacobian_sqrt', str(tt_node.get_jacobian_sqrt()))

                        self.svg.get_current_layer().add(tt_node)
                else:
                    with logger.debug("Replacing node in document"):
                        relative_scale = user_scale_factor / original_scale
                        tt_node.align_to_node(old_svg_ele, alignment, relative_scale)

                        # If no non-black color has been explicitily set by TeX we copy the color information from the old node
                        # so that coloring done in Inkscape is preserved.
                        if False and not tt_node.is_colorized(): # todo: re-enable colorize feature
                            tt_node.import_group_color_style(old_svg_ele)

                        self.replace_node(old_svg_ele, tt_node)

                with logger.debug("Saving global settings"):
                    # -- Save settings
                    if os.path.isfile(preamble_file):
                        self.config['preamble'] = preamble_file
                    else:
                        self.config['preamble'] = ''

                    # ToDo: Do we really need this if statement?
                    if scale_factor is not None:
                        self.config['scale'] = user_scale_factor

                    self.config["previous_tex_command"] = tex_command

                    self.config.save()

        def get_old(self):
            """
            Dig out LaTeX code and name of preamble file from old
            TexText-generated objects.

            :return: (old_svg_ele, latex_text, preamble_file_name, scale)
            :rtype: (TexTextElement, str, str, float)
            """

            for node in self.svg.selected.values():

                # TexText node must be a group
                if node.tag_name != 'g':
                    continue

                node.__class__ = TexTextElement

                try:
                    text = node.get_meta('text')
                    preamble = node.get_meta('preamble')
                    scale = float(node.get_meta('scale', 1.0))

                    return node, text, preamble, scale

                except (TypeError, AttributeError) as ignored:
                    pass

            return None, "", "", None

        def replace_node(self, old_node, new_node):
            """
            Replace an XML node old_node with new_node
            """
            parent = old_node.getparent()
            parent.remove(old_node)
            parent.append(new_node)
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
                with open(self.tmp('tex'), 'w') as f_tex:
                    f_tex.write(texwrapper)

                # Exec tex_command: tex -> pdf
                try:
                    exec_command([tex_command, self.tmp('tex')] + self.LATEX_OPTIONS)
                except TexTextCommandFailed as error:
                    if os.path.exists(self.tmp('log')):
                        parsed_log = self.parse_pdf_log(self.tmp('log'))
                        raise TexTextConversionError(parsed_log, error.return_code, error.stdout, error.stderr)
                    else:
                        raise TexTextConversionError(error.message, error.return_code, error.stdout, error.stderr)

                if not os.path.exists(self.tmp('pdf')):
                    raise TexTextConversionError("%s didn't produce output %s" % (tex_command, self.tmp('pdf')))

        def pdf_to_svg(self):
            """Convert the PDF file to a SVG file"""
            exec_command([
                self.checker.inkscape_executable,
                "--without-gui",
                "--pdf-poppler",
                "--pdf-page=1",
                "--export-type=svg",
                "--export-text-to-path",
                "--export-area-drawing",
                "--export-file", self.tmp('svg'),
                self.tmp('pdf')
            ]
            )

        def pdf_to_png(self):
            """Convert the PDF file to a SVG file"""
            exec_command([
                self.checker.inkscape_executable,
                "--without-gui",
                "--pdf-poppler",
                "--pdf-page=1",
                "--export-type=png",
                "--export-area-drawing",
                "--export-dpi=300",
                "--export-file", self.tmp('png'),
                self.tmp('pdf')
            ]
            )

        def parse_pdf_log(self, logfile):
            """
            Strip down tex output to only the warnings, errors etc. and discard all the noise
            :param logfile:
            :return: string
            """
            with logger.debug("Parsing LaTeX log file"):
                from io import StringIO
                log_buffer = StringIO()
                log_handler = logging.StreamHandler(log_buffer)

                typesetter = Typesetter(self.tmp('tex'))
                typesetter.halt_on_errors = False

                handlers = typesetter.logger.handlers
                for handler in handlers:
                    typesetter.logger.removeHandler(handler)

                typesetter.logger.addHandler(log_handler)
                typesetter.process_log(logfile)

                typesetter.logger.removeHandler(log_handler)

                log_handler.flush()
                log_buffer.flush()

                return log_buffer.getvalue()

    import inkex.svg


    class TexTextElement(inkex.elements.Group):
        tag_name = "g"

        def __init__(self, svg_filename=None):
            super(TexTextElement, self).__init__()
            self._svg_to_textext_node(svg_filename)

        def _svg_to_textext_node(self, svg_filename):
            from inkex.elements import ShapeElement
            from inkex.svg import SvgDocumentElement
            doc = etree.parse(svg_filename, parser=inkex.elements.SVG_PARSER)

            root = doc.getroot()

            TexTextElement._expand_defs(root)

            shape_elements = [el for el in root if isinstance(el, ShapeElement)]
            root.append(self)

            for el in shape_elements:
                self.append(el)

        @staticmethod
        def _expand_defs(root):
            from inkex.transforms import TranslateTransform, Transform
            from inkex.elements import ShapeElement
            from copy import deepcopy
            for el in root:
                if isinstance(el, inkex.elements.Use):
                    # <group> element will replace <use> node
                    group = inkex.elements.Group()

                    # add all objects from symbol node
                    for obj in el.href:
                        group.append(deepcopy(obj))

                    # translate group
                    group.transform = TranslateTransform(float(el.attrib["x"]), float(el.attrib["y"]))

                    # replace use node with group node
                    parent = el.getparent()
                    parent.remove(el)
                    parent.add(group)

                    el = group  # required for recursive defs

                # expand children defs
                TexTextElement._expand_defs(el)

        def get_jacobian_sqrt(self):
            from inkex.transforms import Transform
            (a, b, c), (d, e, f) = Transform(self.transform).matrix
            det = a * e - d * b
            assert det != 0
            return math.sqrt(math.fabs(det))

        def set_meta(self, key, value):
            ns_key = '{{{ns}}}{key}'.format(ns=TEXTEXT_NS, key=key)
            self.set(ns_key, value.encode('string-escape'))
            assert self.get_meta(key) == value, (self.get_meta(key), value)

        def get_meta(self, key, default=None):
            try:
                ns_key = '{{{ns}}}{key}'.format(ns=TEXTEXT_NS, key=key)
                value = self.get(ns_key).decode('string-escape')
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
            from inkex.transforms import Transform, TranslateTransform
            scale_transform = Transform("scale(%f)" % relative_scale)

            old_transform = Transform(ref_node.transform)

            # Account for vertical flipping of pstoedit nodes when recompiled via pdf2svg and vice versa
            revert_flip = Transform("scale(1)")
            if ref_node.get_meta("pdfconverter") == "pdf2svg":
                revert_flip = Transform(matrix=((1, 0, 0), (0, -1, 0)))  # vertical reflection

            composition = old_transform * revert_flip

            composition = scale_transform * composition

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

            composition = TranslateTransform(dx, dy) * composition

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
            raise NotImplementedError("Not ported to inkscape 1.0")
            return self.has_colorized_attribute(self._node) or self.has_colorized_style(self._node)


        def has_colorized_attribute(self):
            """ Returns true if at least one element of node contains a non-black fill or stroke attribute """
            raise NotImplementedError("Not ported to inkscape 1.0")
            for it_node in self.getiterator():
                for attrib in ["stroke", "fill"]:
                    if attrib in it_node.attrib and it_node.attrib[attrib].lower().replace(" ", "") not in ["rgb(0%,0%,0%)",
                                                                                                            "black", "none",
                                                                                                            "#000000"]:
                        return True
            return False

        def has_colorized_style(self):
            """ Returns true if at least one element of node contains a non-black fill or stroke style """
            raise NotImplementedError("Not ported to inkscape 1.0")
            for it_node in self.getiterator():
                if "style" in it_node.attrib:
                    node_style_dict = it_node.style
                    for style_attrib in ["stroke", "fill"]:
                        if style_attrib in node_style_dict and \
                                node_style_dict[style_attrib].lower().replace(" ", "") not in ["rgb(0%,0%,0%)",
                                                                                               "black",
                                                                                               "none",
                                                                                               "#000000"]:
                            return True
            return False

        def import_group_color_style(self, src_svg_ele):
            """
            Extracts the color relevant style attributes of src_svg_ele (of class SVGElement) and applies them to all items
            of self._node. Ensures that non color relevant style attributes are not overwritten.
            """
            raise NotImplementedError("Not ported to inkscape 1.0")

            # Take the top level style information which is set when coloring the group in Inkscape
            src_style_string = src_svg_ele._node.get("style")

            # If a style attribute exists we can copy the style, if not, there is nothing to do here
            if src_style_string:
                # Fetch the part of the source dict which is interesting for colorization
                src_style_dict = ss.parseStyle(src_style_string)
                color_style_dict = {key: value for key, value in src_style_dict.items() if
                                    key.lower() in ["fill", "stroke", "opacity", "stroke-opacity",
                                                    "fill-opacity"] and value.lower() != "none"}

                # Iterate over all nodes of self._node and apply the imported color style
                for dest_node in self._node.getiterator():
                    dest_style_string = dest_node.attrib.get("style")
                    if dest_style_string:
                        dest_style_dict = ss.parseStyle(dest_style_string)
                        for key, value in color_style_dict.items():
                            dest_style_dict[key] = value
                    else:
                        dest_style_dict = color_style_dict
                    dest_style_string = ss.formatStyle(dest_style_dict)
                    dest_node.attrib["style"] = dest_style_string

    # ------------------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------------------

    if __name__ == "__main__":
        effect = TexText()
        effect.run()
        effect.cache["previous_exit_code"] = EXIT_CODE_OK
        effect.cache.save()


except TexTextInternalError as e:
    # TexTextInternalError should never be raised.
    # It's TexText logic error and should be reported.
    logger.error(str(e))
    logger.error(traceback.format_exc())
    logger.info("TexText finished with error, please run extension again")
    logger.info("If problem persists, please file a bug https://github.com/textext/textext/issues/new")
    user_log_channel.show_messages()
    try:
        cache = Cache()
        cache["previous_exit_code"] = EXIT_CODE_UNEXPECTED_ERROR
        cache.save()
    except:
        pass
    exit(EXIT_CODE_UNEXPECTED_ERROR)  # TexText internal error
except TexTextFatalError as e:
    logger.error(str(e))
    user_log_channel.show_messages()
    try:
        cache = Cache()
        cache["previous_exit_code"] = EXIT_CODE_EXPECTED_ERROR
        cache.save()
    except:
        pass
    exit(EXIT_CODE_EXPECTED_ERROR)  # Bad setup
except Exception as e:
    # All errors should be handled by above clause.
    # If any propagates here it's TexText logic error and should be reported.
    logger.error(str(e))
    logger.error(traceback.format_exc())
    logger.info("TexText finished with error, please run extension again")
    logger.info("If problem persists, please file a bug https://github.com/textext/textext/issues/new")
    user_log_channel.show_messages()
    try:
        cache = Cache()
        cache["previous_exit_code"] = EXIT_CODE_UNEXPECTED_ERROR
        cache.save()
    except:
        pass
    exit(EXIT_CODE_UNEXPECTED_ERROR)  # TexText internal error
