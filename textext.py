#!/usr/bin/env python
"""
=======
textext
=======

:Author: Pauli Virtanen <pav@iki.fi>
:Date: 2008-04-26
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
     - Pstoedit_ and Skconvert_

.. _Pstoedit: http://www.pstoedit.net/pstoedit
.. _Skconvert: http://www.skencil.org/
.. _Pdf2svg: http://www.cityinthesky.co.uk/pdf2svg.html
.. _Inkscape: http://www.inkscape.org/
.. _InkLaTeX: http://www.kono.cis.iwate-u.ac.jp/~arakit/inkscape/inklatex.html
"""

#------------------------------------------------------------------------------

__version__ = "0.4.4"
__docformat__ = "restructuredtext en"

import sys, os, glob, traceback, platform
sys.path.append('/usr/share/inkscape/extensions')
sys.path.append(r'c:/Program Files/Inkscape/share/extensions')
sys.path.append(os.path.dirname(__file__))

import inkex
import os, sys, tempfile, traceback, glob, re, md5, copy
from lxml import etree

USE_GTK = False
try:
    import pygtk
    pygtk.require('2.0')
    import gtk
    USE_GTK = True
except ImportError:
    pass

USE_TK = False
try:
    import Tkinter as Tk
    USE_TK = True
except ImportError:
    pass

USE_WINDOWS = (platform.system() == "Windows")

TEXTEXT_NS = u"http://www.iki.fi/pav/software/textext/"
SVG_NS = u"http://www.w3.org/2000/svg"
XLINK_NS = u"http://www.w3.org/1999/xlink"

ID_PREFIX = "textext-"

NSS = {
    u'textext': TEXTEXT_NS,
    u'svg': SVG_NS,
    u'xlink': XLINK_NS,
}

#------------------------------------------------------------------------------
# GUI
#------------------------------------------------------------------------------

if USE_GTK:
    class AskText(object):
        """GUI for editing TexText objects"""
        def __init__(self, text, preamble_file, scale_factor):
            self.text = text
            self.preamble_file = preamble_file
            self.scale_factor = scale_factor
            self.callback = None
    
        def ask(self, callback):
            self.callback = callback
            
            window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            window.set_title("TeX Text")
            window.set_default_size(600, 400)
    
            label1 = gtk.Label(u"Preamble file:")
            label2 = gtk.Label(u"Scale factor:")
            label3 = gtk.Label(u"Text:")


            if hasattr(gtk, 'FileChooserButton'):
                self._preamble = gtk.FileChooserButton("...")
                if os.path.exists(self.preamble_file):
                    self._preamble.set_filename(self.preamble_file)
                self._preamble.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
            else:
                self._preamble = gtk.Entry()
                self._preamble.set_text(self.preamble_file)
            
            self._scale_adj = gtk.Adjustment(lower=0.01, upper=100,
                                             step_incr=0.1, page_incr=1)
            self._scale = gtk.SpinButton(self._scale_adj, digits=2)
            
            if self.scale_factor is not None:
                self._scale_adj.set_value(self.scale_factor)
            else:
                self._scale_adj.set_value(1.0)
                self._scale.set_sensitive(False)
            
            self._text = gtk.TextView()
            self._text.get_buffer().set_text(self.text)

            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_IN)
            sw.add(self._text)
            
            self._ok = gtk.Button(stock=gtk.STOCK_OK)
            self._cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
    
            # layout
            table = gtk.Table(3, 2, False)
            table.attach(label1,         0,1,0,1,xoptions=0,yoptions=gtk.FILL)
            table.attach(self._preamble, 1,2,0,1,yoptions=gtk.FILL)
            table.attach(label2,         0,1,1,2,xoptions=0,yoptions=gtk.FILL)
            table.attach(self._scale,    1,2,1,2,yoptions=gtk.FILL)
            table.attach(label3,         0,1,2,3,xoptions=0,yoptions=gtk.FILL)
            table.attach(sw,             1,2,2,3)
    
            vbox = gtk.VBox(False, 5)
            vbox.pack_start(table)
            
            hbox = gtk.HButtonBox()
            hbox.add(self._ok)
            hbox.add(self._cancel)
            hbox.set_layout(gtk.BUTTONBOX_SPREAD)
            
            vbox.pack_end(hbox, expand=False, fill=False)
    
            window.add(vbox)
    
            # signals
            window.connect("delete-event", self.cb_delete_event)
            window.connect("key-press-event", self.cb_key_press)
            self._ok.connect("clicked", self.cb_ok)
            self._cancel.connect("clicked", self.cb_cancel)
    
            # show
            window.show_all()
            self._text.grab_focus()

            # run
            self._window = window
            gtk.main()
    
            return self.text, self.preamble_file, self.scale_factor
    
        def cb_delete_event(self, widget, event, data=None):
            gtk.main_quit()
            return False

        def cb_key_press(self, widget, event, data=None):
            # ctrl+return clicks the ok button
            if gtk.gdk.keyval_name(event.keyval) == 'Return' \
                   and gtk.gdk.CONTROL_MASK & event.state:
                self._ok.clicked()
                return True
            return False
        
        def cb_cancel(self, widget, data=None):
            raise SystemExit(1)
        
        def cb_ok(self, widget, data=None):
            buf = self._text.get_buffer()
            self.text = buf.get_text(buf.get_start_iter(),
                                     buf.get_end_iter())
            if isinstance(self._preamble, gtk.FileChooser):
                self.preamble_file = self._preamble.get_filename()
                if not self.preamble_file:
                    self.preamble_file = ""
            else:
                self.preamble_file = self._preamble.get_text()

            if self.scale_factor is not None:
                self.scale_factor = self._scale_adj.get_value()
            
            try:
                self.callback(self.text, self.preamble_file, self.scale_factor)
            except StandardError, e:
                err_msg = traceback.format_exc()
                dlg = gtk.Dialog("Textext Error", self._window, 
                                 gtk.DIALOG_MODAL)
                dlg.set_default_size(600, 400)
                btn = dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)
                btn.connect("clicked", lambda w, d=None: dlg.destroy())
                msg = gtk.Label()
                msg.set_markup("<b>Error occurred while converting text from Latex to SVG:</b>")
                
                txtw = gtk.ScrolledWindow()
                txtw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                txtw.set_shadow_type(gtk.SHADOW_IN)
                txt = gtk.TextView()
                txt.set_editable(False)
                txt.get_buffer().set_text(err_msg)
                txtw.add(txt)
                
                dlg.vbox.pack_start(msg, expand=False, fill=True)
                dlg.vbox.pack_start(txtw, expand=True, fill=True)
                dlg.show_all()
                dlg.run()
                return False
            
            gtk.main_quit()
            return False

elif USE_TK:
    class AskText(object):
        """GUI for editing TexText objects"""
        def __init__(self, text, preamble_file, scale_factor):
            self.text = text
            self.preamble_file = preamble_file
            self.scale_factor = scale_factor
            self.callback = None
    
        def ask(self, callback):
            self.callback = callback
            
            root = Tk.Tk()
            
            self._frame = Tk.Frame(root)
            self._frame.pack()
            
            box = Tk.Frame(self._frame)
            label = Tk.Label(box, text="Preamble file:")
            label.pack(pady=2, padx=5, side="left", anchor="w")
            self._preamble = Tk.Entry(box)
            self._preamble.pack(expand=True, fill="x", pady=2, padx=5, side="right")
            self._preamble.insert(Tk.END, self.preamble_file)
            box.pack(fill="x", expand=True)
            
            box = Tk.Frame(self._frame)
            label = Tk.Label(box, text="Scale factor:")
            label.pack(pady=2, padx=5, side="left", anchor="w")
            self._scale = Tk.Scale(box, orient="horizontal", from_=0.1, to=10, resolution=0.1)
            self._scale.pack(expand=True, fill="x", pady=2, padx=5, anchor="e")
            if self.scale_factor is not None:
                self._scale.set(self.scale_factor)
            else:
                self._scale.set(1.0)
            box.pack(fill="x", expand=True)
            
            label = Tk.Label(self._frame, text="Text:")
            label.pack(pady=2, padx=5, anchor="w")

            self._text = Tk.Text(self._frame)
            self._text.pack(expand=True, fill="both", pady=5, padx=5)
            self._text.insert(Tk.END, self.text)
           
            box = Tk.Frame(self._frame)
            self._btn = Tk.Button(box, text="OK", command=self.cb_ok)
            self._btn.pack(ipadx=30, ipady=4, pady=5, padx=5, side="left")
            
            self._cancel = Tk.Button(box, text="Cancel", command=self.cb_cancel)
            self._cancel.pack(ipadx=30, ipady=4, pady=5, padx=5, side="right")

            box.pack(expand=False)
            
            root.mainloop()
            
            self.callback(self.text, self.preamble_file, self.scale_factor)
            return self.text, self.preamble_file, self.scale_factor

        def cb_cancel(self):
            raise SystemExit(1)
    
        def cb_ok(self):
            self.text = self._text.get(1.0, Tk.END)
            self.preamble_file = self._preamble.get()
            if self.scale_factor is not None:
                self.scale_factor = self._scale.get()
            self._frame.quit()

else:
    raise RuntimeError("Neither pygtk nor Tkinter is available!")

#------------------------------------------------------------------------------
# Inkscape plugin functionality
#------------------------------------------------------------------------------

class TexText(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

        self.settings = Settings()
        
        self.OptionParser.add_option(
            "-t", "--text", action="store", type="string",
            dest="text", default=None)
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
        
        converter_cls = None
        for conv_cls in CONVERTERS:
            try:
                conv_cls.available()
                converter_cls = conv_cls
                break
            except StandardError, e:
                converter_errors.append("%s: %s" % (conv_cls.__name__, str(e)))
        
        if not converter_cls:
            raise RuntimeError("No Latex -> SVG converter available:\n%s"
                               % ';\n'.join(converter_errors))
        
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
            
            asker = AskText(text, preamble_file, scale_factor)
            asker.ask(lambda t, p, s: self.do_convert(t, p, s,
                                                      converter_cls, old_node))
        else:
            self.do_convert(self.options.text,
                            self.options.preamble_file,
                            self.options.scale_factor, converter_cls, old_node)

    def do_convert(self, text, preamble_file, scale_factor, converter_cls,
                   old_node):
        
        if not text:
            return

        if isinstance(text, unicode):
            text = text.encode('utf-8')
        
        # Convert
        converter = converter_cls(self.document)
        try:
            new_node = converter.convert(text, preamble_file, scale_factor)
        finally:
            converter.finish()
        
        if new_node is None:
            return # noop

        # Insert into document

        # -- Set textext attribs
        new_node.attrib['{%s}text'%TEXTEXT_NS] = text.encode('string-escape')
        new_node.attrib['{%s}preamble'%TEXTEXT_NS] = \
                                       preamble_file.encode('string-escape')

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
            new_node.attrib['transform'] = old_node.attrib['{%s}transform'%SVG_NS]
        except (KeyError, IndexError, TypeError, AttributeError):
            pass

        # -- Copy style
        if old_node is not None:
            self.copy_style(old_node, new_node)
        
        # -- Replace
        self.replace_node(old_node, new_node)

        # -- Save settings
        if os.path.isfile(preamble_file):
            self.settings.set('preamble', preamble_file)
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
            if node.tag != '{%s}g' % SVG_NS: continue
            
            if '{%s}text'%TEXTEXT_NS in node.attrib:
                # starting from 0.2, use namespaces
                return (node,
                        node.attrib.get('{%s}text'%TEXTEXT_NS, '').decode('string-escape'),
                        node.attrib.get('{%s}preamble'%TEXTEXT_NS, '').decode('string-escape'))
            elif '{%s}text'%SVG_NS in node.attrib:
                # < 0.2 backward compatibility
                return (node,
                        node.attrib.get('{%s}text'%SVG_NS, '').decode('string-escape'),
                        node.attrib.get('{%s}preamble'%SVG_NS, '').decode('string-escape'))
        return None, "", ""

    def replace_node(self, old_node, new_node):
        """
        Replace an XML node old_node with new_node
        in self.document.
        """
        if old_node is None:
            self.current_layer.append(new_node)
        else:
            parent = old_node.getparent()
            parent.remove(old_node)
            parent.append(new_node)


    STYLE_ATTRS = ['fill','fill-opacity','fill-rule',
                   'font-size-adjust','font-stretch',
                   'font-style','font-variant',
                   'font-weight','letter-spacing',
                   'stroke','stroke-dasharray',
                   'stroke-linecap','stroke-linejoin',
                   'stroke-miterlimit','stroke-opacity',
                   'text-anchor','word-spacing','style']
    
    def copy_style(self, old_node, new_node):
        # XXX: Needs work...
        #
        #      We could try traversing the node tree downwards and
        #      removing color-alteration from the attributes.
        #      Not straightforward, need to read the SVG spec...
        #
        #      Removing style attributes does not work in general, because
        #      at least pdf2svg relies on preserving the stroke attrs.
        #
        try:
            new_node.attrib['style'] = old_node.attrib['style']
        except (KeyError, IndexError, TypeError, AttributeError):
            pass

#------------------------------------------------------------------------------
# Settings backend
#------------------------------------------------------------------------------

class Settings(object):
    def __init__(self):
        self.values = {}
        
        if USE_WINDOWS:
            self.keyname = r"Software\TexText\TexText"
        else:
            self.filename = os.path.expanduser("~/.inkscape/textextrc")

        self.load()
    
    def load(self):
        if USE_WINDOWS:
            import _winreg
            try:
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, self.keyname)
            except:
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
                    if not '=' in line: continue
                    k, v = line.split("=", 1)
                    self.values[k.strip()] = v.strip()
            finally:
                f.close()
    
    def save(self):
        if USE_WINDOWS:
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
                data = '\n'.join(["%s=%s" % (k,v)
                                  for k,v in self.values.iteritems()])
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
        """
        try:
            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            out, err = p.communicate()
        except OSError, e:
            raise RuntimeError("Command %s failed: %s" % (' '.join(cmd), e))
        
        if ok_return_value is not None and p.returncode != ok_return_value:
            raise RuntimeError("Command %s failed (code %d): %s"
                               % (' '.join(cmd), p.returncode, out + err))
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
            raise RuntimeError("Command %s failed: %s" % (' '.join(cmd), e))
        
        if ok_return_value is not None and returncode != ok_return_value:
            raise RuntimeError("Command %s failed (code %d): %s"
                               % (' '.join(cmd), returncode, out))
        return out

if USE_WINDOWS:
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
        return os.path.join(self.tmp_path,
                            self.tmp_base + '.' + suffix)

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
            raise RuntimeError("pdflatex didn't produce output")

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
    

class SkConvert(PdfConverterBase):
    """
    Convert PDF -> SK -> SVG using pstoedit and skconvert
    """
    def get_transform(self, scale_factor):
        return 'scale(%f,%f)' % (scale_factor, scale_factor)

    def pdf_to_svg(self):
        # Options for pstoedit command
        pstoeditOpts = '-dt -ssp -psarg -r9600x9600'.split()

        # Exec pstoedit: pdf -> sk
        exec_command(['pstoedit', '-f', 'sk',
                      self.tmp('pdf'), self.tmp('sk')]
                     + pstoeditOpts)
        if not os.path.exists(self.tmp('sk')):
            raise RuntimeError("pstoedit didn't produce output")

        # Exec skconvert: sk -> svg
        os.environ['LC_ALL'] = 'C'
        exec_command(['skconvert', self.tmp('sk'), self.tmp('svg')])
        if not os.path.exists(self.tmp('svg')):
            raise RuntimeError("skconvert didn't produce output")

    def available(cls):
        """Check whether skconvert and pstoedit are available"""
        out = exec_command(['pstoedit'], ok_return_value=None)
        if 'version 3.44' in out and 'Ubuntu' in out:
            raise RuntimeError("Pstoedit version 3.44 on Ubuntu found, but it "
                               "contains too many bugs to be usable")
        exec_command(['skconvert'], ok_return_value=1)
    available = classmethod(available)

class PstoeditPlotSvg(PdfConverterBase):
    """
    Convert PDF -> SVG using pstoedit's plot-svg backend
    """
    def get_transform(self, scale_factor):
        return 'matrix(%f,0,0,%f,%f,%f)' % (
            scale_factor, -scale_factor,
            -200*scale_factor, 750*scale_factor)
    
    def pdf_to_svg(self):
        # Options for pstoedit command
        pstoeditOpts = '-dt -ssp -psarg -r9600x9600'.split()

        # Exec pstoedit: pdf -> svg
        exec_command(['pstoedit', '-f', 'plot-svg',
                      self.tmp('pdf'), self.tmp('svg')]
                     + pstoeditOpts)
        if not os.path.exists(self.tmp('svg')):
            raise RuntimeError("pstoedit didn't produce output")

    def available(cls):
        """Check whether pstoedit has plot-svg available"""
        out = exec_command(['pstoedit', '-help'],
                           ok_return_value=None)
        if 'version 3.44' in out and 'Ubuntu' in out:
            raise RuntimeError("Pstoedit version 3.44 on Ubuntu found, but it "
                               "contains too many bugs to be usable")
        if 'plot-svg' not in out:
            raise RuntimeError("Pstoedit not compiled with plot-svg support")
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
        self.hash = md5.new('%s%s' % (a, kw)).hexdigest()[:8]
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
            href = el.attrib['{%s}href'%XLINK_NS]
            el.attrib['{%s}href'%XLINK_NS] = href_map.get(href, href)

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

CONVERTERS = [Pdf2Svg, PstoeditPlotSvg, SkConvert]

#------------------------------------------------------------------------------
# Entry point
#------------------------------------------------------------------------------

if __name__ == "__main__":
    e = TexText()
    e.affect()
