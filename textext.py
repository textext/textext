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

__version__ = "0.4.dev"
__docformat__ = "restructuredtext en"

import sys, os, glob, traceback, platform
import shutil, tempfile, re, copy

sys.path.append('/usr/share/inkscape/extensions')
sys.path.append(r'c:/Program Files/Inkscape/share/extensions')
sys.path.append(os.path.dirname(__file__))

from lxml import etree
import inkex

try:
    import hashlib
except ImportError:
    import md5 as hashlib

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
        def __init__(self, info):
            self.info = info
            self.callback = None

        def ask(self, callback):
            self.callback = callback
            
            window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            window.set_title("TeX Text")
            window.set_default_size(600, 400)
    
            label_preamble = gtk.Label(u"Preamble file:")
            label_scale = gtk.Label(u"Scale factor:")
            label_text = gtk.Label(u"Text:")
            label_converter = gtk.Label(u"Converter:")
            label_page_width = gtk.Label(u"LaTeX page width:")

            if hasattr(gtk, 'FileChooserButton'):
                self._preamble = gtk.FileChooserButton("Preamble file")
                if os.path.isfile(self.info.preamble_file):
                    self._preamble.set_filename(self.info.preamble_file)
                self._preamble.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
            else:
                self._preamble = gtk.Entry()
                self._preamble.set_text(self.info.preamble_file)
            
            self._scale_adj = gtk.Adjustment(lower=0.01, upper=100,
                                             step_incr=0.1, page_incr=1)
            self._scale = gtk.SpinButton(self._scale_adj, digits=2)
            
            if not self.info.has_node:
                self._scale_adj.set_value(self.info.scale_factor)
            else:
                self._scale_adj.set_value(1.0)
                self._scale.set_sensitive(False)

            self._page_width = gtk.Entry()
            self._page_width.set_text(self.info.page_width)

            self._converter = gtk.combo_box_new_text()
            for conv in self.info.available_converters:
                self._converter.append_text(conv.name)
            for conv in self.info.unavailable_converters:
                self._converter.append_text(conv.name
                                            + ' [NOT AVAILABLE CURRENTLY]')
            self._converter.set_active(0)
            for j, conv in enumerate(self.info.available_converters):
                if conv.name == self.info.selected_converter:
                    self._converter.set_active(j)
                    break

            self._text = gtk.TextView()
            self._text.get_buffer().set_text(self.info.text)

            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_IN)
            sw.add(self._text)
            
            self._ok = gtk.Button(stock=gtk.STOCK_OK)
            self._cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
    
            # layout
            table = gtk.Table(5, 2, False)

            table.attach(label_preamble,     0,1,0,1,xoptions=0,yoptions=gtk.FILL)
            table.attach(self._preamble,     1,2,0,1,yoptions=gtk.FILL)

            table.attach(label_scale,        0,1,1,2,xoptions=0,yoptions=gtk.FILL)
            table.attach(self._scale,        1,2,1,2,yoptions=gtk.FILL)

            table.attach(label_page_width,   0,1,2,3,xoptions=0,yoptions=gtk.FILL)
            table.attach(self._page_width,   1,2,2,3,yoptions=gtk.FILL)

            table.attach(label_converter,    0,1,3,4,xoptions=0,yoptions=gtk.FILL)
            table.attach(self._converter,    1,2,3,4,yoptions=gtk.FILL)

            table.attach(label_text,         0,1,4,5,xoptions=0,yoptions=gtk.FILL)
            table.attach(sw,                 1,2,4,5)

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
            self.info.text = buf.get_text(buf.get_start_iter(),
                                     buf.get_end_iter())
            if isinstance(self._preamble, gtk.FileChooser):
                self.info.preamble_file = self._preamble.get_filename()
                if not self.info.preamble_file:
                    self.info.preamble_file = ""
            else:
                self.info.preamble_file = self._preamble.get_text()

            self.info.page_width = self._page_width.get_text()

            j = self._converter.get_active()
            try:
                self.info.selected_converter = \
                    self.info.available_converters[j].name
            except IndexError:
                self.info.selected_converter = None

            if not self.info.has_node:
                self.info.scale_factor = self._scale_adj.get_value()
            
            try:
                self.callback()

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
        def __init__(self, info):
            self.info = info
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
            self._preamble.insert(Tk.END, self.info.preamble_file)
            box.pack(fill="x", expand=True)

            box = Tk.Frame(self._frame)
            label = Tk.Label(box, text="LaTeX page width:")
            label.pack(pady=2, padx=5, side="left", anchor="w")
            self._page_width = Tk.Entry(box)
            self._page_width.pack(expand=True, fill="x", pady=2, padx=5, side="right")
            self._page_width.insert(Tk.END, self.info.page_width)
            box.pack(fill="x", expand=True)
 
            box = Tk.Frame(self._frame)
            label = Tk.Label(box, text="Scale factor:")
            label.pack(pady=2, padx=5, side="left", anchor="w")
            self._scale = Tk.Scale(box, orient="horizontal", from_=0.1, to=10, resolution=0.1)
            self._scale.pack(expand=True, fill="x", pady=2, padx=5, anchor="e")
            if not self.info.has_node:
                self._scale.set(self.info.scale_factor)
            else:
                self._scale.set(1.0)
            box.pack(fill="x", expand=True)
            
            box = Tk.Frame(self._frame)
            label = Tk.Label(box, text="Converter:")
            label.pack(pady=2, padx=5, side="left", anchor="w")
            cvs = ([conv.name for conv in self.info.available_converters]
                   + [conv.name + " [NOT AVAILABLE CURRENTLY]"
                      for conv in self.info.unavailable_converters])
            self._converter = Tk.StringVar()
            self._converter.set(cvs[0])
            opt = Tk.OptionMenu(box, self._converter, *cvs)
            opt.pack(expand=True, fill="x", pady=2, padx=5, anchor="e")
            box.pack(fill="x", expand=True)

            label = Tk.Label(self._frame, text="Text:")
            label.pack(pady=2, padx=5, anchor="w")


            box = Tk.Frame(self._frame)
            scrollbar = Tk.Scrollbar(box)
            scrollbar.pack(side=Tk.RIGHT, fill=Tk.Y)

            self._text = Tk.Text(box)
            self._text.pack(expand=True, side=Tk.LEFT, fill="both", pady=5, padx=5)
            self._text.insert(Tk.END, self.info.text)

            self._text.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=self._text.yview)

            box.pack(fill="x", expand=True)
           
            box = Tk.Frame(self._frame)
            self._btn = Tk.Button(box, text="OK", command=self.cb_ok)
            self._btn.pack(ipadx=30, ipady=4, pady=5, padx=5, side="left")
            
            self._cancel = Tk.Button(box, text="Cancel", command=self.cb_cancel)
            self._cancel.pack(ipadx=30, ipady=4, pady=5, padx=5, side="right")

            box.pack(expand=True)

            while True:
                root.mainloop()
                try:
                    self.callback()
                    return
                except StandardError, e:
                    err = traceback.format_exc()

                    dlg = Tk.Toplevel()
                    dlg.title("Error")

                    msg = Tk.Message(dlg, text=u"Error occurred while converting text from Latex to SVG:")
                    msg.pack(expand=True, fill=Tk.X, padx=5)

                    box = Tk.Frame(dlg)
                    scrollbar = Tk.Scrollbar(box)
                    scrollbar.pack(side=Tk.RIGHT, fill=Tk.Y)
                    txt = Tk.Text(box)
                    txt.pack(expand=True, fill="both", pady=5, padx=5)
                    txt.insert(Tk.END, err)
                    txt.config(yscrollcommand=scrollbar.set)
                    scrollbar.config(command=txt.yview)
                    box.pack()

                    btn = Tk.Button(dlg, text="OK", command=dlg.destroy)
                    btn.pack()
                    dlg.mainloop()

        def cb_cancel(self):
            raise SystemExit(1)
    
        def cb_ok(self):
            def stru(s):
                if isinstance(s, unicode):
                    return s.encode('utf-8')
                else:
                    return s

            self.info.text = stru(self._text.get(1.0, Tk.END))
            self.info.preamble_file = stru(self._preamble.get())
            self.info.page_width = stru(self._page_width.get())
            self.info.selected_converter = bool(self._converter.get())

            if not self.info.has_node:
                self.info.scale_factor = self._scale.get()
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
            dest="preamble_file", default=None)
        self.OptionParser.add_option(
            "-w", "--page-width", action="store", type="string",
            dest="page_width", default=None)
        self.OptionParser.add_option(
            "-s", "--scale-factor", action="store", type="float",
            dest="scale_factor", default=None)
        self.OptionParser.add_option(
            "-T", "--text-to-path", action="store_true",
            dest="text_to_path", default=None)
        self.OptionParser.add_option(
            "--no-text-to-path", action="store_false",
            dest="text_to_path", default=None)
        self.OptionParser.add_option(
            "-c", "--converter", action="store", type="string",
            dest="selected_converter", default=None)

    def effect(self):
        """Perform the effect: create/modify TexText objects"""
        # Load default convert info from settings
        info = ConvertInfo()
        info.load_from_settings(self.settings)

        # Find root element
        old_node = self.get_old()

        # Load convert info from old node
        if not old_node is None:
            info.load_from_node(old_node)

        # Override info with command line options
        info.load_from_options(self.options)

        # Update convert info from GUI (if we're not supplied with text from cmd)
        if self.options.text is None:
            asker = AskText(info)
            asker.ask(lambda: self.do_convert(info, old_node))
        else:
            self.do_convert(info, old_node)

    def do_convert(self, info, old_node):
        # Must have some text to convert
        if not info.text:
            return

        # Convert
        converter = None
        try:
            converter_cls = info.get_converter_cls()
            converter = converter_cls(self.document)
            new_node = converter.convert(info)
        finally:
            if converter is not None:
                converter.finish()

        if new_node is None:
            return # noop

        # Insert into document

        # -- Set textext attribs
        info.save_to_node(new_node)

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
        
        # -- Work around probable bugs in several viewers that don't handle
        #    "stroke-width: 0;" style properly.
        style = 'stroke-width: 0.0000001'
        try:
            xstyle = new_node.attrib['style']
        except KeyError:
            try:
                xstyle = new_node.attrib['{%s}style'%SVG_NS]
                del new_node.attrib['{%s}style'%SVG_NS]
            except KeyError:
                xstyle = ""
        if 'stroke-width' not in xstyle:
            if xstyle.strip():
                style = xstyle + ';' + style
        else:
            style = xstyle
        new_node.attrib['style'] = style

        # -- Replace
        self.replace_node(old_node, new_node)

        # -- Save settings
        info.save_to_settings(self.settings)
   
    def get_old(self):
        """
        Dig out LaTeX code and name of preamble file from old
        TexText-generated objects.

        :Returns: (old_node, ConvertInfo)
        """
        
        info = ConvertInfo()
        for i in self.options.ids:
            node = self.selected[i]
            if node.tag != '{%s}g' % SVG_NS: continue
            
            if '{%s}text'%TEXTEXT_NS in node.attrib:
                # starting from 0.2, use namespaces
                return node

            elif '{%s}text'%SVG_NS in node.attrib:
                # < 0.2 backward compatibility
                return node

        return None

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

        dir_1 = os.path.expanduser("~/.config/inkscape")
        dir_2 = os.path.expanduser("~/.inkscape")

        if USE_WINDOWS:
            self.keyname = r"Software\TexText\TexText"
        elif os.path.isdir(dir_1):
            # Since Inkscape 0.47
            self.filename = os.path.join(dir_1, "textextrc")
        else:
            self.filename = os.path.join(dir_2, "textextrc")

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
                data = '\n'.join(["%s = %s" % (k, v)
                                  for k, v in self.values.iteritems()])
                data += '\n'
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
        # Guess some paths
        paths += glob.glob(os.path.join(program_files, 'gs/gs*/bin'))
        paths += glob.glob(os.path.join(program_files, 'pstoedit*'))
        paths += glob.glob(os.path.join(program_files, 'miktex*/miktex/bin'))

        # FIXME: a better solution would be to look them up from the registry

    # The path where Inkscape is likely to be
    paths += [os.path.join(os.abspath(os.dirname(sys.argv[0])), '..', '..')]

    # Set the paths
    os.environ['PATH'] = os.path.pathsep.join(paths)


class ConvertInfo(object):
    def __init__(self):
        self.text = None
        self.preamble_file = None
        self.page_width = None
        self.scale_factor = None
        self.has_node = False
        self.text_to_path = False
        self.selected_converter = None

        self.available_converters = []
        self.unavailable_converters = []

        self._find_converters()

    def _find_converters(self):
        converter_errors = []
        for conv_cls in CONVERTERS:
            try:
                conv_cls.check_available()
                self.available_converters.append(conv_cls)
            except StandardError, e:
                self.unavailable_converters.append(conv_cls)
                converter_errors.append("%s: %s" % (conv_cls.__name__, str(e)))

        if not self.available_converters:
            raise RuntimeError(("No Latex -> SVG converter available:\n%s\n\n"
                                "TexText does not work without one.")
                               % ';\n'.join(converter_errors))

    def get_converter_cls(self):
        # Try to find the selected one
        for cls in self.available_converters:
            if cls.name == self.selected_converter:
                return cls

        # Try to use one conforming to the chosen text-to-path setting
        for cls in self.available_converters:
            if cls.text_to_path == self.text_to_path:
                return cls

        raise RuntimeError("No converter supporting the chosen 'Text to path' setting "
                           "was found. Toggle the option and try again.")

    def hash(self):
        s = "%s\n%s\n%s\n%s\n%d" % (
            self.text, self.preamble_file,
            self.page_width, self.scale_factor,
            self.text_to_path)
        return hashlib.md5(s).hexdigest()[:8]

    #-- Getters

    def get_text_encoded(self):
        text = self.text
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        return text

    #-- Serialization

    def load_from_settings(self, settings):
        def str_to_bool(x):
            try:
                return bool(int(x))
            except ValueError:
                pass
            if x.lower() in ('true', 'yes'):
                return True
            elif x.lower() ('false', 'no'):
                return False
            raise ValueError(x)

        self.preamble_file = settings.get("preamble", str, "")
        self.scale_factor = settings.get("scale", float, 1.0)
        self.page_width = settings.get("page_width", str, "10cm")
        self.text_to_path = settings.get("text_to_path", str_to_bool, False)
        self.selected_converter = settings.get("selected_converter", str, "")

    def load_from_node(self, node):
        self.has_node = True
        if '{%s}text' % TEXTEXT_NS in node.attrib:
            # starting from 0.2, use namespaces
            self.load_from_node_ns(node, TEXTEXT_NS)
        elif '{%s}text' % SVG_NS in node.attrib:
            # < 0.2 backward compatibility
            self.load_from_node_ns(node, SVG_NS)
        else:
            raise RuntimeError("Node %s has no textext text" % node)

    def load_from_node_ns(self, node, ns):
        self.has_node = True
        self.text = node.attrib.get('{%s}text'%ns, '').decode('string-escape')
        self.preamble_file = node.attrib.get('{%s}preamble'%ns, '').decode('string-escape')
        self.page_width = node.attrib.get('{%s}page_width'%ns, '').decode('string-escape')

    def load_from_options(self, options):
        # Set from option if option is given
        def get_opt(name):
            if not getattr(options, name) is None:
                setattr(self, name, getattr(options, name))

        get_opt("text")
        get_opt("preamble_file")
        get_opt("page_width")
        get_opt("scale_factor")
        get_opt("text_to_path")
        get_opt("selected_converter")

        if self.text is None:
            self.text = ""
        
        if not os.path.isfile(self.preamble_file):
            self.preamble_file = ""

    def save_to_node(self, node):
        node.attrib['{%s}text'%TEXTEXT_NS] = self.text.encode('string-escape')
        node.attrib['{%s}preamble'%TEXTEXT_NS] = \
                                       self.preamble_file.encode('string-escape')
        node.attrib['{%s}page_width'%TEXTEXT_NS] = \
                                       self.page_width.encode('string-escape')

    def save_to_settings(self, settings):
        if os.path.isfile(self.preamble_file):
            settings.set("preamble", self.preamble_file)
        if self.scale_factor is not None:
            settings.set("scale", self.scale_factor)
        if self.page_width is not None:
            settings.set("page_width", self.page_width)
        if self.text_to_path is not None:
            settings.set("text_to_path", self.text_to_path)
        if self.selected_converter is not None:
            settings.set("selected_converter", self.selected_converter)
        settings.save()
 
    def __str__(self):
        return "%s %s %s %s %s %s" % (
                 self.text,
                 self.scale_factor,
                 self.preamble_file,
                 self.page_width,
                 self.text_to_path,
                 self.selected_converter)


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

    def convert(self, info):
        """
        Return an XML node containing latex text

        :Parameters:
            - info ConvertInfo object containing
              - `latex_text`: Latex code to use
              - `preamble_file`: Name of a preamble file to include
              - `scale_factor`: Scale factor to use if object doesn't have
                                a ``transform`` attribute.
    
        :Returns: XML DOM node
        """
        raise NotImplementedError

    def check_available(cls):
        """
        :Returns: Check if converter is available, raise RuntimeError if not
        """
        pass
    check_available = classmethod(check_available)

    def is_available(cls):
        try:
            cls.check_available()
            return True
        except StandardError:
            return False
    is_available = classmethod(is_available)

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

    def _get_text(self, info):
        latex_text = info.text
        if os.path.isfile(latex_text):
            f = open(latex_text, 'r')
            latex_text = f.read()
            f.close()
        return latex_text

    def tex_to_pdf(self, info):
        """
        Create a PDF file from latex text
        """

        # Read preamble
        preamble = ""
        if os.path.isfile(info.preamble_file):
            f = open(info.preamble_file, 'r')
            preamble += f.read()
            f.close()

        # If latex_text is a file, use the file content instead
        latex_text = self._get_text(info)

        # Geometry and document class
        width = info.page_width
        height = "400cm" # probably large enough
        geometry = ""
        document_class = r"\documentclass[a0paper,landscape]{article}"
        if width:
            document_class = r"\documentclass{article}"
            geometry = (("\usepackage[left=0cm, top=0cm, right=0cm, nohead, "
                         "nofoot, papersize={%s,%s} ]{geometry}") 
                        % (width, height))

        if r"\documentclass" in preamble:
            document_class = ""

        # Write the template to a file
        texwrapper = r"""
        %(document_class)s
        %(preamble)s
        %(geometry)s
        \pagestyle{empty}
        \begin{document}
        \noindent
        %(latex_text)s
        \end{document}
        """ % locals()

        f_tex = open(self.tmp('tex'), 'w')
        try:
            f_tex.write(texwrapper)
        finally:
            f_tex.close()

        # Options pass to LaTeX-related commands
        latex_opts = ['-interaction=nonstopmode', '-halt-on-error']

        # Exec pdflatex: tex -> pdf
        out = exec_command(['pdflatex', self.tmp('tex')] + latex_opts)
        if not os.path.exists(self.tmp('pdf')):
            raise RuntimeError("pdflatex didn't produce output:\n\n" + out)

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
            try:
                os.rmdir(filename)
            except OSError:
                pass

class PdfConverterBase(LatexConverterBase):

    text_to_path = True

    def convert(self, info):
        cwd = os.getcwd()
        try:
            os.chdir(self.tmp_path)
            self.tex_to_pdf(info)
            self.pdf_to_svg()
        finally:
            os.chdir(cwd)
        
        new_node = self.svg_to_group()
        if new_node is None:
            return None

        if info.scale_factor is not None:
            new_node.attrib['transform'] = self.get_transform(info.scale_factor)
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

    name = "Skconvert"
    text_to_path = True

    def get_transform(self, scale_factor):
        # Correct for SVG units -> points scaling
        scale_factor *= 1.25
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

    def check_available(cls):
        """Check whether skconvert and pstoedit are available"""
        out = exec_command(['pstoedit'], ok_return_value=None)
        if 'version 3.44' in out and 'Ubuntu' in out:
            raise RuntimeError("Pstoedit version 3.44 on Ubuntu found, but it "
                               "contains too many bugs to be usable")
        exec_command(['skconvert'], ok_return_value=1)
    check_available = classmethod(check_available)

class PstoeditPlotSvg(PdfConverterBase):
    """
    Convert PDF -> SVG using pstoedit's plot-svg backend
    """

    name = "Pstoedit"
    text_to_path = True

    def get_transform(self, scale_factor):
        # Correct for SVG units -> points scaling
        scale_factor *= 1.25
        return 'matrix(%f,0,0,%f,%f,%f)' % (
            scale_factor, -scale_factor,
            -200*scale_factor/1.25, 750*scale_factor/1.25)

    def pdf_to_svg(self):
        # Options for pstoedit command
        pstoeditOpts = '-dt -ssp -psarg -r9600x9600'.split()

        # Exec pstoedit: pdf -> svg
        exec_command(['pstoedit', '-f', 'plot-svg',
                      self.tmp('pdf'), self.tmp('svg')]
                     + pstoeditOpts)
        if not os.path.exists(self.tmp('svg')):
            raise RuntimeError("pstoedit didn't produce output")

    def check_available(cls):
        """Check whether pstoedit has plot-svg available"""
        out = exec_command(['pstoedit', '-help'],
                           ok_return_value=None)
        if 'version 3.44' in out and 'Ubuntu' in out:
            raise RuntimeError("Pstoedit version 3.44 on Ubuntu found, but it "
                               "contains too many bugs to be usable")
        if 'plot-svg' not in out:
            raise RuntimeError("Pstoedit not compiled with plot-svg support")
    check_available = classmethod(check_available)

class Pdf2Svg(PdfConverterBase):
    """
    Convert PDF -> SVG using pdf2svg
    """

    name = "Pdf2Svg"
    text_to_path = True

    def __init__(self, document):
        PdfConverterBase.__init__(self, document)
        self.hash = None

    def convert(self, info):
        # compute hash for generating unique ids for sub-elements
        self.hash = info.hash()
        return PdfConverterBase.convert(self, info)

    def pdf_to_svg(self):
        exec_command(['pdf2svg', self.tmp('pdf'), self.tmp('svg'), '1'])

    def get_transform(self, scale_factor):
        # Correct for SVG units -> points scaling
        scale_factor *= 1.25
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

    def check_available(cls):
        """Check whether pdf2svg is available, raise RuntimeError if not"""
        exec_command(['pdf2svg'], ok_return_value=254)
    check_available = classmethod(check_available)


class Inkscape(PdfConverterBase):
    """
    Convert PDF -> SVG using Inkscape
    """

    name = "Inkscape"
    text_to_path = False

    INKSCAPE = os.environ.get('INKSCAPE', 'inkscape')

    def __init__(self, document):
        PdfConverterBase.__init__(self, document)

    def pdf_to_svg(self):
        exec_command([self.INKSCAPE, '--export-plain-svg=%s' % self.tmp('svg'),
                      self.tmp('pdf')])

    def get_transform(self, scale_factor):
        # Correct for SVG units -> points scaling
        scale_factor *= 1.25
        return 'matrix(%f,0,0,-%f,%f,%f)' % (
                scale_factor, scale_factor,
                0, 11328.62*scale_factor)

    def _get_version(cls):
        out = exec_command([cls.INKSCAPE, '--version'])
        m = re.search(r'(\d+)\.(\d+)', out)
        if m:
            major = int(m.group(1))
            minor = int(m.group(2))
            dev = '+devel' in out
            return major, minor, dev
        raise RuntimeError('Inkscape could not be located')
    _get_version = classmethod(_get_version)

    def check_available(cls):
        """Check whether inkscape is sufficiently new and found"""
        major, minor, dev = cls._get_version()
        if major > 0 or major == 0 and (minor >= 47 or minor >= 46 and dev):
            return
        raise RuntimeError('Inkscape %d.%d found, but it is too old' % (major, minor))
    check_available = classmethod(check_available)

class InkscapePath(Inkscape):
    """
    Convert PDF -> SVG using Inkscape, with text-to-path applied first

    This is currently quite slow, as we invoke Inkscape twice.
    """

    name = "Inkscape (+ text-to-path)"
    text_to_path = True

    def pdf_to_svg(self):
        # FIXME: inkscape bug #168616 prevents us from doing
        #    inkscape -z --verb=EditSelectAll --verb=ObjectToPath --verb FileSave
        # so we need to invoke inkscape twice
        shutil.move(self.tmp('pdf'), self.tmp('2.pdf'))
        exec_command([self.INKSCAPE, '-T',
                      '--export-pdf=%s' % self.tmp('pdf'),
                      self.tmp('2.pdf')])
        Inkscape.pdf_to_svg(self)

class MatplotlibSVG(PdfConverterBase):
    name = "Matplotlib"
    text_to_path = False

    def tex_to_pdf(self, info):
        import matplotlib as mpl
        mpl.use('svg')
        import matplotlib.pyplot as plt

        fig = plt.figure()
        fig.patch.set_visible(False)
        fig.text(0., 1., self._get_text(info), ha='left', va='top')
        plt.savefig(self.tmp('svg'))

    def get_transform(self, scale_factor):
        # Correct for SVG units -> points scaling
        scale_factor *= 1.25
        return 'scale(%f,%f)' % (scale_factor, scale_factor)

    def pdf_to_svg(self):
        pass

    def check_available(cls):
        try:
            import matplotlib
        except ImportError:
            raise RuntimeError("Matplotlib not available.")
    check_available = classmethod(check_available)

CONVERTERS = [
    Pdf2Svg, PstoeditPlotSvg, Inkscape, SkConvert, InkscapePath,
    MatplotlibSVG,
]

#------------------------------------------------------------------------------
# Entry point
#------------------------------------------------------------------------------

if __name__ == "__main__":
    e = TexText()
    e.affect()
