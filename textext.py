#! /usr/bin/env python
"""
=======
textext
=======

:Author: Pauli Virtanen <pav@iki.fi>
:Date: 2006-12-06
:License: BSD

Textext is an extension for Inkscape_ that allows adding
LaTeX-generated text objects to your SVG drawing. What's more, you can
also *edit* these text objects after creating them.

This brings some of the power of TeX typesetting to Inkscape.

Textext was initially based on InkLaTeX_ written by Toru Araki.

.. note::
   Unfortunately, the TeX input dialog is modal. That is, you cannot
   do anything else with Inkscape while you are composing the LaTeX
   text snippet.

   This is because I have not yet worked out whether it is possible to
   write asynchronous extensions for Inkscape.

.. note::
   Textext requires ``pdflatex``, ``pstoedit``, and ``skconvert``.
   The last one is included in Skencil.

.. _Inkscape: http://www.inkscape.org/
.. _InkLaTeX: http://www.kono.cis.iwate-u.ac.jp/~arakit/inkscape/inklatex.html
"""

__version__ = "0.1"
__author__ = "Pauli Virtanen <pav@iki.fi>"
__docformat__ = "restructuredtext en"

import sys
sys.path.append('/usr/share/inkscape/extensions')

import inkex
import os, sys, tempfile, traceback
import xml.dom.ext.reader.Sax2

import pygtk
pygtk.require('2.0')
import gtk


######################################################################

class AskText(object):
    """GUI for editing TexText objects"""
    def __init__(self, text, preamble_file, scale_factor):
        self.text = text
        self.preamble_file = preamble_file
        self.scale_factor = scale_factor

    def ask(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("TeX Text")
        window.set_default_size(400, 200)

        label1 = gtk.Label(u"Preamble file:")
        label2 = gtk.Label(u"Scale factor:")
        label3 = gtk.Label(u"Text:")

        self._preamble = gtk.Entry()
        self._preamble.set_text(self.preamble_file)

        self._scale_adj = gtk.Adjustment(value=self.scale_factor,
                                         lower=0.01, upper=100,
                                         step_incr=0.1, page_incr=1)
        self._scale = gtk.SpinButton(self._scale_adj, digits=2)

        self._text = gtk.TextView()
        self._text.get_buffer().set_text(self.text)

        ok = gtk.Button(stock=gtk.STOCK_OK)

        # layout
        table = gtk.Table(3, 2, False)
        table.attach(label1,         0,1,0,1,xoptions=0,yoptions=gtk.FILL)
        table.attach(self._preamble, 1,2,0,1,yoptions=gtk.FILL)
        table.attach(label2,         0,1,1,2,xoptions=0,yoptions=gtk.FILL)
        table.attach(self._scale,    1,2,1,2,yoptions=gtk.FILL)
        table.attach(label3,         0,1,2,3,xoptions=0,yoptions=gtk.FILL)
        table.attach(self._text,     1,2,2,3)

        vbox = gtk.VBox(False, 5)
        vbox.pack_start(table)
        vbox.pack_end(ok, expand=False)

        window.add(vbox)

        # signals
        window.connect("delete-event", self.cb_delete_event)
        ok.connect("clicked", self.cb_ok)

        # run
        window.show_all()
        gtk.main()

        return self.text, self.preamble_file, self.scale_factor

    def cb_delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False
    
    def cb_ok(self, widget, data=None):
        buf = self._text.get_buffer()
        self.text = buf.get_text(buf.get_start_iter(),
                                 buf.get_end_iter())
        self.preamble_file = self._preamble.get_text()
        self.scale_factor = self._scale_adj.get_value()
        gtk.main_quit()
        return False

class TexText(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

    def effect(self):
        """Perform the effect: create/modify TexText objects"""
        # Find root element
        root, text, preamble_file = self.get_old()
        
        # Ask for TeX code
        asker = AskText(text, preamble_file, 56.0/10.0)
        text, preamble_file, scale_factor = asker.ask()

        # Convert & read SVG
        try:
            self.convert(root, text, preamble_file, scale_factor)
        except Exception, e:
            traceback.print_exc()

    def get_old(self):
        """
        Dig out LaTeX code and name of preamble file from old
        TexText-generated objects.

        :Returns: (root_node, latex_text, preamble_file_name)
        """
        for i in self.options.ids:
            node = self.selected[i]
            if node.tagName == 'g' and node.hasAttribute('textext'):
                return (node,
                        node.getAttribute('textext').decode('string-escape'),
                        node.getAttribute('texpreamble').decode('string-escape'))
        newone = self.document.createElement('g')
        self.document.documentElement.appendChild(newone)
        return newone, "", "header.inc"

    def convert(self, root, latex_text, preamble_file, scale_factor):
        """
        Replace object ``root`` with a similar object generated by LaTeX.

        :Parameters:
          - `root`: SVG node to replace
          - `latex_text`: Latex code to use
          - `preamble_file`: Name of a preamble file to include
          - `scale_factor`: Scale factor to use if object doesn't have
                            a ``transform`` attribute.
        """
        if root.hasAttribute('transform'):
            transform = root.getAttribute('transform')
        else:
            transform = 'scale(%f,%f)' % (scale_factor, scale_factor)
        
        parent = root.parentNode
        parent.removeChild(root)

        paths = self.tex_to_paths(latex_text, preamble_file)
        newgroup = self.document.createElement('svg:g')

        parent.appendChild(newgroup)
        newgroup.setAttribute('transform', transform)
        newgroup.setAttribute('textext', latex_text.encode('string-escape'))
        newgroup.setAttribute('texpreamble',
                              preamble_file.encode('string-escape'))

        for p in paths:
            if p.nodeType == p.ELEMENT_NODE:
                attr_style = p.getAttributeNode('style')
                attr_d =  p.getAttributeNode('d')
                newpath = self.document.createElement('svg:path')
                newgroup.appendChild(newpath)
                newpath.setAttribute('style', attr_style.value)
                newpath.setAttribute('d', attr_d.value)

    def tex_to_paths(self, text, preamble_file):
        """
        Convert a LaTeX string + preamble file to a list of SVG nodes.

        :Parameters:
          - `text`: TeX string
          - `preamble_file`: Name of preamble file to include

        :Returns: xml.dom.NodeList of relevant SVG nodes
        """
        preamble = ""
        if os.path.exists(preamble_file):
            f = open(preamble_file, 'r')
            preamble += f.read()
            f.close()

        # create xml.dom representation of the TeX file
        doc_tex = self.tex_svg(text, preamble)
        
        # get latex path from svg_out
        path_element = doc_tex.documentElement.getElementsByTagName('path')
        for path in path_element:
            if path.parentNode.nodeName == 'g':
                tex_group_node = path.parentNode
                break
        paths = tex_group_node.childNodes

        return paths

    def tex_svg(self, latex_text, preamble):
        """
        Create a SVG file from latex_text and return its contents as
        a xml.dom tree.

        :Parameters:
          - `latex_text`: String to pass to LaTeX
          - `preamble`:   TeX going into preamble
        """
        
        # Options pass to LaTeX-related commands
        latexOpts = '-interaction=nonstopmode'
    
        # Options for pstoedit command
        pstoeditOpts = '-dt -psarg "-r9600x9600"'

        texwrapper = r"""
        \documentclass[landscape,a0]{article}
        %s
        \pagestyle{empty}
        \begin{document}
        \noindent
        %s
        \end{document}
        """ % (preamble, latex_text)

        temppath = tempfile.gettempdir()
        file = tempfile.mktemp()

        # Convert TeX to SVG
        svg_stream = None
        try:
            # Write tex
            f_tex = open('%s.tex' % file, 'w')
            f_tex.write(texwrapper)
            f_tex.close()
            if not os.path.exists('%s.tex' % file):
                raise RuntimeError("LaTeX File\n",
                                   "Can't create tempory file %s.tex" % file)

            # Exec pdflatex: tex -> pdf
            res = self.exec_command('cd %s; pdflatex %s %s </dev/null 2>&1' % (
                temppath, latexOpts, file))
            if not os.path.exists('%s.pdf' % file):
                raise RuntimeError("pdfLaTeX\n", res)

            # Exec pstoedit: pdf -> sk
            res = self.exec_command('pstoedit %s -f sk %s.pdf %s.sk 2>&1' % (
                pstoeditOpts, file, file))
            if not os.path.exists('%s.sk' % file):
                raise RuntimeError("pstoedit", res)

            # Exec skconvert: sk -> svg
            res = self.exec_command('skconvert %s.sk %s.svg' % (file, file))
            if not os.path.exists('%s.svg' % file):
                raise RuntimeError("skconvert", res)

            # Read SVG to XML
            svg_stream = open('%s.svg' % file, 'r')
            reader_tex = xml.dom.ext.reader.Sax2.Reader()
            return reader_tex.fromStream(svg_stream)
        finally:
            if svg_stream:
                svg_stream.close()
            self.remove_temp_files(file)

    def exec_command(self, command):
        """Run given command in shell and return output as string"""
        file = os.popen(command, 'r')
        message = file.read()
        file.close()
        return message

    def remove_temp_files(self, filename):
        """Remove files made in /tmp"""
        self.try_remove(filename + '.tex')
        self.try_remove(filename + '.log')
        self.try_remove(filename + '.aux')
        self.try_remove(filename + '.pdf')
        self.try_remove(filename + '.sk')
        self.try_remove(filename + '.svg')

    def try_remove(self, filename):
        """Try to remove given file, skipping if not exists."""
        if os.path.exists(filename):
            os.remove(filename)

e = TexText()
e.affect()
