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
:Date: 2018-05-24
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

__version__ = "0.8.2"
__docformat__ = "restructuredtext en"

import os
import sys
import math
import platform
import subprocess

DEBUG = False

MAC = "Darwin"
WINDOWS = "Windows"
PLATFORM = platform.system()

if PLATFORM == MAC:
    sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions')
    sys.path.append('/usr/local/lib/python2.7/site-packages')
    sys.path.append('/usr/local/lib/python2.7/site-packages/gtk-2.0')

sys.path.append(os.path.dirname(__file__))

import inkex
import simplestyle as ss
import simpletransform as st
import tempfile
import abc
import copy
from lxml import etree

if PLATFORM == WINDOWS:
    import win_app_paths as wap

TEXTEXT_NS = u"http://www.iki.fi/pav/software/textext/"
SVG_NS = u"http://www.w3.org/2000/svg"
XLINK_NS = u"http://www.w3.org/1999/xlink"

ID_PREFIX = "textext-"

NSS = {
    u'textext': TEXTEXT_NS,
    u'svg': SVG_NS,
    u'xlink': XLINK_NS,
}

messages = []

LOG_LEVEL_ERROR = "Error Log Level"
LOG_LEVEL_DEBUG = "Debug Log Level"

from asktext import AskerFactory

# Due to Inkscape 0.92.2 path problem placed here and not in LatexConverterBase.parse_pdf_log
from typesetter import Typesetter

#------------------------------------------------------------------------------
# Inkscape plugin functionality
#------------------------------------------------------------------------------


def die(message=""):
    """
    Terminate the program with an optional error message while also emitting all accumulated warnings.
    :param message: Optional error message.
    :raise SystemExit:
    """
    if message:
        add_log_message(message, LOG_LEVEL_ERROR)
    show_log()
    raise SystemExit(1)


def show_log():
    """
    Show log in popup, if there are error messages.
    Include debug messages as well, when there are some.
    """
    filtered_messages = messages
    if not DEBUG:
        filtered_messages = filter(lambda (m, l): l != LOG_LEVEL_DEBUG, filtered_messages)

    if len(filtered_messages) > 0:
        rendered_messages = map(render_message, filtered_messages)
        inkex.errormsg("\n".join(rendered_messages))


def add_log_message(message, level):
    """
    Insert a log message and its log level
    :param message: Text
    :param level: log level, can be LOG_LEVEL_DEBUG or LOG_LEVEL_ERROR
    """
    messages.append((message, level))


def render_message((message, level)):
    """
    Render message tuple to output string
    :return: string
    """
    if level == LOG_LEVEL_DEBUG:
        prefix = "(D)"
    elif level == LOG_LEVEL_ERROR:
        prefix = "(E)"
    else:
        prefix = "(Invalid Log Level - {level})".format(level=level)

    return "{prefix}: {message}".format(prefix=prefix, message=message)


def latest_message():
    """
    Return the latest message from the log, without indication of log level.
    :return: The message text
    """
    return messages[-1][0]


class TexText(inkex.Effect):

    DEFAULT_ALIGNMENT = "middle center"
    DEFAULT_TEXCMD = "pdflatex"

    def __init__(self):
        inkex.Effect.__init__(self)

        self.settings = Settings()

        self.OptionParser.add_option(
            "-t", "--text", action="store", type="string",
            dest="text",
            default=None)
        self.OptionParser.add_option(
            "-p", "--preamble-file", action="store", type="string",
            dest="preamble_file",
            default=self.settings.get('preamble', str, "default_packages.tex"))
        self.OptionParser.add_option(
            "-s", "--scale-factor", action="store", type="float",
            dest="scale_factor",
            default=self.settings.get('scale', float, 1.0))

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
        global CONVERTERS

        # Pick a converter
        converter_errors = []

        usable_converter_class = None
        for converter_class in CONVERTERS:
            try:
                converter_class.check_available()
                usable_converter_class = converter_class
                break
            except StandardError, err:
                converter_errors.append("%s: %s" % (converter_class.__name__, str(err)))

        if not usable_converter_class:
            die("No Latex -> SVG converter available:\n%s" % ';\n'.join(converter_errors))

        # Find root element
        old_svg_ele, text, preamble_file, current_scale = self.get_old()

        # This is very important when re-editing nodes which have been created using TexText <= 0.7. It ensures that
        # the scale factor which is displayed in the AskText dialog is adjusted in such a way that the size of the node
        # is preserved when recompiling the LaTeX code. ("version" attribute introduced in 0.7.1)
        if (old_svg_ele is not None) and (not old_svg_ele.is_attrib("version", TEXTEXT_NS)):
            current_scale *= self.uu_to_unit(1, "pt")

        if old_svg_ele is not None and old_svg_ele.is_attrib("jacobian_sqrt", TEXTEXT_NS):
            current_scale *= old_svg_ele.get_jacobian_sqrt()/float(old_svg_ele.get_attrib("jacobian_sqrt", TEXTEXT_NS))

        alignment = TexText.DEFAULT_ALIGNMENT

        if old_svg_ele is not None and old_svg_ele.is_attrib("alignment", TEXTEXT_NS):
            alignment = old_svg_ele.get_attrib("alignment", TEXTEXT_NS)

        current_tex_command = TexText.DEFAULT_TEXCMD
        if old_svg_ele is not None and old_svg_ele.is_attrib("texconverter", TEXTEXT_NS):
            current_tex_command = old_svg_ele.get_attrib("texconverter", TEXTEXT_NS)

        # Ask for TeX code
        if self.options.text is None:
            global_scale_factor = self.options.scale_factor

            if not preamble_file:
                preamble_file = self.options.preamble_file
            else:
                # Check if preamble file exists at the specified absolute path location. If not, check to find
                # the file in the default path. If this fails, too, fallback to the default.
                if not os.path.exists(preamble_file):
                    preamble_file = os.path.join(os.path.dirname(self.options.preamble_file), os.path.basename(preamble_file))
                    if not os.path.exists(preamble_file):
                        preamble_file = self.options.preamble_file

            if not os.path.isfile(preamble_file):
                preamble_file = ""

            asker = AskerFactory().asker(__version__, text, preamble_file, global_scale_factor, current_scale,
                                         current_alignment=alignment, current_texcmd=current_tex_command)
            try:

                def callback(_text, _preamble, _scale, alignment=TexText.DEFAULT_ALIGNMENT,
                             tex_cmd=TexText.DEFAULT_TEXCMD):
                    return self.do_convert(_text, _preamble, _scale, usable_converter_class, old_svg_ele, alignment,
                                           tex_cmd, original_scale=current_scale)

                asker.ask(callback,
                          lambda _text, _preamble, _preview_callback, _tex_command: self.preview_convert(_text,
                                                                                                         _preamble,
                                                                                                         usable_converter_class,
                                                                                                         _preview_callback,
                                                                                                         _tex_command))
            finally:
                pass

        else:
            # ToDo: I think this is completely broken...
            self.do_convert(self.options.text,
                            self.options.preamble_file,
                            self.options.scale_factor, usable_converter_class, old_svg_ele)

        show_log()

    @staticmethod
    def preview_convert(text, preamble_file, converter_class, image_setter, tex_command):
        """
        Generates a preview PNG of the LaTeX output using the selected converter.

        :param text:
        :param preamble_file:
        :param converter_class:
        :param image_setter: A callback to execute with the file path of the generated PNG
        :param tex_command: Command for tex -> pdf
        """
        if not text:
            return

        if isinstance(text, unicode):
            text = text.encode('utf-8')

        converter = converter_class()

        cwd = os.getcwd()
        try:
            converter.tex_to_pdf(tex_command, text, preamble_file)

            # convert resulting pdf to png using ImageMagick's 'convert' or 'magick'
            try:
                # -trim MUST be placed between the filenames!
                options = ['-density', '200', '-background', 'transparent', converter.tmp('pdf'),
                           '-trim', converter.tmp('png')]

                if PLATFORM == WINDOWS:
                    win_command = wap.get_imagemagick_command()
                    if not win_command:
                        raise RuntimeError()
                    exec_command([win_command] + options)
                else:
                    try:
                        exec_command(['convert'] + options)   # ImageMagick 6
                    except OSError:
                        exec_command(['magick'] + options)    # ImageMagick 7

                image_setter(converter.tmp('png'))
            except RuntimeError as error:
                add_log_message("Could not convert PDF to PNG. Please make sure that ImageMagick is installed.\nDetailed error message:\n%s" % (str(error)),
                                LOG_LEVEL_ERROR)
                raise RuntimeError(latest_message())
        except Exception as error:
            if isinstance(error, OSError):
                pass
            elif PLATFORM == WINDOWS and isinstance(error, WindowsError):
                pass
            else:
                raise
        finally:
            os.chdir(cwd)
            converter.finish()

    def do_convert(self, text, preamble_file, user_scale_factor, converter_class, old_svg_ele, alignment, tex_command,
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
        if not text:
            return

        if isinstance(text, unicode):
            text = text.encode('utf-8')

        # Coordinates in node from converter are always in pt, we have to scale them such that the node size is correct
        # even if the document user units are not in pt
        scale_factor = user_scale_factor * self.unit_to_uu("1pt")

        # Convert
        converter = converter_class()
        try:
            new_svg_ele = converter.convert(text, preamble_file, scale_factor, tex_command)
        finally:
            converter.finish()

        if new_svg_ele is None:
            add_log_message("No new Node!", LOG_LEVEL_DEBUG)
            return

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
            root = self.document.getroot()
            width = self.unit_to_uu(self.get_document_width())
            height = self.unit_to_uu(self.get_document_height())

            x, y, w, h = new_svg_ele.get_frame()
            new_svg_ele.translate(-x + width/2 -w/2, -y+height/2 -h/2)
            new_svg_ele.set_attrib('jacobian_sqrt', str(new_svg_ele.get_jacobian_sqrt()), TEXTEXT_NS)

            self.current_layer.append(new_svg_ele.get_xml_raw_node())
        else:
            relative_scale = user_scale_factor / original_scale
            new_svg_ele.align_to_node(old_svg_ele, alignment, relative_scale)

            # If no non-black color has been explicitily set by TeX we copy the color information from the old node
            # so that coloring done in Inkscape is preserved.
            if not new_svg_ele.is_colorized():
                new_svg_ele.import_group_color_style(old_svg_ele)

            self.replace_node(old_svg_ele.get_xml_raw_node(), new_svg_ele.get_xml_raw_node())

        # -- Save settings
        if os.path.isfile(preamble_file):
            self.settings.set('preamble', preamble_file)
        else:
            self.settings.set('preamble', '')

        # ToDo: Do we really need this if statement?
        if scale_factor is not None:
            self.settings.set('scale', user_scale_factor)
        self.settings.save()

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


class Settings(object):
    def __init__(self):
        self.values = {}

        if PLATFORM == WINDOWS:
            self.keyname = r"Software\TexText\TexText"
        else:
            self.filename = os.path.expanduser("~/.inkscape/textextrc")

        self.load()

    def load(self):
        if PLATFORM == WINDOWS:
            import _winreg

            try:
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, self.keyname)
            except WindowsError:
                return
            try:
                self.values = {}
                for j in range(1000):
                    try:
                        name, data, dtype = _winreg.EnumValue(key, j)
                    except EnvironmentError:
                        break
                    self.values[name] = str(data)
            finally:
                key.Close()
        else:
            try:
                f = open(self.filename, 'r')
            except (IOError, OSError):
                return
            try:
                self.values = {}
                for line in f.read().split("\n"):
                    if '=' not in line:
                        continue
                    k, v = line.split("=", 1)
                    self.values[k.strip()] = v.strip()
            finally:
                f.close()

    def save(self):
        if PLATFORM == WINDOWS:
            import _winreg

            try:
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                      self.keyname,
                                      0,
                                      _winreg.KEY_SET_VALUE | _winreg.KEY_WRITE)
            except WindowsError:
                key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, self.keyname)
            try:
                for k, v in self.values.iteritems():
                    _winreg.SetValueEx(key, str(k), 0, _winreg.REG_SZ, str(v))
            finally:
                key.Close()
        else:
            d = os.path.dirname(self.filename)
            if not os.path.isdir(d):
                os.makedirs(d)

            f = open(self.filename, 'w')
            try:
                data = '\n'.join(["%s=%s" % (k, v) for k, v in self.values.iteritems()])
                f.write(data)
            finally:
                f.close()

    def get(self, key, typecast, default=None):
        try:
            return typecast(self.values[key])
        except (KeyError, ValueError, TypeError):
            return default

    def set(self, key, value):
        self.values[key] = str(value)


#------------------------------------------------------------------------------
# LaTeX converters
#------------------------------------------------------------------------------

try:
    def exec_command(cmd, ok_return_value=0):
        """
        Run given command, check return value, and return
        concatenated stdout and stderr.
        :param cmd: Command to execute
        :param ok_return_value: The expected return value after successful completion
        """

        try:
            # hides the command window for cli tools that are run (in Windows)
            info = None
            if PLATFORM == WINDOWS:
                info = subprocess.STARTUPINFO()
                info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                info.wShowWindow = subprocess.SW_HIDE

            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 startupinfo=info)
            out, err = p.communicate()
        except OSError, err:
            add_log_message("Command %s failed: %s" % (' '.join(cmd), err), LOG_LEVEL_DEBUG)
            raise RuntimeError(latest_message())

        if ok_return_value is not None and p.returncode != ok_return_value:
            add_log_message("Command %s failed (code %d): %s" % (' '.join(cmd), p.returncode, out + err),
                            LOG_LEVEL_DEBUG)
            raise RuntimeError(latest_message())
        return out + err

except ImportError:
    # Python < 2.4 ...
    import popen2


    def exec_command(cmd, ok_return_value=0):
        """
        Run given command, check return value, and return
        concatenated stdout and stderr.
        """

        # XXX: unix-only!

        try:
            p = popen2.Popen4(cmd, True)
            p.tochild.close()
            returncode = p.wait() >> 8
            out = p.fromchild.read()
        except OSError, err:
            add_log_message("Command %s failed: %s" % (' '.join(cmd), err), LOG_LEVEL_DEBUG)
            raise RuntimeError(latest_message())

        if ok_return_value is not None and returncode != ok_return_value:
            add_log_message("Command %s failed (code %d): %s" % (' '.join(cmd), returncode, out), LOG_LEVEL_DEBUG)
            raise RuntimeError(latest_message())
        return out

if PLATFORM == WINDOWS:
    # Try to add some commonly needed paths to PATH
    paths = os.environ.get('PATH', '').split(os.path.pathsep)

    additional_path = ""
    new_path_element = wap.get_pstoedit_dir()
    if new_path_element:
        if new_path_element != wap.IS_IN_PATH:
            paths += [os.path.join(new_path_element)]
    else:
        add_log_message(wap.get_last_error(), LOG_LEVEL_ERROR)
        raise RuntimeError(latest_message())

    new_path_element = wap.get_ghostscript_dir()
    if new_path_element:
        if new_path_element != wap.IS_IN_PATH:
            paths += [os.path.join(new_path_element)]
    else:
        add_log_message(wap.get_last_error(), LOG_LEVEL_ERROR)
        raise RuntimeError(latest_message())

    os.environ['PATH'] = os.path.pathsep.join(paths)


class LatexConverterBase(object):
    """
    Base class for Latex -> SVG converters
    """

    # --- Public api

    def __init__(self):
        """
        Initialize Latex -> SVG converter.
        """
        self.tmp_path = tempfile.mkdtemp()
        self.tmp_base = 'tmp'

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

    @classmethod
    def check_available(cls):
        """
        :Returns: Check if converter is available, raise RuntimeError if not
        """
        pass

    def finish(self):
        """
        Clean up any temporary files
        """
        self.remove_temp_files()

    # --- Internal
    def tmp(self, suffix):
        """
        Return a file name corresponding to given file suffix,
        and residing in the temporary directory.
        """
        return os.path.join(self.tmp_path, self.tmp_base + '.' + suffix)

    def tex_to_pdf(self, tex_command, latex_text, preamble_file):
        """
        Create a PDF file from latex text
        """

        # Read preamble
        preamble = ""
        if os.path.isfile(preamble_file):
            f = open(preamble_file, 'r')
            preamble += f.read()
            f.close()

        # Options pass to LaTeX-related commands
        latexOpts = ['-interaction=nonstopmode',
                     '-halt-on-error']

        texwrapper = r"""
        \documentclass{article}
        %s
        \pagestyle{empty}
        \begin{document}
        %s
        \end{document}
        """ % (preamble, latex_text)

        # Convert TeX to PDF

        # Write tex
        os.chdir(self.tmp_path)
        f_tex = open(self.tmp('tex'), 'w')
        try:
            f_tex.write(texwrapper)
        finally:
            f_tex.close()

        # Exec tex_command: tex -> pdf
        try:
            # lualatex does not like the backslash, even on Windows... So we always pass it unix-like but with
            # a drive letter.
            exec_command([tex_command, self.tmp('tex').replace('\\', '/')] + latexOpts)
        except RuntimeError as error:
            if os.path.exists(self.tmp('log')):
                parsed_log = self.parse_pdf_log(self.tmp('log'))
                add_log_message(parsed_log, LOG_LEVEL_ERROR)
                raise RuntimeError("Your LaTeX code has problems:\n\n{errors}".format(errors=parsed_log))
            else:
                add_log_message(error.message, LOG_LEVEL_ERROR)
                raise RuntimeError(latest_message())

        if not os.path.exists(self.tmp('pdf')):
            add_log_message("%s didn't produce output %s" % (tex_command, self.tmp('pdf')), LOG_LEVEL_ERROR)
            raise RuntimeError(latest_message())

        return

    def parse_pdf_log(self, logfile):
        """
        Strip down tex output to only the warnings, errors etc. and discard all the noise
        :param logfile:
        :return: string
        """
        import logging
        from StringIO import StringIO

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


    def remove_temp_files(self):
        """Remove temporary files and directory"""
        for base, dirs, files in os.walk(self.tmp_path, topdown=False):
            for filename in files:
                os.remove(os.path.join(base, filename))
            for dirname in dirs:
                os.rmdir(os.path.join(base, dirname))
        os.rmdir(self.tmp_path)


class PdfConverterBase(LatexConverterBase):

    def convert(self, latex_text, preamble_file, scale_factor, tex_command):
        cwd = os.getcwd()
        try:
            os.chdir(self.tmp_path)
            self.tex_to_pdf(tex_command, latex_text, preamble_file)
            self.pdf_to_svg()
        finally:
            os.chdir(cwd)

        new_svg_ele = self.svg_to_group()
        if new_svg_ele is None:
            return None

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

    @staticmethod
    def get_pdf_converter_name():
        return "pstoedit"

    def pdf_to_svg(self):
        # Options for pstoedit command
        pstoeditOpts = '-dt -ssp -psarg -r9600x9600 -pta'.split()

        # Exec pstoedit: pdf -> svg
        delay_bind_error = False
        result = ""
        try:
            result = exec_command(['pstoedit', '-f', 'plot-svg',
                                   self.tmp('pdf'), self.tmp('svg')]
                                  + pstoeditOpts)
        except RuntimeError as excpt:
            # Linux runs into this in case of DELAYBIND error
            if "DELAYBIND" in excpt.message:
                delay_bind_error = True
                result += excpt.message
            else:
                # Process rare STATUS_DLL_NOT_FOUND = 0xC0000135 error (DWORD)
                if "-1073741515" in excpt.message:
                    add_log_message("Call to pstoedit failed because of a STATUS_DLL_NOT_FOUND error. "
                                    "Most likely the reason for this is a missing MSVCR100.dll, i.e. you need "
                                    "to install the Microsoft Visual C++ 2010 Redistributable Package "
                                    "(search for vcredist_x86.exe or vcredist_x64.exe 2010). "
                                    "This is a problem of pstoedit, not of TexText!!", LOG_LEVEL_ERROR)
                raise RuntimeError(latest_message())
        if not os.path.exists(self.tmp('svg')) or os.path.getsize(self.tmp('svg')) == 0:
            # Windows runds into this in case of DELAYBIND error
            if "DELAYBIND" in result:
                delay_bind_error = True
            else:
                add_log_message("pstoedit didn't produce output.\n%s" % (result), LOG_LEVEL_ERROR)
                raise RuntimeError(latest_message())

        if delay_bind_error:
            result = "%s %s" % ("The ghostscript version installed on your system is not compatible with pstoedit! "
                                "Make sure that you have not ghostscript 9.22 installed (please upgrade or downgrade "
                                "ghostscript).\n\n Detailed error message:\n", result)
            add_log_message(result, LOG_LEVEL_ERROR)
            raise RuntimeError(latest_message())

    def svg_to_group(self):
        """
        Convert the SVG file to an SVG group node.

        :Returns: Subclass of SvgElement
        """
        tree = etree.parse(self.tmp('svg'))
        self._fix_xml_namespace(tree.getroot())
        try:
            return PsToEditSvgElement(copy.copy(tree.getroot().xpath('g')[0]))
        except IndexError:
            return None

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

    @classmethod
    def check_available(cls):
        """Check whether pstoedit has plot-svg"""
        out = exec_command(['pstoedit', '-help'], ok_return_value=None)
        if 'version 3.44' in out and 'Ubuntu' in out:
            add_log_message("Pstoedit version 3.44 on Ubuntu found, but it contains too many bugs to be usable",
                            LOG_LEVEL_DEBUG)
        if 'plot-svg' not in out:
            add_log_message("Pstoedit not compiled with plot-svg support", LOG_LEVEL_DEBUG)


class Pdf2SvgPlotSvg(PdfConverterBase):
    """
    Convert PDF -> SVG using pdf2svg
    """

    @staticmethod
    def get_pdf_converter_name():
        return "pdf2svg"

    def pdf_to_svg(self):
        """
        Converts the produced pdf file into a svg file using pdf2svg. Raises RuntimeError if conversion fails.
        """
        try:
            # Exec pdf2cvg infile.pdf outfile.svg
            result = exec_command(['pdf2svg', self.tmp('pdf'), self.tmp('svg')])
        except RuntimeError as excpt:
            add_log_message("Command pdf2svg failed: %s" % (excpt))
            raise RuntimeError(latest_message())

        if not os.path.exists(self.tmp('svg')) or os.path.getsize(self.tmp('svg')) == 0:
            add_log_message("pdf2svg didn't produce output.\n%s" % (result), LOG_LEVEL_ERROR)
            raise RuntimeError(latest_message())

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

            # return new_group
            return Pdf2SvgSvgElement(new_group)

        except:
            return None

    @classmethod
    def check_available(cls):
        """
        Check if pdf2svg is available
        """
        out = exec_command(['pdf2svg', '--help'], ok_return_value=None)


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
        self._node.attrib[aname] = attrib_value.encode('string-escape')

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
        revert_flip = self._check_and_fix_transform(ref_node, [[1,0,0],[0,1,0]])
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
    def _check_and_fix_transform(self, ref_node, transform_as_list):
        """
        Modifies - if necessary - the transformation matrix stored in transform_as_list which has its origin
        from ref_node such that no unexepcted behavior occurs if applied to the node managed by self.

        This is required to ensure that pstoedit nodes do not vertical flip pdf2svg nodes and vice versa, see
        derived classes.

        :param ref_node: An object subclassed from ref_node the transform in transform_as_list originally belonged to
        :param transform_as_list: The transformation matrix as a 2-dim list [[a,c,e],[b,d,f]]
        :return: The modified or original transformation matrix as a 2-dim list.
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

    def _check_and_fix_transform(self, ref_node, transform_as_list):
        """ Fixes vertical flipping of nodes which have been originally created via pdf2svg"""
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

    def _check_and_fix_transform(self, ref_node, transform_as_list):
        """ Fixes vertical flipping of nodes which have been originally created via pstoedit """
        if isinstance(ref_node, PsToEditSvgElement):
            transform_as_list[1][1] *= -1
        return transform_as_list


CONVERTERS = [Pdf2SvgPlotSvg, PstoeditPlotSvg]

#------------------------------------------------------------------------------
# Entry point
#------------------------------------------------------------------------------

if __name__ == "__main__":
    effect = TexText()
    effect.affect()
