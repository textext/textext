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

Thanks to Robert Szalai, Rafal Kolanski, Brian Clarke, Florent Becker and Vladislav Gavryusev
for contributions.

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

__version__ = "0.7"
__docformat__ = "restructuredtext en"

import os
import sys
import glob
import platform
import subprocess

DEBUG = False

MAC = "Mac OS"
WINDOWS = "Windows"
PLATFORM = platform.system()

if PLATFORM == MAC:
    sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions')
    sys.path.append('/usr/local/lib/python2.7/site-packages')
    sys.path.append('/usr/local/lib/python2.7/site-packages/gtk-2.0')

sys.path.append(os.path.dirname(__file__))

import inkex
import simplestyle as ss
import tempfile
import re
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
                converter_class.check_available()
                usable_converter_class = converter_class
                break
            except StandardError, err:
                converter_errors.append("%s: %s" % (converter_class.__name__, str(err)))

        if not usable_converter_class:
            die("No Latex -> SVG converter available:\n%s" % ';\n'.join(converter_errors))

        # Find root element
        old_node, text, preamble_file, current_scale = self.get_old()

        # This is very important when re-editing nodes which have been created using TexText <= 0.7. It ensures that
        # the scale factor which is displayed in the AskText dialog is adjusted in such a way that the size of the node
        # is preserved when recompiling the LaTeX code.
        if (old_node is not None) and ('{%s}version' % TEXTEXT_NS not in old_node.attrib.keys()):
            try:
                # Inkscape > 0.48
                current_scale *= self.uutounit(1, "pt")
            except AttributeError:
                # Inkscape <= 0.48
                current_scale *= inkex.uutounit(1, "pt")

        # Ask for TeX code
        if self.options.text is None:
            global_scale_factor = self.options.scale_factor

            if not preamble_file:
                preamble_file = self.options.preamble_file

            if not os.path.isfile(preamble_file):
                preamble_file = ""

            asker = AskerFactory().asker(text, preamble_file, global_scale_factor, current_scale)
            try:
                asker.ask(lambda _text, _preamble, _scale: self.do_convert(_text, _preamble, _scale,
                                                                           usable_converter_class,
                                                                           old_node),
                          lambda _text, _preamble, _preview_callback: self.preview_convert(_text, _preamble,
                                                                                           usable_converter_class,
                                                                                           _preview_callback))
            finally:
                pass

        else:
            self.do_convert(self.options.text,
                            self.options.preamble_file,
                            self.options.scale_factor, usable_converter_class, old_node)

        show_log()

    @staticmethod
    def preview_convert(text, preamble_file, converter_class, image_setter):
        """
        Generates a preview PNG of the LaTeX output using the selected converter.

        :param text:
        :param preamble_file:
        :param converter_class:
        :param image_setter: A callback to execute with the file path of the generated PNG
        """
        if not text:
            return

        if isinstance(text, unicode):
            text = text.encode('utf-8')

        converter = converter_class()

        cwd = os.getcwd()
        try:
            converter.tex_to_pdf(text, preamble_file)

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

    def do_convert(self, text, preamble_file, scale_factor_from_user, converter_class, old_node):
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

        # Coordinates in node from converter are always in pt, we have to scale them such that the node size is correct
        # even if the document user units are not in pt
        try:
            # Inkscape > 0.48
            scale_factor = scale_factor_from_user*self.unittouu("1pt")
        except AttributeError:
            # Inkscape <= 0.48
            scale_factor = scale_factor_from_user*inkex.unittouu("1pt")

        # Convert
        converter = converter_class()
        try:
            new_node = converter.convert(text, preamble_file, scale_factor)
        finally:
            converter.finish()

        if new_node is None:
            add_log_message("No new Node!", LOG_LEVEL_DEBUG)
            return

        # -- Store textext attributes
        new_node.attrib['{%s}version' % TEXTEXT_NS] = __version__.encode('string-escape')
        new_node.attrib['{%s}texconverter' % TEXTEXT_NS] = "pdflatex".encode('string-escape')
        new_node.attrib['{%s}pdfconverter' % TEXTEXT_NS] = "pstoedit".encode('string-escape')
        new_node.attrib['{%s}text' % TEXTEXT_NS] = text.encode('string-escape')
        new_node.attrib['{%s}preamble' % TEXTEXT_NS] = preamble_file.encode('string-escape')
        new_node.attrib['{%s}scale' % TEXTEXT_NS] = str(scale_factor_from_user).encode('string-escape')

        # -- Copy style
        if old_node is None:
            self.set_node_color(new_node, "black")

            root = self.document.getroot()
            try:
                # -- for Inkscape version 0.91
                width = self.unittouu(root.get('width'))
                height = self.unittouu(root.get('height'))
            except AttributeError:
                # -- for Inkscape version 0.48
                width = inkex.unittouu(root.get('width'))
                height = inkex.unittouu(root.get('height'))

            x, y, w, h = self.get_node_frame(new_node, scale_factor)
            self.translate_node(new_node, (width - w) / 2.0 - x, (height + h) / 2.0 + y)

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

            x_old, y_old, w_old, h_old = self.get_node_frame(old_node, old_scale)
            x_new, y_new, w_new, h_new = self.get_node_frame(new_node, scale_factor)

            w_diff = w_old - w_new
            h_diff = h_old - h_new

            x_diff = x_old - x_new
            y_diff = y_old - y_new

            self.translate_node(new_node, w_diff / 2.0 + x_diff, -h_diff / 2.0 - y_diff)

            self.replace_node(old_node, new_node)

        # -- Save settings
        if os.path.isfile(preamble_file):
            self.settings.set('preamble', preamble_file)
        else:
            self.settings.set('preamble', '')

        if scale_factor is not None:
            self.settings.set('scale', scale_factor_from_user)
        self.settings.save()

    def get_old(self):
        """
        Dig out LaTeX code and name of preamble file from old
        TexText-generated objects.

        :return: (old_node, latex_text, preamble_file_name, scale)
        """

        for i in self.options.ids:
            node = self.selected[i]
            # ignore, if node tag has SVG_NS Namespace
            if node.tag != '{%s}g' % SVG_NS:
                continue

            # otherwise, check for TEXTEXT_NS in attrib
            if '{%s}text' % TEXTEXT_NS in node.attrib:
                scale = None
                if '{%s}scale' % TEXTEXT_NS in node.attrib:
                    scale_string = node.attrib.get('{%s}scale' % TEXTEXT_NS, '').decode('string-escape')
                    scale = float(scale_string)

                text = node.attrib.get('{%s}text' % TEXTEXT_NS, '').decode('string-escape')
                preamble = node.attrib.get('{%s}preamble' % TEXTEXT_NS, '').decode('string-escape')

                return node, text, preamble, scale
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
        TexText.set_node_style_color(node, color)  # for fill in the style attribute
        for child in node.iterchildren():
            child.attrib["fill"] = color
            TexText.set_node_style_color(child, color)  # for fill in the style attribute

    @staticmethod
    def set_node_style_color(node, color):
        """
        If node contains a style attribute which is a CSS attribute string the
        value fill of this string is set to color
        :param node: which node
        :param color: what color, i.e. "red" or "#ff0000" or "rgb(255,0,0)"
        """
        if "style" in node.keys():
            old_style_dict = ss.parseStyle(node.attrib["style"])
            if "fill" in old_style_dict.keys():
                old_style_dict["fill"] = color
                node.attrib["style"] = ss.formatStyle(old_style_dict)

    @staticmethod
    def path_from_node(node):
        return node.attrib['d']

    @staticmethod
    def line_from_node(node):
        return 'M{x1},{y1} L{x2},{y2}'.format(x1=node.attrib['x1'],
                                              x2=node.attrib['x2'],
                                              y1=node.attrib['y1'],
                                              y2=node.attrib['y2'])

    def get_node_frame(self, node, scale):
        """
        Determine the node's size and position

        It's accounting for the coordinates of all paths in the node's children.

        :param node:
        :param scale: The scale factor to take into account
        :return: x, y, width, height
        """

        # match coordinates in SVG path data (see: http://www.w3.org/TR/SVG/paths.html#PathData)
        # 1. zero or more letters
        # 2. zero or more spaces
        # 3. optional minus sign
        # 4. at least one digit + optional dot + optional digits
        # 5. zero or one of the following group:
        # 5.1 comma
        # 5.2 optional minus sign
        # 5.3 at least one digit + optional dot + optional digits
        # This matches stuff like:
        #   "L152.47,698.78"
        #   "C151.82,703.7"
        #   "151,701.63"
        #   "500.01"
        #   "54"
        #   "c 35,45.0"
        #   "v 0"
        # etc.
        pattern = re.compile(r"[a-zA-Z]*\s*\-?\d+\.?\d*(,\-?\d+\.?\d*)?")
        text = ""

        name_space = "{{{ns}}}".format(ns=SVG_NS)
        for child in node.iterchildren():
            tag = child.tag
            if tag.startswith(name_space):
                tag = tag[len(name_space):]

            if tag == "path":
                text += "  " + self.path_from_node(child)
            elif tag == "line":
                text += "  " + self.line_from_node(child)

        points = [match.group() for match in re.finditer(pattern, text)]

        x_values = []
        y_values = []

        if points[0][0] == "m":
            absolute = False
        elif points[0][0] == "M":
            absolute = True
        else:
            # Guessing
            absolute = True

        current_x, current_y = 0, 0
        x, y = 0, 0

        if absolute:
            for point in points:
                point = point.lstrip()
                first_letter = point[0]

                if not first_letter.isdigit() and not first_letter == "-":
                    command = first_letter
                    point = point[1:].lstrip()

                if command in "MLC":  # Move, Line, Cubic Curve
                    x, y = point.split(",", 1)
                elif command == "H":  # Horizontal (just one coordinate part)
                    x, y = point, current_y
                elif command == "V":  # Vertical (just one coordinate part)
                    x, y = current_x, point

                current_x = float(x)
                current_y = float(y)
                x_values.append(current_x)
                y_values.append(current_y)
        else:
            for point in points:
                point = point.lstrip()
                first_letter = point[0]

                if not first_letter.isdigit() and not first_letter == "-":
                    command = first_letter
                    point = point[1:].lstrip()

                    if command == "m":
                        current_x, current_y = 0, 0  # reset base coordinate ('m' at the beginning of path is absolute)

                if command in "mlc":  # move, line, cubic curve
                    x, y = point.split(",", 1)
                elif command in "h":  # horizontal (only one coordinate part)
                    x, y = point, 0
                elif command in "v":  # vertical (only one coordinate part)
                    x, y = 0, point

                current_x += float(x)
                current_y += float(y)
                x_values.append(current_x)
                y_values.append(current_y)

        scale = float(scale)
        min_x = min(x_values) * scale
        max_x = max(x_values) * scale
        min_y = min(y_values) * scale
        max_y = max(y_values) * scale

        width = (max_x - min_x)
        height = (max_y - min_y)

        return min_x, min_y, width, height

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

    @staticmethod
    def get_node_transform(node):
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
            paths += glob.glob(os.path.join(new_path_element))
    else:
        add_log_message(wap.get_last_error(), LOG_LEVEL_ERROR)
        raise RuntimeError(latest_message())

    new_path_element = wap.get_ghostscript_dir()
    if new_path_element:
        if new_path_element != wap.IS_IN_PATH:
            paths += glob.glob(os.path.join(new_path_element))
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
        pstoeditOpts = '-dt -ssp -psarg -r9600x9600 -pta'.split()

        # Exec pstoedit: pdf -> svg
        try:
            result = exec_command(['pstoedit', '-f', 'plot-svg',
                                   self.tmp('pdf'), self.tmp('svg')]
                                   + pstoeditOpts)
        except RuntimeError as excpt:
            # Process rare STATUS_DLL_NOT_FOUND = 0xC0000135 error (DWORD)
            if "-1073741515" in excpt.message:
                add_log_message("Call to pstoedit failed because of a STATUS_DLL_NOT_FOUND error. "
                                "Most likely the reason for this is a missing MSVCR100.dll, i.e. you need "
                                "to install the Microsoft Visual C++ 2010 Redistributable Package "
                                "(search for vcredist_x86.exe or vcredist_x64.exe 2010). "
                                "This is a problem of pstoedit, not of TexText!!", LOG_LEVEL_ERROR)
            raise RuntimeError(latest_message())
        if not os.path.exists(self.tmp('svg')) or os.path.getsize(self.tmp('svg')) == 0:
            # Check for broken pstoedit due to deprecated DELAYBIND option in ghostscript            
            if "DELAYBIND" in result:
                result += "Ensure that a ghostscript version < 9.21 is installed on your system!\n"
            add_log_message("pstoedit didn't produce output.\n%s" % (result), LOG_LEVEL_ERROR)
            raise RuntimeError(latest_message())

    @classmethod
    def check_available(cls):
        """Check whether pstoedit has plot-svg"""
        out = exec_command(['pstoedit', '-help'], ok_return_value=None)
        if 'version 3.44' in out and 'Ubuntu' in out:
            add_log_message("Pstoedit version 3.44 on Ubuntu found, but it contains too many bugs to be usable",
                            LOG_LEVEL_DEBUG)
        if 'plot-svg' not in out:
            add_log_message("Pstoedit not compiled with plot-svg support", LOG_LEVEL_DEBUG)


CONVERTERS = [PstoeditPlotSvg]

#------------------------------------------------------------------------------
# Entry point
#------------------------------------------------------------------------------

if __name__ == "__main__":
    effect = TexText()
    effect.affect()
