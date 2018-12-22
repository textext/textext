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
:Date: 2018-12-20
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
from utility import ChangeToTemporaryDirectory, CycleBufferHandler, MyLogger, NestedLoggingGuard, Settings, Cache, exec_command
from errors import *

__version__ = open(os.path.join(os.path.dirname(__file__), "VERSION")).readline().strip()
__docformat__ = "restructuredtext en"

EXIT_CODE_OK = 0
EXIT_CODE_EXPECTED_ERROR = 1
EXIT_CODE_UNEXPECTED_ERROR = 60

LOG_LOCATION = os.path.dirname(__file__)  # todo: check destination is writeable
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
                                                        backupCount=2         # up to two log files
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
    import simplestyle as ss
    import simpletransform as st
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

    #------------------------------------------------------------------------------
    # Inkscape plugin functionality
    #------------------------------------------------------------------------------

    class TexText(inkex.Effect):

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

            inkex.Effect.__init__(self)

            self.OptionParser.add_option(
                "-t", "--text", action="store", type="string",
                dest="text",
                default=None)
            self.OptionParser.add_option(
                "-p", "--preamble-file", action="store", type="string",
                dest="preamble_file",
                default=self.config.get('preamble', "default_packages.tex"))
            self.OptionParser.add_option(
                "-s", "--scale-factor", action="store", type="float",
                dest="scale_factor",
                default=self.config.get('scale', 1.0))

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

        def unit_to_uu(self, unit):
            """ Wrapper for unittouu() accounting for different implementation in Inkscape versions"""
            try:
                # Inkscape > 0.48
                return self.unittouu(unit)
            except AttributeError:
                # Inkscape <= 0.48
                return inkex.unittouu(unit)

        def uu_to_unit(self, val, unit):
            """ Wrapper for uutounit() accounting for different implementation in Inkscape versions"""
            try:
                # Inkscape > 0.48
                return self.uutounit(val, unit)
            except AttributeError:
                # Inkscape <= 0.48
                return inkex.uutounit(val, unit)

        def effect(self):
            """Perform the effect: create/modify TexText objects"""
            from asktext import AskerFactory

            global CONVERTERS
            with logger.debug("TexText.effect"):

                # Pick a converter
                converter_errors = []

                tex_to_pdf_converter = None
                for converter_class_name, converter_class in CONVERTERS.items():
                    if converter_class_name in self.requirements_checker.available_pdf_to_svg_converters:
                        tex_to_pdf_converter = converter_class(self.requirements_checker)
                        logger.debug("%s is usable" % converter_class.__name__)
                        break
                    else:
                        logger.debug("%s is not usable" % converter_class.__name__)

                # Find root element
                old_svg_ele, text, preamble_file, current_scale = self.get_old()

                if text:
                    logger.debug("Old node text = %s" % repr(text))
                    logger.debug("Old node scale = %s" % repr(current_scale))


                # This is very important when re-editing nodes which have been created using TexText <= 0.7. It ensures that
                # the scale factor which is displayed in the AskText dialog is adjusted in such a way that the size of the node
                # is preserved when recompiling the LaTeX code. ("version" attribute introduced in 0.7.1)
                if (old_svg_ele is not None) and (not old_svg_ele.is_attrib("version", TEXTEXT_NS)):
                    logger.debug("Adjust scale factor for node created with TexText<=0.7")
                    current_scale *= self.uu_to_unit(1, "pt")

                if old_svg_ele is not None and old_svg_ele.is_attrib("jacobian_sqrt", TEXTEXT_NS):
                    logger.debug("Adjust scale factor to account transformations in inkscape")
                    current_scale *= old_svg_ele.get_jacobian_sqrt()/float(old_svg_ele.get_attrib("jacobian_sqrt", TEXTEXT_NS))
                else:
                    logger.debug("Can't adjust scale to account node transformations done in inkscape. "
                                   "May result in loss of scale.")

                alignment = TexText.DEFAULT_ALIGNMENT

                if old_svg_ele is not None and old_svg_ele.is_attrib("alignment", TEXTEXT_NS):
                    alignment = old_svg_ele.get_attrib("alignment", TEXTEXT_NS)
                    logger.debug("Old node alignment `%s`" % alignment)
                else:
                    logger.debug("Using default node alignment `%s`" %alignment)

                preferred_tex_cmd = self.config.get("previous_tex_command", TexText.DEFAULT_TEXCMD)

                if preferred_tex_cmd in self.requirements_checker.available_tex_to_pdf_converters.keys():
                    current_tex_command = preferred_tex_cmd
                else:
                    current_tex_command = self.requirements_checker.available_tex_to_pdf_converters.keys()[0]

                if old_svg_ele is not None and old_svg_ele.is_attrib("texconverter", TEXTEXT_NS):
                    current_tex_command = old_svg_ele.get_attrib("texconverter", TEXTEXT_NS)
                else:
                    logger.debug("Using default tex converter `%s` " % current_tex_command)

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
                            preamble_file = os.path.join(os.path.dirname(self.options.preamble_file), os.path.basename(preamble_file))
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
                        return self.do_convert(_text, _preamble, _scale, tex_to_pdf_converter, old_svg_ele, alignment,
                                               tex_command=tex_cmd,
                                               original_scale=current_scale)

                    def preview_callback(_text, _preamble, _preview_callback, _tex_command):
                        return self.preview_convert(_text,
                                                    _preamble,
                                                    tex_to_pdf_converter,
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
                                    tex_to_pdf_converter,
                                    old_svg_ele,
                                    self.DEFAULT_ALIGNMENT,
                                    self.DEFAULT_TEXCMD,
                                    original_scale=current_scale
                                    )

        def preview_convert(self, text, preamble_file, converter, image_setter, tex_command):
            """
            Generates a preview PNG of the LaTeX output using the selected converter.

            :param text:
            :param preamble_file:
            :param converter:
            :param image_setter: A callback to execute with the file path of the generated PNG
            :param tex_command: Command for tex -> pdf
            """

            tex_executable = self.requirements_checker.available_tex_to_pdf_converters[tex_command]

            with logger.debug("TexText.preview"):
                with logger.debug("args:"):
                    for k,v in locals().items():
                        logger.debug("%s = %s" % (k, repr(v)))

                if not text:
                    logger.debug("no text, return")
                    return

                if isinstance(text, unicode):
                    text = text.encode('utf-8')

                with ChangeToTemporaryDirectory():
                    with logger.debug("Converting tex to pdf"):
                        converter.tex_to_pdf(tex_executable, text, preamble_file)
                        converter.pdf_to_svg()

                        if converter.get_pdf_converter_name() == "pdf2svg":
                            export_area_arguments = ['--export-area-drawing']
                        else:
                            export_area_arguments = ['--export-id','content','--export-id-only']

                        # convert resulting svg to png using Inkscape
                        options = ['-f', converter.tmp("svg"),
                                   '--export-png', converter.tmp('png'),
                                   ] + export_area_arguments + [
                                      '--export-dpi=200'
                                  ]
                        executable = self.requirements_checker.inkscape_executable

                        exec_command([executable] + options)

                        image_setter(converter.tmp('png'))


        def do_convert(self, text, preamble_file, user_scale_factor, converter, old_svg_ele, alignment, tex_command,
                       original_scale=None):
            """
            Does the conversion using the selected converter.

            :param text:
            :param preamble_file:
            :param user_scale_factor:
            :param converter_class:
            :param old_svg_ele:
            :param alignment:
            :param tex_cmd: The tex command to be used for tex -> pdf ("pdflatex", "xelatex", "lualatex")
            """

            tex_executable = self.requirements_checker.available_tex_to_pdf_converters[tex_command]

            with logger.debug("TexText.do_convert"):
                with logger.debug("args:"):
                    for k,v in locals().items():
                        logger.debug("%s = %s" % (k, repr(v)))

                if not text:
                    logger.debug("no text, return")
                    return

                if isinstance(text, unicode):
                    text = text.encode('utf-8')

                # Coordinates in node from converter are always in pt, we have to scale them such that the node size is correct
                # even if the document user units are not in pt
                scale_factor = user_scale_factor * self.unit_to_uu("1pt")

                # Convert
                with logger.debug("Converting tex to svg"):
                    new_svg_ele = converter.convert(text, preamble_file, scale_factor, tex_executable)

                # -- Store textext attributes
                new_svg_ele.set_attrib("version", __version__, TEXTEXT_NS)
                new_svg_ele.set_attrib("texconverter", tex_command, TEXTEXT_NS)
                new_svg_ele.set_attrib("pdfconverter", converter.get_pdf_converter_name(), TEXTEXT_NS)
                new_svg_ele.set_attrib("text", text, TEXTEXT_NS)
                new_svg_ele.set_attrib("preamble", preamble_file, TEXTEXT_NS)
                new_svg_ele.set_attrib("scale", str(user_scale_factor), TEXTEXT_NS)
                new_svg_ele.set_attrib("alignment", str(alignment), TEXTEXT_NS)

                if SvgElement.is_node_attrib(self.document.getroot(), 'version', inkex.NSS["inkscape"]):
                    new_svg_ele.set_attrib("inkscapeversion", SvgElement.get_node_attrib(self.document.getroot(), 'version',
                                                                                      inkex.NSS["inkscape"]).split(' ')[0])
                    # Unfortunately when this node comes from an Inkscape document that has never been saved before
                    # no version attribute is provided by Inkscape :-(

                # -- Copy style
                if old_svg_ele is None:
                    with logger.debug("Adding new node to document"):
                        root = self.document.getroot()
                        width = self.unit_to_uu(self.get_document_width())
                        height = self.unit_to_uu(self.get_document_height())

                        x, y, w, h = new_svg_ele.get_frame()
                        new_svg_ele.translate(-x + width/2 -w/2, -y+height/2 -h/2)
                        new_svg_ele.set_attrib('jacobian_sqrt', str(new_svg_ele.get_jacobian_sqrt()), TEXTEXT_NS)

                        self.current_layer.append(new_svg_ele.get_xml_raw_node())
                else:
                    with logger.debug("Replacing node in document"):
                        relative_scale = user_scale_factor / original_scale
                        new_svg_ele.align_to_node(old_svg_ele, alignment, relative_scale)

                        # If no non-black color has been explicitily set by TeX we copy the color information from the old node
                        # so that coloring done in Inkscape is preserved.
                        if not new_svg_ele.is_colorized():
                            new_svg_ele.import_group_color_style(old_svg_ele)

                        self.replace_node(old_svg_ele.get_xml_raw_node(), new_svg_ele.get_xml_raw_node())

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
            """

            for i in self.options.ids:
                node = self.selected[i]
                # ignore, if node tag has SVG_NS Namespace
                if node.tag != '{%s}g' % SVG_NS:
                    continue

                # otherwise, check for TEXTEXT_NS in attrib
                if SvgElement.is_node_attrib(node, 'text', TEXTEXT_NS):

                    # Check which pdf converter has been used for creating svg data
                    if SvgElement.is_node_attrib(node, 'pdfconverter', TEXTEXT_NS):
                        pdf_converter = SvgElement.get_node_attrib(node, 'pdfconverter', TEXTEXT_NS)
                        if pdf_converter == "pdf2svg":
                            svg_element = Pdf2SvgSvgElement(node)
                        else:
                            svg_element = PsToEditSvgElement(node)
                    else:
                        svg_element = PsToEditSvgElement(node)

                    text = svg_element.get_attrib('text', TEXTEXT_NS)
                    preamble = svg_element.get_attrib('preamble', TEXTEXT_NS)

                    scale = 1.0
                    if svg_element.is_attrib('scale', TEXTEXT_NS):
                        scale = float(svg_element.get_attrib('scale', TEXTEXT_NS))

                    return svg_element, text, preamble, scale
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

    class LatexConverterBase(object):
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
            self.checker = checker # type: requirements_check.TexTextRequirementsChecker

        def convert(self, latex_text, preamble_file, scale_factor, tex_command):
            """
            Return an XML node containing latex text

            :param latex_text: Latex code to use
            :param preamble_file: Name of a preamble file to include
            :param scale_factor: Scale factor to use if object doesn't have a ``transform`` attribute.
            :param tex_command: The command for tex -> pdf ("pdflatex", "xelatex", "lualatex"

            :return: XML DOM node
            """
            raise NotImplementedError

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

        def parse_pdf_log(self, logfile):
            """
            Strip down tex output to only the warnings, errors etc. and discard all the noise
            :param logfile:
            :return: string
            """
            with logger.debug("Parsing LaTeX log file"):
                import StringIO
                log_buffer = StringIO.StringIO()
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


    class PdfConverterBase(LatexConverterBase):

        def convert(self, latex_text, preamble_file, scale_factor, tex_command):
            with logger.debug("Converting .tex to svg element"):
                with ChangeToTemporaryDirectory():
                    self.tex_to_pdf(tex_command, latex_text, preamble_file)
                    self.pdf_to_svg()

                    new_svg_ele = self.svg_to_group()

                    if scale_factor is not None:
                        new_svg_ele.set_scale_factor(scale_factor)

                    return new_svg_ele

        def pdf_to_svg(self):
            """Convert the PDF file to a SVG file"""
            raise NotImplementedError

        def svg_to_group(self):
            """
            Convert the SVG file to an SVG group node.

            :Returns: Subclass of SvgElement
            """
            raise NotImplementedError


    class PstoeditPlotSvg(PdfConverterBase):
        """
        Convert PDF -> SVG using pstoedit's plot-svg backend
        """
        def __init__(self, checker=None):
            super(PstoeditPlotSvg, self).__init__(checker)

        @classmethod
        def get_pdf_converter_name(cls):
            return "pstoedit"

        def pdf_to_svg(self):
            """
            :raises: TexTextCommandNotFound, TexTextCommandFailed
            """
            # Options for pstoedit command

            with logger.debug("Converting .pdf to .svg"):

                pstoeditOpts = '-dt -ssp -psarg -r9600x9600 -pta'.split()

                # Exec pstoedit: pdf -> svg
                result = ""
                try:
                    result = exec_command([self.checker.available_pdf_to_svg_converters[self.get_pdf_converter_name()],
                                           '-f', 'plot-svg',
                                           self.tmp('pdf'),
                                           self.tmp('svg')
                                           ]
                                          + pstoeditOpts)
                except TexTextCommandFailed as error:
                    # Linux runs into this in case of DELAYBIND error
                    result = str(error)
                    if "DELAYBIND" in error.stdout+error.stderr:
                        result = "%s %s" % (
                        "The ghostscript version installed on your system is not compatible with pstoedit! "
                        "Make sure that you have not ghostscript 9.22 installed (please upgrade or downgrade "
                        "ghostscript).\n\n Detailed error message:\n", result)
                    elif "-1073741515" in error.stdout+error.stderr:
                        result = ("Call to pstoedit failed because of a STATUS_DLL_NOT_FOUND error. "
                                  "Most likely the reason for this is a missing MSVCR100.dll, i.e. you need "
                                  "to install the Microsoft Visual C++ 2010 Redistributable Package "
                                  "(search for vcredist_x86.exe or vcredist_x64.exe 2010). "
                                  "This is a problem of pstoedit, not of TexText!!")
                    raise TexTextCommandFailed(result, error.return_code, error.stdout, error.stderr)

                if not os.path.exists(self.tmp('svg')) or os.path.getsize(self.tmp('svg')) == 0:
                    raise TexTextConversionError("pstoedit didn't produce output.\n%s" % (result))

        def svg_to_group(self):
            """
            Convert the SVG file to an SVG group node.

            :returns: Subclass of SvgElement
            """
            with logger.debug("Grouping resulting svg"):
                tree = etree.parse(self.tmp('svg'))
                self._fix_xml_namespace(tree.getroot())
                try:
                    result = PsToEditSvgElement(copy.copy(tree.getroot().xpath('g')[0]))
                except IndexError:
                    raise TexTextConversionError("Can't find a group in resulting svg")
                return result

        def _fix_xml_namespace(self, node):
            svg = '{%s}' % SVG_NS

            if node.tag.startswith(svg):
                node.tag = node.tag[len(svg):]

            for key in node.attrib.keys():
                if key.startswith(svg):
                    new_key = key[len(svg):]
                    node.attrib[new_key] = node.attrib[key]
                    del node.attrib[key]

            for c in node:
                self._fix_xml_namespace(c)


    class Pdf2SvgPlotSvg(PdfConverterBase):
        """
        Convert PDF -> SVG using pdf2svg
        """

        def __init__(self, checker):
            super(Pdf2SvgPlotSvg, self).__init__(checker)

        @classmethod
        def get_pdf_converter_name(self):
            return "pdf2svg"

        def pdf_to_svg(self):
            """
            Converts the produced pdf file into a svg file using pdf2svg. Raises RuntimeError if conversion fails.
            """
            with logger.debug("Converting .pdf to .svg"):
                # Exec pdf2cvg infile.pdf outfile.svg
                result = exec_command([self.checker.available_pdf_to_svg_converters[self.get_pdf_converter_name()],
                                       self.tmp('pdf'), self.tmp('svg')])

                if not os.path.exists(self.tmp('svg')) or os.path.getsize(self.tmp('svg')) == 0:
                    raise TexTextConversionError("pdf2svg didn't produce output.\n%s" % result)

        def svg_to_group(self):
            """
            Convert the SVG file to an SVG group node. pdf2svg produces a file of the following structure:
            <svg>
                <defs>
                </defs>
                <g>
                </g>
            </svg>
            The groups in the last <g>-Element reference the symbols defined within the <def>-node. In this method
            the references in the <g>-node are replaced  by the definitions from <defs> so we can return the group without
            any <defs>.
            """
            with logger.debug("Groupping resulting svg"):
                tree = etree.parse(self.tmp('svg'))
                svg_raw = tree.getroot()

                # At first we collect all defs with an id-attribute found in the svg raw tree. They are put later directly
                # into the nodes in the <g>-Element referencing them
                path_defs = {}
                for def_node in svg_raw.xpath("//*[local-name() = \"defs\"]//*[@id]"):
                    path_defs["#" + def_node.attrib["id"]] = def_node

                try:
                    # Now we pick all nodes that have a href attribute and replace the reference in them by the appropriate
                    # path definitions from def_nodes
                    for node in svg_raw.xpath("//*"):
                        if ("{%s}href" % XLINK_NS) in node.attrib:
                            # Fetch data from node
                            node_href = node.attrib["{%s}href" % XLINK_NS]
                            node_x = node.attrib["x"]
                            node_y = node.attrib["y"]
                            node_translate = "translate(%s,%s)" % (node_x, node_y)

                            # remove the node
                            parent = node.getparent()
                            parent.remove(node)

                            # Add positional data to the svg paths
                            for svgdef in path_defs[node_href].iterchildren():
                                svgdef.attrib["transform"] = node_translate

                                # Add new node into document
                                parent.append(copy.copy(svgdef))

                    # Finally, we build the group
                    new_group = etree.Element(inkex.addNS("g"))
                    for node in svg_raw:
                        if node.tag != "{%s}defs" % SVG_NS:
                            new_group.append(node)

                    # Ensure that strokes with color "none" have zero width to ensure proper colorization via Inkscape
                    for node in new_group.getiterator(tag="{%s}path" % SVG_NS):
                        if "style" in node.attrib:
                            node_style_dict = ss.parseStyle(node.attrib["style"])
                            if "stroke" in node_style_dict and node_style_dict["stroke"].lower() == "none":
                                node_style_dict["stroke-width"] = "0"
                                node.attrib["style"] = ss.formatStyle(node_style_dict)
                    return Pdf2SvgSvgElement(new_group)
                except:  # todo: <-- be more precise here
                    raise TexTextConversionError("Can't find a group in resulting svg")


    class SvgElement(object):
        """ Holds SVG node data and provides several methods for working on the data """
        __metaclass__ = abc.ABCMeta

        def __init__(self, xml_element):
            """ Instanciates an object of type SvgElement

            :param xml_element: The node as an etree.Element object
            """
            self._node = xml_element

        def get_xml_raw_node(self):
            """ Returns the node as an etree.Element object """
            return self._node

        def is_attrib(self, attrib_name, namespace=u""):
            """ Returns True if the attibute attrib_name (str) exists in the specified namespace, otherwise false """
            return self.is_node_attrib(self._node, attrib_name, namespace)

        def get_attrib(self, attrib_name, namespace=u""):
            """
            Returns the value of the attribute attrib_name (str) in the specified namespace if it exists, otherwise None
            """
            return self.get_node_attrib(self._node, attrib_name, namespace)

        def set_attrib(self, attrib_name, attrib_value, namespace=""):
            """ Sets the attribute attrib_name (str) to the value attrib_value (str) in the specified namespace"""
            aname = self.build_full_attribute_name(attrib_name, namespace)
            # ToDo: Unicode behavior?
            self._node.attrib[aname] = str(attrib_value).encode('string-escape')

        @classmethod
        def is_node_attrib(cls, node, attrib_name, namespace=u""):
            """
            Returns True if the attibute attrib_name (str) exists in the specified namespace of the given XML node,
            otherwise False
            """
            return cls.build_full_attribute_name(attrib_name, namespace) in node.attrib.keys()

        @classmethod
        def get_node_attrib(cls, node, attrib_name, namespace=u""):
            """
            Returns the value of the attribute attrib_name (str) in the specified namespace of the given CML node
            if it exists, otherwise None
            """
            attrib_value = None
            if cls.is_node_attrib(node, attrib_name, namespace):
                aname = cls.build_full_attribute_name(attrib_name, namespace)
                attrib_value = node.attrib[aname].decode('string-escape')
            return attrib_value

        @staticmethod
        def build_full_attribute_name(attrib_name, namespace):
            """ Builds a correct namespaced attribute name """
            if namespace == "":
                return attrib_name
            else:
                return '{%s}%s' % (namespace, attrib_name)

        def get_frame(self, mat=[[1,0,0],[0,1,0]]):
            """
            Determine the node's size and position. It's accounting for the coordinates of all paths in the node's children.

            :return: x position, y position, width, height
            """
            min_x, max_x, min_y, max_y = st.computeBBox([self._node], mat)
            width = max_x - min_x
            height = max_y - min_y
            return min_x, min_y, width, height

        def get_transform_values(self):
            """
            Returns the entries a, b, c, d, e, f of self._node's transformation matrix
            depending on the transform applied. If no transform is defined all values returned are zero
            See: https://www.w3.org/TR/SVG11/coords.html#TransformMatrixDefined
            """
            a = b = c = d = e = f = 0
            if 'transform' in self._node.attrib:
                (a,c,e),(b,d,f) = st.parseTransform(self._node.attrib['transform'])
            return a, b, c, d, e, f

        def get_jacobian_sqrt(self):
            a, b, c, d, e, f = self.get_transform_values()
            det = a * d - c * b
            return math.sqrt(math.fabs(det))

        def translate(self, x, y):
            """
            Translate the node
            :param x: horizontal translation
            :param y: vertical translation
            """
            a, b, c, d, old_x, old_y = self.get_transform_values()
            new_x = float(old_x) + x
            new_y = float(old_y) + y
            transform = 'matrix(%s, %s, %s, %s, %f, %f)' % (a, b, c, d, new_x, new_y)
            self._node.attrib['transform'] = transform

        def align_to_node(self, ref_node, alignment, relative_scale):
            """
            Aligns the node represented by self to a reference node according to the settings defined by the user
            :param ref_node: Reference node subclassed from SvgElement to which self is going to be aligned
            :param alignment: A 2-element string list defining the alignment
            :param relative_scale: Scaling of the new node relative to the scale of the reference node
            """
            scale_transform = st.parseTransform("scale(%f)" % relative_scale)

            old_transform = st.parseTransform(ref_node.get_attrib('transform'))

            # Account for vertical flipping of pstoedit nodes when recompiled via pdf2svg and vice versa
            revert_flip = self._get_flip_transformation(ref_node)
            composition = st.composeTransform(old_transform, revert_flip)

            composition = st.composeTransform(scale_transform, composition)

            # keep alignment point of drawing intact, calculate required shift
            self.set_attrib('transform', st.formatTransform(composition))

            x, y, w, h = ref_node.get_frame()
            new_x, new_y, new_w, new_h = self.get_frame()

            p_old = self._get_pos(x, y, w, h, alignment)
            p_new = self._get_pos(new_x, new_y, new_w, new_h, alignment)

            dx = p_old[0] - p_new[0]
            dy = p_old[1] - p_new[1]

            composition[0][2] += dx
            composition[1][2] += dy

            self.set_attrib('transform', st.formatTransform(composition))
            self.set_attrib("jacobian_sqrt", str(self.get_jacobian_sqrt()), TEXTEXT_NS)

        @abc.abstractmethod
        def set_scale_factor(self, scale):
            """ Sets the SVG scale factor of the node """

        @abc.abstractmethod
        def is_colorized(self):
            """ Returns true if at least one element of the managed node contains a non-black fill or stroke color """

        @staticmethod
        def has_colorized_attribute(node):
            """ Returns true if at least one element of node contains a non-black fill or stroke attribute """
            for it_node in node.getiterator():
                for attrib in ["stroke", "fill"]:
                    if attrib in it_node.attrib and it_node.attrib[attrib].lower().replace(" ", "") not in ["rgb(0%,0%,0%)",
                                                                                                            "black", "none",
                                                                                                            "#000000"]:
                        return True
            return False

        @staticmethod
        def has_colorized_style(node):
            """ Returns true if at least one element of node contains a non-black fill or stroke style """
            for it_node in node.getiterator():
                if "style" in it_node.attrib:
                    node_style_dict = ss.parseStyle(it_node.attrib["style"])
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

        @abc.abstractmethod
        def _get_flip_transformation(self, ref_node):
            """
            Returns Unity ([[1,0,0],[0,1,0]]) or Reflection ([[1,0,0],[0,-1,0]]) transformation which
        is required to ensure that pstoedit nodes do not vertical flip pdf2svg nodes and vice versa,
            see derived classes.

            :param ref_node: An object subclassed from ref_node the transform in transform_as_list originally belonged to
            :return: transformation matrix as a 2-dim list
            """

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


    class PsToEditSvgElement(SvgElement):
        """ Holds SVG node data created by pstoedit """

        def __init__(self, xml_element):
            super(self.__class__, self).__init__(xml_element)

        def set_scale_factor(self, scale):
            """
            Set the node's scale factor (keeps the rest of the transform matrix)
            Note that pstoedit needs -scale at the fourth position!
            :param scale: the new scale factor
            """
            a, b, c, d, e, f = self.get_transform_values()
            transform = 'matrix(%f, %s, %s, %f, %s, %s)' % (scale, b, c, -scale, e, f)
            self._node.attrib['transform'] = transform

        def is_colorized(self):
            """ Returns true if at least one element of the node contains a non-black fill or stroke color """
            # pstoedit stores color information as attributes, not as css styles, so checking for attributes should
            # be enough. But to be on the save side...
            return self.has_colorized_attribute(self._node) or self.has_colorized_style(self._node)

        def _get_flip_transformation(self, ref_node):
            """ Fixes vertical flipping of nodes which have been originally created via pdf2svg"""
            transform_as_list = st.parseTransform("scale(1)")
            if isinstance(ref_node, Pdf2SvgSvgElement):
                transform_as_list[1][1] *= -1
            return transform_as_list


    class Pdf2SvgSvgElement(SvgElement):
        """ Holds SVG node data created by pdf2svg """

        def __init__(self, xml_element):
            super(self.__class__, self).__init__(xml_element)

        def set_scale_factor(self, scale):
            """
            Set the node's scale factor (keeps the rest of the transform matrix)
            :param scale: the new scale factor
            """
            a, b, c, d, e, f = self.get_transform_values()
            transform = 'matrix(%f, %s, %s, %f, %s, %s)' % (scale, b, c, scale, e, f)
            self._node.attrib['transform'] = transform

        def is_colorized(self):
            """ Returns true if at least one element of the node contains a non-black fill or stroke color """
            # pdf2svg consequently uses the style css properties for colorization, so checking for style should
            # be enough. But to be on the save side...
            return self.has_colorized_style(self._node) or self.has_colorized_attribute(self._node)

        def _get_flip_transformation(self, ref_node):
            """ Fixes vertical flipping of nodes which have been originally created via pstoedit """
            transform_as_list = st.parseTransform("scale(1)")
            if isinstance(ref_node, PsToEditSvgElement):
                transform_as_list[1][1] *= -1
            return transform_as_list


    CONVERTERS = {PstoeditPlotSvg.get_pdf_converter_name(): PstoeditPlotSvg,
                  Pdf2SvgPlotSvg.get_pdf_converter_name(): Pdf2SvgPlotSvg}

    #------------------------------------------------------------------------------
    # Entry point
    #------------------------------------------------------------------------------

    if __name__ == "__main__":
        effect = TexText()
        effect.affect()
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
    exit(EXIT_CODE_EXPECTED_ERROR)   # Bad setup
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
