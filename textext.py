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

warning_messages = []

from asktext import AskerFactory

#------------------------------------------------------------------------------
# Inkscape plugin functionality
#------------------------------------------------------------------------------


def die(message=""):
    if message:
        add_warning_message("ERROR: " + message)
    show_warnings()
    raise SystemExit(1)


def show_warnings():
    inkex.errormsg("\n".join(warning_messages))


def add_warning_message(message):
    warning_messages.append(message)


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
            default=self.settings.get('preamble', str, ""))
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
            except StandardError, e:
                converter_errors.append("%s: %s" % (converter_class.__name__, str(e)))

        if not usable_converter_class:
            die("No Latex -> SVG converter available:\n%s" % ';\n'.join(converter_errors))

        # Find root element
        old_node, text, preamble_file = self.get_old()

        # Ask for TeX code
        if self.options.text is None:
            # If there is a transform, scale in GUI will be ignored
            if old_node is not None:
                scale_factor = None
            else:
                scale_factor = self.options.scale_factor

            if not preamble_file:
                preamble_file = self.options.preamble_file

            if not os.path.isfile(preamble_file):
                preamble_file = ""

            asker = AskerFactory().asker(text, preamble_file, scale_factor)
            try:
                asker.ask(lambda t, p, s: self.do_convert(t, p, s, usable_converter_class, old_node))
            except RuntimeError as error:
                die(str(error))

        else:
            self.do_convert(self.options.text,
                            self.options.preamble_file,
                            self.options.scale_factor, usable_converter_class, old_node)

        if DEBUG:
            show_warnings()

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
        converter = converter_class(self.document)
        try:
            new_node = converter.convert(text, preamble_file, scale_factor)
        finally:
            converter.finish()

        if new_node is None:
            add_warning_message("No new Node!")
            return

        # Insert into document

        # -- Set textext attribs
        new_node.attrib['{%s}text' % TEXTEXT_NS] = text.encode('string-escape')
        new_node.attrib['{%s}preamble' % TEXTEXT_NS] = preamble_file.encode('string-escape')

        # -- Copy transform
        try:
            # Note: the new node does *not* have the SVG namespace prefixes!
            #       This caused some problems as Inkscape couldn't properly
            #       handle both svg: and prefixless entries in the same file
            #       in some cases.
            new_node.attrib['transform'] = old_node.attrib['transform']
        except (KeyError, IndexError, TypeError, AttributeError):
            pass

        try:
            new_node.attrib['transform'] = old_node.attrib['{%s}transform' % SVG_NS]
        except (KeyError, IndexError, TypeError, AttributeError):
            pass

        # -- Copy style
        if old_node is None:
            self.current_layer.append(new_node)
        else:
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

        :Returns: (old_node, latex_text, preamble_file_name)
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
        Replace an XML node old_node with new_node in self.document.
        """
        parent = old_node.getparent()
        parent.remove(old_node)
        parent.append(new_node)
        self.copy_style(old_node, new_node)

    def copy_style(self, old_node, new_node):
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

                if attribute_name == "fill" and old_attribute == "none":
                    old_attribute = "black"

                new_node.attrib[attribute_name] = old_attribute

                for child in new_node.iterchildren():
                    child.attrib[attribute_name] = old_attribute

            except (KeyError, IndexError, TypeError, AttributeError):
                add_warning_message("Problem setting attribute %s" % attribute_name)


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
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, self.keyname,
                                      sam=_winreg.KEY_SET_VALUE | _winreg.KEY_WRITE)
            except:
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

    def exec_command(cmd, ok_return_value=0, combine_error=False):
        """
        Run given command, check return value, and return
        concatenated stdout and stderr.
        :param cmd: Command to execute
        :param ok_return_value: The expected return value after successful completion
        """

        try:
            info = subprocess.STARTUPINFO()
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE

            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 startupinfo=info)
            out, err = p.communicate()
        except OSError, e:
            add_warning_message("Command %s failed: %s" % (' '.join(cmd), e))
            raise RuntimeError
            return

        if ok_return_value is not None and p.returncode != ok_return_value:
            add_warning_message("Command %s failed (code %d): %s" % (' '.join(cmd), p.returncode, out + err))
            raise RuntimeError
        return out + err

except ImportError:
    # Python < 2.4 ...
    import popen2

    def exec_command(cmd, ok_return_value=0, combine_error=False):
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
        except OSError, e:
            add_warning_message("Command %s failed: %s" % (' '.join(cmd), e))
            raise RuntimeError

        if ok_return_value is not None and returncode != ok_return_value:
            add_warning_message("Command %s failed (code %d): %s" % (' '.join(cmd), returncode, out))
            raise RuntimeError
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

    def __init__(self, document):
        """
        Initialize Latex -> SVG converter.

        :Parameters:
          - `document`: Document where the result is to be embedded (read-only)
        """
        self.tmp_path = tempfile.mkdtemp()
        self.tmp_base = 'tmp'

    def convert(self, latex_text, preamble_file, scale_factor):
        """
        Return an XML node containing latex text

        :Parameters:
          - `latex_text`: Latex code to use
          - `preamble_file`: Name of a preamble file to include
          - `scale_factor`: Scale factor to use if object doesn't have
                            a ``transform`` attribute.

        :Returns: XML DOM node
        """
        raise NotImplementedError

    def available(cls):
        """
        :Returns: Check if converter is available, raise RuntimeError if not
        """
        pass

    available = classmethod(available)

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
        \documentclass[landscape,a0]{article}
        %s
        \pagestyle{empty}
        \begin{document}
        \noindent
        %s
        \end{document}
        """ % (preamble, latex_text)

        # Convert TeX to PDF

        # Write tex
        f_tex = open(self.tmp('tex'), 'w')
        try:
            f_tex.write(texwrapper)
        finally:
            f_tex.close()

        # Exec pdflatex: tex -> pdf
        exec_command(['pdflatex', self.tmp('tex')] + latexOpts)
        if not os.path.exists(self.tmp('pdf')):
            die("pdflatex didn't produce output")

    def remove_temp_files(self):
        """Remove temporary files"""
        base = os.path.join(self.tmp_path, self.tmp_base)
        for filename in glob.glob(base + '*'):
            self.try_remove(filename)
        self.try_remove(self.tmp_path)

    def try_remove(self, filename):
        """Try to remove given file, skipping if not exists."""
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
            -200 * scale_factor, 750 * scale_factor)

    def pdf_to_svg(self):
        # Options for pstoedit command
        pstoeditOpts = '-dt -ssp -psarg -r9600x9600'.split()

        # Exec pstoedit: pdf -> svg
        exec_command(['pstoedit', '-f', 'plot-svg',
                      self.tmp('pdf'), self.tmp('svg')]
                     + pstoeditOpts)
        if not os.path.exists(self.tmp('svg')):
            die("pstoedit didn't produce output")

    def available(cls):
        """Check whether pstoedit has plot-svg available"""
        out = exec_command(['pstoedit', '-help'], ok_return_value=None)
        if 'version 3.44' in out and 'Ubuntu' in out:
            add_warning_message("Pstoedit version 3.44 on Ubuntu found, but it contains too many bugs to be usable")
        if 'plot-svg' not in out:
            add_warning_message("Pstoedit not compiled with plot-svg support")

    available = classmethod(available)


class Pdf2Svg(PdfConverterBase):
    """
    Convert PDF -> SVG using pdf2svg
    """

    def __init__(self, document):
        PdfConverterBase.__init__(self, document)
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

    def available(cls):
        """Check whether pdf2svg is available, raise RuntimeError if not"""
        exec_command(['pdf2svg'], ok_return_value=254)

    available = classmethod(available)


CONVERTERS = [Pdf2Svg, PstoeditPlotSvg]

#------------------------------------------------------------------------------
# Entry point
#------------------------------------------------------------------------------

if __name__ == "__main__":
    e = TexText()
    e.affect()
