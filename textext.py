#!/usr/bin/env python
"""
=======
textext
=======

:Author: Pauli Virtanen <pav@iki.fi>
:Date: 2008-04-26
:Author: Pit Garbe <piiit@gmx.de>
:Date: 2014-02-03
:License: BSD

Textext is an extension for Inkscape_ that allows adding
LaTeX-generated text objects to your SVG drawing. What's more, you can
also *edit* these text objects after creating them.

This brings some of the power of TeX typesetting to Inkscape.

Textext was initially based on InkLaTeX_ written by Toru Araki,
but is now rewritten.

Thanks to Robert Szalai, Rafal Kolanski, Brian Clarke, and Florent Becker
for contributions.

.. note::
   Unfortunately, the TeX input dialog is modal. That is, you cannot
   do anything else with Inkscape while you are composing the LaTeX
   text snippet.

   This is because I have not yet worked out whether it is possible to
   write asynchronous extensions for Inkscape.

.. note::
   Textext requires Pdflatex and one of the following
     - Pdf2svg_
     - Pstoedit_ compiled with the ``plot-svg`` back-end

.. _Pstoedit: http://www.pstoedit.net/pstoedit
.. _Pdf2svg: http://www.cityinthesky.co.uk/pdf2svg.html
.. _Inkscape: http://www.inkscape.org/
.. _InkLaTeX: http://www.kono.cis.iwate-u.ac.jp/~arakit/inkscape/inklatex.html
"""

__version__ = "0.5"
__docformat__ = "restructuredtext en"

import sys
import os
import glob
import platform
import re

DEBUG = False

MAC = "Mac OS"
WINDOWS = "Windows"
PLATFORM = platform.system()

if PLATFORM == MAC:
    sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions')
    sys.path.append('/usr/local/lib/python2.7/site-packages')
    sys.path.append('/usr/local/lib/python2.7/site-packages/gtk-2.0')
elif PLATFORM == WINDOWS:
    sys.path.append(r'C:/Program Files/Inkscape/share/extensions')

sys.path.append(os.path.dirname(__file__))

import inkex
import tempfile
import re
import copy
import hashlib
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

messages = []

LOG_LEVEL_ERROR = "Error Log Level"
LOG_LEVEL_DEBUG = "Debug Log Level"

from asktext import AskerFactory

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

    def effect(self):
        """Perform the effect: create/modify TexText objects"""
        global CONVERTERS

        # Pick a converter
        converter_errors = []

        usable_converter_class = None
        for converter_class in CONVERTERS:
            try:
                converter_class.available()
                usable_converter_class = converter_class
                break
            except StandardError, err:
                converter_errors.append("%s: %s" % (converter_class.__name__, str(err)))

        if not usable_converter_class:
            die("No Latex -> SVG converter available:\n%s" % ';\n'.join(converter_errors))

        # Find root element
        old_node, text, preamble_file = self.get_old()

        # Ask for TeX code
        if self.options.text is None:
            scale_factor = self.options.scale_factor

            if not preamble_file:
                preamble_file = self.options.preamble_file

            if not os.path.isfile(preamble_file):
                preamble_file = ""

            asker = AskerFactory().asker(text, preamble_file, scale_factor)
            try:
                asker.ask(lambda t, p, s: self.do_convert(t, p, s, usable_converter_class, old_node),
                          lambda t, p, c: self.preview_convert(t, p, usable_converter_class, c))
            except RuntimeError:
                raise

        else:
            self.do_convert(self.options.text,
                            self.options.preamble_file,
                            self.options.scale_factor, usable_converter_class, old_node)

        show_log()

    def preview_convert(self, text, preamble_file, converter_class, image_setter_callback):
        """
        Generates a preview PNG of the LaTeX output using the selected converter.

        :param text:
        :param preamble_file:
        :param converter_class:
        :param image_setter_callback: A callback to execute with the file path of the generated PNG
        """
        if not text:
            return

        if isinstance(text, unicode):
            text = text.encode('utf-8')

        converter = converter_class()

        cwd = os.getcwd()
        try:
            converter.tex_to_pdf(text, preamble_file)

            # convert resulting pdf to png
            try:
                options = ['-density', '200', '-background', 'transparent', converter.tmp('pdf'), converter.tmp('png')]

                if PLATFORM == WINDOWS:
                    import _winreg
                    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"Software\ImageMagick\Current")
                    path = _winreg.QueryValueEx(key, "LibPath")[0]
                    exec_command([path + '\\' + 'convert'] + options)
                else:
                    exec_command(['convert'] + options)

                image_setter_callback(converter.tmp('png'))
            except RuntimeError:
                add_log_message("Could not convert PDF to PNG. Please make sure that ImageMagick is installed.",
                                LOG_LEVEL_ERROR)
                raise RuntimeError(latest_message())
        except OSError, WindowsError:
            pass
        finally:
            os.chdir(cwd)
            converter.finish()

    def do_convert(self, text, preamble_file, scale_factor, converter_class, old_node):
        """
        Does the conversion using the selected converter.

        :param text:
        :param preamble_file:
        :param scale_factor:
        :param converter_class:
        :param old_node:
        """
        if not text:
            return

        if isinstance(text, unicode):
            text = text.encode('utf-8')

        # Convert
        converter = converter_class()
        try:
            new_node = converter.convert(text, preamble_file, scale_factor)
        finally:
            converter.finish()
            pass

        if new_node is None:
            add_log_message("No new Node!", LOG_LEVEL_DEBUG)
            return


        # -- Set textext attribs
        new_node.attrib['{%s}text' % TEXTEXT_NS] = text.encode('string-escape')
        new_node.attrib['{%s}preamble' % TEXTEXT_NS] = preamble_file.encode('string-escape')

        # -- Copy style
        if old_node is None:
            self.set_node_color(new_node, "black")

            root = self.document.getroot()
            width = inkex.unittouu(root.get('width'))
            height = inkex.unittouu(root.get('height'))

            w, h = self.get_node_size(new_node, scale_factor)
            self.translate_node(new_node, (width - w) / 2, (height + h) / 2)

            self.current_layer.append(new_node)
        else:
            # copy old transform but apply the current scale factor
            try:
                new_node.attrib['transform'] = old_node.attrib['transform']
            except (KeyError, IndexError, TypeError, AttributeError):
                pass

            try:
                new_node.attrib['transform'] = old_node.attrib['{%s}transform' % SVG_NS]
            except (KeyError, IndexError, TypeError, AttributeError):
                pass

            # calculate the size difference between the old and new node and translate the new node to keep it centered
            old_scale = self.get_node_scale_factor(old_node)

            self.set_node_scale_factor(new_node, scale_factor)

            w_old, h_old = self.get_node_size(old_node, old_scale)
            w_new, h_new = self.get_node_size(new_node, scale_factor)

            w_diff = w_old - w_new
            h_diff = h_old - h_new

            self.translate_node(new_node, w_diff / 2, -h_diff / 2)

            self.replace_node(old_node, new_node)

        # -- Save settings
        if os.path.isfile(preamble_file):
            self.settings.set('preamble', preamble_file)
        else:
            self.settings.set('preamble', '')

        if scale_factor is not None:
            self.settings.set('scale', scale_factor)
        self.settings.save()

    def get_old(self):
        """
        Dig out LaTeX code and name of preamble file from old
        TexText-generated objects.

        :return: (old_node, latex_text, preamble_file_name)
        """

        for i in self.options.ids:
            node = self.selected[i]
            # ignore, if node tag has SVG_NS Namespace
            if node.tag != '{%s}g' % SVG_NS:
                continue

            # otherwise, check for TEXTEXT_NS in attrib
            if '{%s}text' % TEXTEXT_NS in node.attrib:
                return (node,
                        node.attrib.get('{%s}text' % TEXTEXT_NS, '').decode('string-escape'),
                        node.attrib.get('{%s}preamble' % TEXTEXT_NS, '').decode('string-escape'))
        return None, "", ""

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
        """
        Copy all style attributes from the old to the new node, including the children, since TexText nodes are groups.
        :param old_node:
        :param new_node:
        """
        style_attrs = ['fill', 'fill-opacity', 'fill-rule', 'font-size-adjust', 'font-stretch', 'font-style',
                       'font-variant', 'font-weight', 'letter-spacing', 'stroke', 'stroke-dasharray', 'stroke-linecap',
                       'stroke-linejoin', 'stroke-miterlimit', 'stroke-opacity', 'text-anchor', 'word-spacing', 'style']

        for attribute_name in style_attrs:
            try:
                if attribute_name in old_node.keys():
                    old_attribute = old_node.attrib[attribute_name]
                else:
                    continue

                new_node.attrib[attribute_name] = old_attribute

                for child in new_node.iterchildren():
                    child.attrib[attribute_name] = old_attribute

            except (KeyError, IndexError, TypeError, AttributeError):
                add_log_message("Problem setting attribute %s" % attribute_name, LOG_LEVEL_DEBUG)

        old_node_has_fill_color = False
        if "fill" in old_node.keys():
            old_fill = old_node.attrib["fill"]
            if old_fill != "none" and old_fill is not None and old_fill != "":
                old_node_has_fill_color = True

        if not old_node_has_fill_color:
            TexText.set_node_color(new_node, "black")

    # ------ SVG Node utilities
    @staticmethod
    def set_node_color(node, color):
        """
        Set a nodes fill color
        :param node: which node
        :param color: what color, i.e. "red" or "#ff0000" or "rgb(255,0,0)"
        """
        node.attrib["fill"] = color
        for child in node.iterchildren():
            child.attrib["fill"] = color

    def get_node_size(self, node, scale):
        """
        Determine the node's size

        It's a good approximation, accounting for the coordinates of all paths in the node's children.
        Somehow the height isn't exact, but good enough.

        :param node:
        :param scale: The scale factor to take into account
        :return: width, height
        """
        text = ""
        pattern = re.compile(r"\d+\.\d+,\d+\.\d+")

        for child in node.iterchildren():
            d = child.attrib['d']
            text = text + " " + d

        points = re.findall(pattern, text)

        xValues = []
        yValues = []

        for point in points:
            x, y = point.split(",", 1)
            xValues.append(float(x))
            yValues.append(float(y))

        minX = min(xValues)
        maxX = max(xValues)

        minY = min(yValues)
        maxY = max(yValues)

        width = (maxX - minX) * float(scale)
        height = (maxY - minY) * float(scale)

        return width, height

    def get_node_scale_factor(self, node):
        """
        Extract the scale factor from the node's transform attribute
        :param node:
        :return: scale factor
        """
        a, b, c, d, e, f = self.get_node_transform(node)
        return a

    def set_node_scale_factor(self, node, scale):
        """
        Set the node's scale factor (keeps the rest of the transform matrix)
        :param node:
        :param scale: the new scale factor
        """
        a, b, c, d, e, f = self.get_node_transform(node)
        transform = 'matrix(%f, %s, %s, %f, %s, %s)' % (scale, b, c, -scale, e, f)
        node.attrib['transform'] = transform

    def translate_node(self, node, x, y):
        """
        Translate the node
        :param node:
        :param x: horizontal translation
        :param y: vertical translation
        """
        a, b, c, d, old_x, old_y = self.get_node_transform(node)
        new_x = float(old_x) + x
        new_y = float(old_y) + y
        transform = 'matrix(%s, %s, %s, %s, %f, %f)' % (a, b, c, d, new_x, new_y)
        node.attrib['transform'] = transform

    def get_node_transform(self, node):
        """
        Gets the matrix values form the node's transform attribute
        :param node:
        :return: a, b, c, d, e, f   (the values of the transform matrix)
        """
        transform = node.attrib['transform']
        transform = transform.split('(', 1)[1].split(')')[0]
        a, b, c, d, e, f = transform.split(',')
        return a, b, c, d, e, f


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
                    if not '=' in line:
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
    import subprocess

    def exec_command(cmd, ok_return_value=0):
        """
        Run given command, check return value, and return
        concatenated stdout and stderr.
        :param cmd: Command to execute
        :param ok_return_value: The expected return value after successful completion
        """

        try:
            # hides the command window for cli tools that are run (in Windows)
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

    program_files = os.environ.get('PROGRAMFILES')
    if program_files:
        paths += glob.glob(os.path.join(program_files, 'gs/gs*/bin'))
        paths += glob.glob(os.path.join(program_files, 'pstoedit*'))
        paths += glob.glob(os.path.join(program_files, 'miktex*/miktex/bin'))

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

    def convert(self, latex_text, preamble_file, scale_factor):
        """
        Return an XML node containing latex text

        :param latex_text: Latex code to use
        :param preamble_file: Name of a preamble file to include
        :param scale_factor: Scale factor to use if object doesn't have a ``transform`` attribute.

        :return: XML DOM node
        """
        raise NotImplementedError

    @classmethod
    def available(cls):
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

    def tex_to_pdf(self, latex_text, preamble_file):
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
        \documentclass[preview]{standalone}
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

        # Exec pdflatex: tex -> pdf
        try:
            exec_command(['pdflatex', self.tmp('tex')] + latexOpts)
        except RuntimeError as error:
            parsed_log = self.parse_pdf_log(self.tmp('log'))
            add_log_message(parsed_log, LOG_LEVEL_ERROR)
            raise RuntimeError("Your LaTeX code has problems:\n\n{errors}".format(errors=parsed_log))

        if not os.path.exists(self.tmp('pdf')):
            add_log_message("pdflatex didn't produce output %s" % self.tmp('pdf'), LOG_LEVEL_ERROR)
            raise RuntimeError(latest_message())

        return

    def parse_pdf_log(self, logfile):
        """
        Strip down pdflatex output to only the warnings, errors etc. and discard all the noise
        :param logfile:
        :return: string
        """
        import logging
        from StringIO import StringIO

        log_buffer = StringIO()
        log_handler = logging.StreamHandler(log_buffer)

        from typesetter import Typesetter

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
        """Remove temporary files"""
        base = os.path.join(self.tmp_path, self.tmp_base)
        for filename in glob.glob(base + '*'):
            self.try_remove(filename)
        self.try_remove(self.tmp_path)

    @staticmethod
    def try_remove(filename):
        """Try to remove given file, skipping if it doesn't exist"""
        if os.path.isfile(filename):
            os.remove(filename)
        elif os.path.isdir(filename):
            os.rmdir(filename)


class PdfConverterBase(LatexConverterBase):
    def convert(self, latex_text, preamble_file, scale_factor):
        cwd = os.getcwd()
        try:
            os.chdir(self.tmp_path)
            self.tex_to_pdf(latex_text, preamble_file)
            self.pdf_to_svg()
        finally:
            os.chdir(cwd)

        new_node = self.svg_to_group()
        if new_node is None:
            return None

        if scale_factor is not None:
            new_node.attrib['transform'] = self.get_transform(scale_factor)
        return new_node

    def pdf_to_svg(self):
        """Convert the PDF file to a SVG file"""
        raise NotImplementedError

    def get_transform(self, scale_factor):
        """Get a suitable default value for the transform attribute"""
        raise NotImplementedError

    def svg_to_group(self):
        """
        Convert the SVG file to an SVG group node.

        :Returns: <svg:g> node
        """
        tree = etree.parse(self.tmp('svg'))
        self.fix_xml_namespace(tree.getroot())
        try:
            return copy.copy(tree.getroot().xpath('g')[0])
        except IndexError:
            return None

    def fix_xml_namespace(self, node):
        svg = '{%s}' % SVG_NS

        if node.tag.startswith(svg):
            node.tag = node.tag[len(svg):]

        for key in node.attrib.keys():
            if key.startswith(svg):
                new_key = key[len(svg):]
                node.attrib[new_key] = node.attrib[key]
                del node.attrib[key]

        for c in node:
            self.fix_xml_namespace(c)


class PstoeditPlotSvg(PdfConverterBase):
    """
    Convert PDF -> SVG using pstoedit's plot-svg backend
    """

    def get_transform(self, scale_factor):
        return 'matrix(%f,0,0,%f,%f,%f)' % (
            scale_factor, -scale_factor,
            0, 0)

    def pdf_to_svg(self):
        # Options for pstoedit command
        pstoeditOpts = '-dt -ssp -psarg -r9600x9600'.split()

        # Exec pstoedit: pdf -> svg
        exec_command(['pstoedit', '-f', 'plot-svg',
                      self.tmp('pdf'), self.tmp('svg')]
                     + pstoeditOpts)
        if not os.path.exists(self.tmp('svg')):
            add_log_message("pstoedit didn't produce output", LOG_LEVEL_ERROR)
            raise RuntimeError(latest_message())

    @classmethod
    def available(cls):
        """Check whether pstoedit has plot-svg available"""
        out = exec_command(['pstoedit', '-help'], ok_return_value=None)
        if 'version 3.44' in out and 'Ubuntu' in out:
            add_log_message("Pstoedit version 3.44 on Ubuntu found, but it contains too many bugs to be usable",
                            LOG_LEVEL_DEBUG)
        if 'plot-svg' not in out:
            add_log_message("Pstoedit not compiled with plot-svg support", LOG_LEVEL_DEBUG)


class Pdf2Svg(PdfConverterBase):
    """
    Convert PDF -> SVG using pdf2svg
    """

    def __init__(self):
        PdfConverterBase.__init__(self)
        self.hash = None

    def convert(self, *a, **kw):
        # compute hash for generating unique ids for sub-elements
        m = hashlib.md5()
        m.update('%s%s' % (a, kw))
        self.hash = m.hexdigest()[:8]
        return PdfConverterBase.convert(self, *a, **kw)

    def pdf_to_svg(self):
        exec_command(['pdf2svg', self.tmp('pdf'), self.tmp('svg'), '1'])

    def get_transform(self, scale_factor):
        return 'scale(%f,%f)' % (scale_factor, scale_factor)

    def svg_to_group(self):
        # create xml.dom representation of the TeX file
        tree = etree.parse(self.tmp('svg'))
        root = tree.getroot()
        self.fix_xml_namespace(root)

        href_map = {}

        # Map items to new ids
        for i, el in enumerate(root.xpath('//*[attribute::id]')):
            cur_id = el.attrib['id']
            new_id = "%s%s-%d" % (ID_PREFIX, self.hash, i)
            href_map['#' + cur_id] = "#" + new_id
            el.attrib['id'] = new_id

        # Replace hrefs
        url_re = re.compile('^url\((.*)\)$')

        for el in root.xpath('//*[attribute::xlink:href]', namespaces=NSS):
            href = el.attrib['{%s}href' % XLINK_NS]
            el.attrib['{%s}href' % XLINK_NS] = href_map.get(href, href)

        for el in root.xpath('//*[attribute::svg:clip-path]', namespaces=NSS):
            value = el.attrib['clip-path']
            m = url_re.match(value)
            if m:
                el.attrib['clip-path'] = \
                    'url(%s)' % href_map.get(m.group(1), m.group(1))

        # Bundle everything in a single group
        master_group = etree.SubElement(root, 'g')
        for c in root:
            if c is master_group: continue
            master_group.append(c)

        return copy.copy(master_group)

    @classmethod
    def available(cls):
        """Check whether pdf2svg is available, raise RuntimeError if not"""
        exec_command(['pdf2svg'], ok_return_value=254)


CONVERTERS = [Pdf2Svg, PstoeditPlotSvg]

#------------------------------------------------------------------------------
# Entry point
#------------------------------------------------------------------------------

if __name__ == "__main__":
    effect = TexText()
    effect.affect()
