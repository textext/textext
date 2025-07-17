"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2025 TexText developers.

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
    exec_command, version_greater_or_equal_than
from .errors import *

with open(os.path.join(os.path.dirname(__file__), "VERSION")) as version_file:
    __version__ = version_file.readline().strip()
__docformat__ = "restructuredtext en"

EXIT_CODE_OK = 0
EXIT_CODE_EXPECTED_ERROR = 1
EXIT_CODE_UNEXPECTED_ERROR = 60

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

# First install the user logger so in case anything fails with the file logger
# we have at least some information in the abort dialog
# Contributed by Thermi@github.com
user_formatter = logging.Formatter('[%(name)s][%(levelname)6s]: %(message)s')
user_log_channel = CycleBufferHandler(capacity=1024)  # store up to 1024 messages
user_log_channel.setLevel(logging.DEBUG)
user_log_channel.setFormatter(user_formatter)
__logger.addHandler(user_log_channel)

# Now we try to install the file logger.
LOG_LOCATION = os.path.join(defaults.textext_logfile_path)
if not os.path.isdir(LOG_LOCATION):
    os.makedirs(LOG_LOCATION)
LOG_FILENAME = os.path.join(LOG_LOCATION, "textext.log") # ToDo: When not writable continue but give a message somewhere
file_log_channel = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                                        maxBytes=500 * 1024,  # up to 500 kB
                                                        backupCount=2,  # up to two log files
                                                        encoding="utf-8"
                                                        )
file_log_channel.setLevel(logging.NOTSET)
file_log_channel.setFormatter(log_formatter)
__logger.addHandler(file_log_channel)

import inkex
import inkex.command as ixc
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

        self.config = Settings(directory=defaults.textext_config_path)
        self.cache = Cache(directory=defaults.textext_config_path)
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
            "--recompile-all",
            action="store_true"
        )

        self.arg_parser.add_argument(
            "--tex_command",
            type=str,
            default=self.DEFAULT_TEXCMD
        )

    def _recompile_all(self):
        """
        Mutate ``self.svg`` to recompile all textext entries.
        This can be invoked from command-line as::

            python3 /path/to/textext/__main__.py --recompile-all        > edited.svg < original.svg
            python3 /path/to/textext/__main__.py --recompile-all --output edited.svg < original.svg

        In the first form ``edited.svg`` must not be the same as ``original.svg``,
        in the second form it is probably fine (although do make a backup).
        """
        for node in self.find_all_textext_nodes(self.svg):
            node.__class__ = TexTextElement
            text, preamble_file, scale = node.get_all_info()
            alignment = node.get_meta_alignment()
            new_node = self._do_convert_one(text, preamble_file, scale, alignment, self.options.tex_command)
            self._replace_node(node, new_node, scale, alignment, scale)

    def effect(self):
        """Perform the effect: create/modify TexText objects"""
        with logger.debug("TexText.effect"):

            if self.options.recompile_all:
                self._recompile_all()
                return

            # Find root element
            try:
                old_svg_ele, text, preamble_file, current_scale = self.get_old()
                error_thrown_by_get_old = None
            except RuntimeError as e:
                old_svg_ele, text, preamble_file, current_scale = None, "", "", None
                error_thrown_by_get_old = e

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

                alignment = old_svg_ele.get_meta_alignment()

                current_tex_command = old_svg_ele.get_meta("texconverter", current_tex_command)

            gui_config = self.config.get("gui", {})

            # Ask for TeX code
            if self.options.text is None:
                global_scale_factor = self.options.scale_factor

                if not preamble_file:
                    logger.debug("Using default preamble file `%s`" % self.options.preamble_file)
                    if current_tex_command != "typst":
                        preamble_file = "default_packages.tex"
                    else:
                        preamble_file = "default_preamble_typst.typ"
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
                            if current_tex_command != "typst":
                                preamble_file = "default_packages.tex"
                            else:
                                preamble_file = "default_preamble_typst.typ"

                        else:
                            logger.debug("Preamble file is found along with default preamble file")
                    else:
                        logger.debug("Preamble file found by absolute path")

                if not os.path.isfile(preamble_file):
                    logger.debug("Preamble file is not found")
                    preamble_file = ""

                from .asktext import load_asktext_tk, load_asktext_gtk
                toolkit = gui_config.get("toolkit", None)
                if "use_gtk_source" in gui_config and toolkit != "gtk":
                    raise RuntimeError("invalid config, use_gtk_source cannot be specified when toolkit != gtk")
                if toolkit == "tk":
                    AskTextImpl = load_asktext_tk()
                elif toolkit == "gtk":
                    use_gtk_source = gui_config.get("use_gtk_source", None)
                    AskTextImpl = load_asktext_gtk(use_gtk_source=use_gtk_source)
                elif toolkit is None:
                    try:
                        AskTextImpl = load_asktext_gtk()
                    except (ImportError, TypeError, ValueError):
                        try:
                            AskTextImpl = load_asktext_tk()
                        except ImportError:
                            raise RuntimeError("\nNeither GTK nor TKinter is available!\nMake sure that at least one of these "
                                               "bindings for the graphical user interface of TexText is installed! Refer to the "
                                               "installation instructions on https://textext.github.io/textext/ !")
                else:
                    raise RuntimeError(f"Unknown toolkit {repr(toolkit)}. Must be one of 'tk', 'gtk' or None.")

                asker = AskTextImpl(__version__, text, preamble_file, global_scale_factor, current_scale,
                                    current_alignment=alignment, current_texcmd=current_tex_command,
                                    tex_commands=sorted(list(
                                      self.requirements_checker.available_tex_to_pdf_converters.keys())),
                                    gui_config=gui_config)

                if error_thrown_by_get_old:
                    asker.show_error_dialog("TexText Error", "Error with user selection",
                                            error_thrown_by_get_old)
                    raise error_thrown_by_get_old

                def save_callback(_text, _preamble, _scale, alignment=TexText.DEFAULT_ALIGNMENT,
                                  tex_cmd=TexText.DEFAULT_TEXCMD):
                    return self.do_convert(_text, _preamble, _scale, old_svg_ele,
                                           alignment,
                                           tex_command=tex_cmd,
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
                if error_thrown_by_get_old:
                    raise error_thrown_by_get_old
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
                                original_scale=current_scale
                                )

    @staticmethod
    def find_all_textext_nodes(svg):
        # svg: has the same type as self.svg
        return svg.xpath(
                './/svg:g[@textext:text]',
                namespaces={'svg': SVG_NS, 'textext': TEXTEXT_NS})


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
                    if tex_command == "typst":
                        converter.typ_to_any(tex_executable, text, preamble_file, 'pdf')
                    else:
                        converter.tex_to_pdf(tex_executable, text, preamble_file)
                    converter.pdf_to_png(white_bg=white_bg)
                    image_setter(converter.tmp('png'))

    def _do_convert_one(self, text: str, preamble_file, user_scale_factor, alignment, tex_command):
        """
        Does the conversion using the selected converter.
        See documentation in do_convert for more details.
        """
        tex_executable = self.requirements_checker.available_tex_to_pdf_converters[tex_command]

        with logger.debug("Converting tex to svg"):
            with ChangeToTemporaryDirectory():
                converter = TexToPdfConverter(self.requirements_checker)
                if tex_command == "typst":
                    converter.typ_to_any(tex_executable, text, preamble_file, 'svg')
                else:
                    converter.tex_to_pdf(tex_executable, text, preamble_file)
                    converter.pdf_to_svg()

                tt_node = TexTextElement(converter.tmp("svg"), self.svg.unit)

        # -- Store textext attributes
        tt_node.set_meta("version", __version__)
        tt_node.set_meta("texconverter", tex_command)
        tt_node.set_meta("pdfconverter", 'inkscape')
        tt_node.set_meta_text(text)
        tt_node.set_meta("preamble", preamble_file)
        tt_node.set_meta("scale", str(user_scale_factor))
        tt_node.set_meta("alignment", str(alignment))
        try:
            inkscape_version = self.document.getroot().get('inkscape:version')
            tt_node.set_meta("inkscapeversion", inkscape_version.split(' ')[0])
        except AttributeError as ignored:
            # Unfortunately when this node comes from an Inkscape document that has never been saved before
            # no version attribute is provided by Inkscape :-(
            pass

        return tt_node

    def _add_new_node(self, tt_node, user_scale_factor):
        from inkex import Transform

        with logger.debug("Adding new node to document"):
            # Place new nodes in the view center and scale them according to user request
            node_center = tt_node.bounding_box().center
            view_center = self.svg.namedview.center

            # Since Inkscape 1.2 (= extension API version 1.2.0) view_center is in px,
            # not in doc units! Hence, we need to convert the value to the document unit.
            # so the transform is correct later.
            if hasattr(inkex, "__version__"):
                if version_greater_or_equal_than(inkex.__version__, "1.2.0"):
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
            full_layer_transform = Transform()
            for layer in layers:
                full_layer_transform @= layer.transform

            # Place the node in the center of the view. Here we need to be aware of
            # transforms in the layers, hence the inverse layer transformation
            tt_node.transform = (-full_layer_transform @               # map to view coordinate system
                                 Transform(translate=view_center) @    # place at view center
                                 Transform(scale=user_scale_factor) @  # scale
                                 Transform(translate=-node_center) @   # place node at origin
                                 tt_node.transform                     # use original node transform
                                 )

            tt_node.set_meta('jacobian_sqrt', str(tt_node.get_jacobian_sqrt()))

            tt_node.set_none_strokes_to_0pt()

            self.svg.get_current_layer().add(tt_node)

    def _replace_node(self, old_svg_ele, tt_node, user_scale_factor, alignment, original_scale):
        with logger.debug("Replacing node in document"):
            # Rescale existing nodes according to user request
            relative_scale = user_scale_factor / original_scale
            tt_node.align_to_node(old_svg_ele, alignment, relative_scale)

            # If no non-black color has been explicitily set by TeX we copy the color information
            # from the old node so that coloring done in Inkscape is preserved.
            if not tt_node.is_colorized():
                tt_node.import_group_color_style(old_svg_ele)

            self.replace_node(old_svg_ele, tt_node)

    def do_convert(self, text, preamble_file, user_scale_factor, old_svg_ele, alignment, tex_command,
                   original_scale=None):
        """
        Does the conversion using the selected converter.

        :param text:
        :param preamble_file:
        :param user_scale_factor:
        :param old_svg_ele:
        :param alignment:
        :param tex_command: The tex command to be used for tex -> pdf ("pdflatex", "xelatex", "lualatex")
        :param original_scale Scale factor of old node
        """
        with logger.debug("TexText.do_convert"):
            with logger.debug("args:"):
                for k, v in list(locals().items()):
                    logger.debug("%s = %s" % (k, repr(v)))

            if not text:
                logger.debug("no text, return")
                return

            if isinstance(text, bytes):
                text = text.decode('utf-8')

            tt_node = self._do_convert_one(text, preamble_file, user_scale_factor, alignment, tex_command)

            # Place new node in document
            if old_svg_ele is None:
                self._add_new_node(tt_node, user_scale_factor)
            else:
                self._replace_node(old_svg_ele, tt_node, user_scale_factor, alignment, original_scale)

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

        :return: (old_svg_ele, latex_text, preamble_file_name, scale)
        :rtype: (TexTextElement, str, str, float, bool)
        """

        layer = self.svg.get_current_layer()
        if any(TexTextElement.to_textext_node(a) for a in [layer, *layer.iterancestors()]):
            raise RuntimeError("A subgroup of a TexText object is selected. Please close this message, press "
                               "CTRL + BACKSPACE (possibly multiple times) until the complete TexText object "
                               "is selected. Then, run TexText again.")

        for node in self.svg.selected.values():
            if not TexTextElement.to_textext_node(node):
                if any(TexTextElement.to_textext_node(a) for a in node.iterancestors()):
                    raise RuntimeError("A subgroup of a TexText object is selected. Please close this message, press "
                                       "CTRL + BACKSPACE (possibly multiple times) until the complete TexText object "
                                       "is selected. Then, run TexText again.")
                node = node.getparent()
                continue
            return node, *node.get_all_info()

        return None, "", "", None

    def replace_node(self, old_node, new_node):
        """
        Replace an XML node old_node with new_node.
        This is only ever called from _replace_node. The parent is responsible
        for positioning the node correctly.
        """
        parent = old_node.getparent()
        index = parent.index(old_node)
        old_id = old_node.get_id()
        parent[index] = new_node
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
    DEFAULT_DOCUMENT_CLASS=r"\documentclass{article}"
    DOCUMENT_TEMPLATE = r"""
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
        
        # If a file with the name "LATEX_OPTIONS" exists in the textext plugin directory, we interpret each line 
        # in that file not starting with "#" as a separate option to be passed to the latex command.
        # This can be used to customize the latex command line options - if needed
        # (for example when choosing to add the -shell-escape option)
        self.latex_options_path = os.path.join(os.path.dirname(__file__), "LATEX_OPTIONS")
        if os.path.exists(self.latex_options_path):
            with open(self.latex_options_path, 'r') as f:
                # Remove lines starting with "#" and empty lines
                self.LATEX_OPTIONS = [option for option in
                                      [s.strip() for s in f.read().splitlines()] if option and not option.startswith("#")]

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

            # Add default document class to preamble if necessary
            if not _contains_document_class(preamble):
                preamble = self.DEFAULT_DOCUMENT_CLASS + preamble

            # Options pass to LaTeX-related commands

            texwrapper = self.DOCUMENT_TEMPLATE % (preamble, latex_text)

            # Convert TeX to PDF

            # Write tex
            with open(self.tmp('tex'), mode='w', encoding='utf-8') as f_tex:
                f_tex.write(texwrapper)

            # Exec tex_command: tex -> pdf
            try:
                
                # Previously, the LATEX_OPTIONS were appended to the end of the command. This causes issues 
                # then the -shell-escape option is used. For some reason, it seems to only be recognized when 
                # appearing before the input file. Therefore, there options are added in between the command 
                # and the input file path here.
                command = [tex_command, *self.LATEX_OPTIONS, self.tmp('tex')]
                exec_command(command)
                
            except TexTextCommandFailed as error:
                
                if os.path.exists(self.tmp('log')):
                    parsed_log = self.parse_pdf_log()
                    raise TexTextConversionError(parsed_log, error.return_code, error.stdout, error.stderr)
                else:
                    raise TexTextConversionError(str(error), error.return_code, error.stdout, error.stderr)

            if not os.path.exists(self.tmp('pdf')):
                raise TexTextConversionError("%s didn't produce output %s" % (tex_command, self.tmp('pdf')))

    def typ_to_any(self, typst_command, typst_text, preamble_file, file_type):
        """
        Create a PDF file from latex text
        """

        with logger.debug("Converting .typ to .{0}".format(file_type)):
            # Read preamble
            preamble = ""
            preamble_file = os.path.abspath(preamble_file)
            if os.path.isfile(preamble_file):
                with open(preamble_file, 'r') as f:
                    preamble += f.read()

            # Write typ code
            with open(self.tmp('typ'), mode='w', encoding='utf-8') as f_typ:
                f_typ.write(f"{preamble}\n\n#set page(fill:none)\n\n{typst_text}")

            # Exec tex_command: tex -> pdf
            try:
                exec_command([typst_command, "compile", self.tmp('typ'), self.tmp(file_type)])
            except TexTextCommandFailed as error:
                raise TexTextConversionError(str(error), error.return_code, error.stdout, error.stderr)

            if not os.path.exists(self.tmp(file_type)):
                raise TexTextConversionError("%s didn't produce output %s" % (typst_command, self.tmp(file_type)))

    def pdf_to_svg(self):
        """Convert the PDF file to a SVG file"""
        kwargs = dict()
        kwargs["export_filename"] = self.tmp('svg')
        kwargs["pdf_poppler"] = True
        kwargs["pages"] = 1
        kwargs["export_type"] = "svg"
        kwargs["export_text_to_path"] = True
        kwargs["export_area_drawing"] = True

        ixc.inkscape(self.tmp('pdf'), **kwargs)

    def pdf_to_png(self, white_bg):
        """Convert the PDF file to a PNG file"""
        kwargs = dict()
        kwargs["export_filename"] = self.tmp('png')
        kwargs["pdf_poppler"] = True
        kwargs["pages"] = 1
        kwargs["export_type"] = "png"
        kwargs["export_dpi"] = 300
        kwargs["export_area_drawing"] = True
        if white_bg:
            kwargs["export_background"] = 300
            kwargs["export-background-opacity"] = 1.0

        ixc.inkscape(self.tmp('pdf'), **kwargs)

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


def _contains_document_class(preamble):
    """Return True if `preamble` contains a documentclass-like command.
    
    Also, checks and considers if the command is commented out or not.
    """
    lines = preamble.split("\n")
    document_commands = ["\\documentclass{", "\\documentclass[",
                        "\\documentstyle{", "\\documentstyle["]
    for line in lines:
        for document_command in document_commands:
            if (document_command in line
                and "%" not in line.split(document_command)[0]):
                return True
    return False


class TexTextElement(inkex.Group):
    tag_name = "g"

    def __init__(self, svg_filename, document_unit):
        """
        :param svg_filename: The name of the file containing the svg-snippet
        :param document_unit: String specifying the unit of the document into which the node is going
                              to be placed ("mm", "pt", ...)
        """
        super(TexTextElement, self).__init__()
        self._svg_to_textext_node(svg_filename, document_unit)

    @staticmethod
    def to_textext_node(node):
        """
        Mutate node.__class__ to TexTextElement if it is detected
        to be a TexText node.

        :return: whether the node is detected as a TexText node
        :rtype: bool
        """
        if node.tag_name != TexTextElement.tag_name:
            return False
        c = node.__class__
        try:
            node.__class__ = TexTextElement
            _ = node.get_all_info()
            return True
        except (TypeError, AttributeError):
            node.__class__ = c
            return False

    def _svg_to_textext_node(self, svg_filename, document_unit):
        from inkex import ShapeElement, Defs, SvgDocumentElement
        doc = etree.parse(svg_filename, parser=inkex.SVG_PARSER)

        root = doc.getroot()

        TexTextElement._expand_defs(root)

        shape_elements = [el for el in root if isinstance(el, (ShapeElement, Defs))]
        root.append(self)

        for el in shape_elements:
            self.append(el)

        self.make_ids_unique()

        self.pure_hlines_to_paths()

        # Ensure that snippet is correctly scaled according to the units of the document
        # We scale it here such that its size is correct in the document units
        # (Usually pt returned from poppler to mm in the main document)
        self.transform.add_scale(root.uutounit("1{}".format(root.unit), document_unit))

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
                group.transform = Transform(translate=(float(el.get("x", "0")), float(el.get("y", "0"))))

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
        To avoid confusion between objects with same id from two or more TexText objects we replace
        auto-generated ids from the converter with random unique values
        """
        self.set_random_ids(prefix=None, levels=-1, backlinks=True)

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

    def get_meta_alignment(self):
        return self.get_meta('alignment', TexText.DEFAULT_ALIGNMENT)

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

    def get_all_info(self):
        text = self.get_meta_text()
        preamble_file = self.get_meta('preamble')
        scale = float(self.get_meta('scale', 1.0))
        return text, preamble_file, scale

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

        composition = scale_transform @ old_transform @ revert_flip

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

        composition = Transform(translate=(dx, dy)) @ composition

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

    def pure_hlines_to_paths(self):
        """ Transforms horizontal lines from strokes to paths

        This makes coloring in Inkscape easier later since all other elements are paths, too.
        The color can be set by selecting the fill color. Without this function one would
        need to pick horizontal lines manually and set their stroke color instead of the fill
        color. Applies to frac and sqrt commands
        """
        for it in self.iter():
            if it.tag_name == "path":
                # Horizontal lines are defined as "M 0,8.656723 H 5.6953123" or
                # m 0,8.656723 h 5.6953123
                match_obj = re.search(r"^([Mm])\s(\d+.?\d*),(\d+.?\d*)\s([Hh])\s(\d+.?\d*)$", it.attrib["d"])
                if not match_obj:
                    continue

                # Take the stroke data (start position, draw line command, width and color)
                m = match_obj.group(1)  # Move-command
                x1 = float(match_obj.group(2))
                y1 = float(match_obj.group(3))
                h = match_obj.group(4)  # Draw line command
                dh = float(match_obj.group(5))
                sw = float(it.attrib["stroke-width"])
                color = it.attrib["stroke"]

                # Draw path, colorize it and remove all other attributes
                it.attrib["d"] = f"{m} {x1},{y1 - 0.5 * sw} {h} {dh} v {sw} H {x1} Z"
                it.attrib["fill"] = color
                for key in it.attrib.keys():
                    if key not in ["id", "d", "fill"]:
                        del it.attrib[key]

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
