#! /usr/bin/env python
"""
=======
textext
=======

:Author: Pauli Virtanen <pav@iki.fi>
:Date: 2007-06-17
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
   Textext requires ``pdflatex`` and ``pstoedit``.

   If your ``pstoedit`` does not have support for the ``plot-svg`` back-end,
   you also need to have Skencil installed.

.. _Inkscape: http://www.inkscape.org/
.. _InkLaTeX: http://www.kono.cis.iwate-u.ac.jp/~arakit/inkscape/inklatex.html
"""

#------------------------------------------------------------------------------

__version__ = "0.2.1"
__author__ = "Pauli Virtanen <pav@iki.fi>"
__docformat__ = "restructuredtext en"

import sys
sys.path.append('/usr/share/inkscape/extensions')

import inkex
import os, sys, tempfile, traceback, subprocess
import xml.dom.ext.reader.Sax2

import pygtk
pygtk.require('2.0')
import gtk

NAMESPACEURI = "http://www.iki.fi/pav/software/textext/"

#------------------------------------------------------------------------------

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
        asker = AskText(text, preamble_file, 1.0)
        text, preamble_file, scale_factor = asker.ask()

        if not text:
            return

        # Convert & read SVG
        self.convert(root, text, preamble_file, scale_factor)

    def get_old(self):
        """
        Dig out LaTeX code and name of preamble file from old
        TexText-generated objects.

        :Returns: (root_node, latex_text, preamble_file_name)
        """
        for i in self.options.ids:
            node = self.selected[i]
            if node.tagName != 'g': continue

            if node.hasAttributeNS(NAMESPACEURI, 'text'):
                # starting from 0.2, use namespaces
                return (node,
                        node.getAttributeNS(NAMESPACEURI, 'text').decode('string-escape'),
                        node.getAttributeNS(NAMESPACEURI, 'preamble').decode('string-escape'))
            elif node.hasAttribute('textext'):
                # < 0.2 backward compatibility
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
        oldgroup = self.tex_to_group(latex_text, preamble_file)
        if not oldgroup:
            return
        
        if root.hasAttribute('transform'):
            transform = root.getAttribute('transform')
        elif self.has_plot_svg:
            transform = ('matrix(%f,0,0,%f,%f,%f)'
                         % (scale_factor, -scale_factor,
                            -200 * scale_factor, 750 * scale_factor))
        else:
            transform = 'scale(%f,%f)' % (scale_factor, scale_factor)
            
        newgroup = self.document.importNode(oldgroup, True)
        self.fix_xml_namespace(newgroup)
        newgroup.setAttribute('transform', transform)
        newgroup.setAttributeNS(NAMESPACEURI,
                                'textext:text',
                                latex_text.encode('string-escape'))
        newgroup.setAttributeNS(NAMESPACEURI, 'textext:preamble',
                                preamble_file.encode('string-escape'))
        
        parent = root.parentNode
        parent.removeChild(root)
        parent.appendChild(newgroup)

    def fix_xml_namespace(self, node):
        """
        Set the default XML namespace to http://www.w3.org/2000/svg
        for the given node and all its children.

        This is needed since pstoedit plot-svg generates namespaceless
        SVG files.
        """
        node.setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns',
                            'http://www.w3.org/2000/svg')
        for c in node.childNodes:
            if c.nodeType == c.ELEMENT_NODE:
                self.fix_xml_namespace(c)

    def tex_to_group(self, text, preamble_file):
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
        docel = doc_tex.documentElement

        # get latex paths from svg_out
        try:
            return docel.getElementsByTagName('g')[0]
        except IndexError:
            return None

    def tex_svg(self, latex_text, preamble):
        """
        Create a SVG file from latex_text and return its contents as
        a xml.dom tree.

        :Parameters:
          - `latex_text`: String to pass to LaTeX
          - `preamble`:   TeX going into preamble
        """
        
        # Options pass to LaTeX-related commands
        latexOpts = ['-interaction=nonstopmode']
    
        texwrapper = r"""
        \documentclass[landscape,a0]{article}
        %s
        \pagestyle{empty}
        \begin{document}
        \noindent
        %s
        \end{document}
        """ % (preamble, latex_text)

        path = tempfile.mkdtemp()
        cwd = os.getcwd()
        os.chdir(path)

        def tmp(name):
            return os.path.join(path, name)

        # Convert TeX to SVG
        svg_stream = None
        try:
            # Write tex
            f_tex = open(tmp('x.tex'), 'w')
            try:
                f_tex.write(texwrapper)
            finally:
                f_tex.close()

            # Exec pdflatex: tex -> pdf
            self.exec_command(['pdflatex', tmp('x.tex')] + latexOpts)
            if not os.path.exists(tmp('x.pdf')):
                raise RuntimeError("pdflatex didn't produce output")

            self.pdf_to_svg(tmp('x.pdf'), tmp('x.svg'))

            # Read SVG to XML
            svg_stream = open(tmp('x.svg'), 'r')
            reader_tex = xml.dom.ext.reader.Sax2.Reader()
            return reader_tex.fromStream(svg_stream)
        finally:
            os.chdir(cwd)
            if svg_stream:
                svg_stream.close()
            self.remove_temp_files(path)

    def pdf_to_svg(self, input, output):
        # Options for pstoedit command
        pstoeditOpts = '-dt -ssp -psarg "-r9600x9600"'.split()

        # Check whether pstoedit has plot-svg available
        p = subprocess.Popen(['pstoedit', '-f', 'help'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        self.has_plot_svg = 'plot-svg' in p.communicate()[0]

        # Proceed
        if self.has_plot_svg:
            # Exec pstoedit: pdf -> svg
            self.exec_command(['pstoedit', '-f', 'plot-svg',
                               input, output]
                              + pstoeditOpts)
            if not os.path.exists(output):
                raise RuntimeError("pstoedit didn't produce output")
        else:
            # Exec pstoedit: pdf -> sk
            sk = input + '.sk'
            self.exec_command(['pstoedit', '-f', 'sk', input, sk]
                              + pstoeditOpts)
            if not os.path.exists(sk):
                raise RuntimeError("pstoedit didn't produce output")

            # Exec skconvert: sk -> svg
            os.environ['LC_ALL'] = 'C'
            self.exec_command(['skconvert', sk, output])
            if not os.path.exists(output):
                raise RuntimeError("skconvert didn't produce output")

    def exec_command(self, cmd):
        """Run given command, check return value"""
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise RuntimeError("Command %s failed (code %d): %s%s"
                               % (' '.join(cmd), p.returncode, out, err))
    
    def remove_temp_files(self, path):
        """Remove files made in /tmp"""
        for filename in ['x.tex', 'x.log', 'x.aux', 'x.pdf', 'x.svg',
                         'x.pdf.sk']:
            self.try_remove(os.path.join(path, filename))
        self.try_remove(path)

    def try_remove(self, filename):
        """Try to remove given file, skipping if not exists."""
        if os.path.isfile(filename):
            os.remove(filename)
        elif os.path.isdir(filename):
            os.rmdir(filename)

if __name__ == "__main__":
    e = TexText()
    e.affect()
