#! /usr/bin/env python
# Time-stamp: <06/03/17 13:50:56 arakit>

import sys
sys.path.append('/usr/share/inkscape/extensions/')

import pygtk
pygtk.require('2.0')
import gtk

import inkex
import tempfile, traceback
import os, sys
import xml.dom.ext.reader.Sax2

######################################################################

class AskText(object):
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
        # options.ids = [...]
        # options.text = "..."

        # Find root element
        root, text, preamble_file = self.get_tex_code()
        
        # Ask for TeX code
        asker = AskText(text, preamble_file, 56.0/10.0)
        text, preamble_file, scale_factor = asker.ask()

        # Convert & read SVG
        try:
            self.convert(root, text, preamble_file, scale_factor)
        except Exception, e:
            traceback.print_exc()

    def get_tex_code(self):
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
        if root.hasAttribute('x'):
            transform = 'translate(%s, %s)' % (x_pos, y_pos)
        elif root.hasAttribute('transform'):
            transform = root.getAttribute('transform')
        else:
            transform = 'scale(%f,%f)' % (scale_factor, scale_factor)
        
        parent = root.parentNode
        parent.removeChild(root)

        paths = self.tex_to_paths(latex_text, preamble_file)
        newgroup = self.document.createElement('svg:g')

        parent.appendChild(newgroup)
        if transform:
            newgroup.setAttribute('transform', transform)
        newgroup.setAttribute('textext',latex_text.encode('string-escape'))
        newgroup.setAttribute('texpreamble',preamble_file.encode('string-escape'))

        for p in paths:
            if p.nodeType == p.ELEMENT_NODE:
                attr_style = p.getAttributeNode('style')
                attr_d =  p.getAttributeNode('d')
                newpath = self.document.createElement('svg:path')
                newgroup.appendChild(newpath)
                newpath.setAttribute('style', attr_style.value)
                newpath.setAttribute('d', attr_d.value)

    def tex_to_paths(self, latex_text, preamble_file):
        # Set use_times & use_sans
        text = latex_text
        preamble = ""

        if os.path.exists(preamble_file):
            f = open(preamble_file, 'r')
            preamble += f.read()
            f.close()

        # Create SVG file
        svg_out = self.tex_svg(text, preamble)

        # create xml parser for generated svg
        reader_tex = xml.dom.ext.reader.Sax2.Reader()
        stream_tex = open(svg_out, 'r')
        doc_tex = reader_tex.fromStream(stream_tex)
        stream_tex.close()

        # Remove generated svg file
        self.try_remove(svg_out)
        
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
        Create a SVG file from latex_text and returns filename of
        generated SVG file.
        latex_text: String that will pass to latex,
                    e.g., '$$\sum_{0 \leq k \leq n} x_k$$'
        preamble: TeX going into preamble
        """
        # Options pass to LaTeX-related commands
        latexOpts = '-interaction=nonstopmode'
    
        # Options for pstoedit command
        pstoeditOpts = '-dt -psarg "-r9600x9600"'

        texwrapper = r"""
        \documentclass[landscape,a3]{article}
        %s
        \pagestyle{empty}
        \begin{document}
        \noindent
        %s
        \end{document}
        """ % (preamble, latex_text)

        temppath = tempfile.gettempdir()
        file = tempfile.mktemp()

        cm_exc = RuntimeError
        msgs = ''
    
        try:
            f_tex = open('%s.tex' % file, 'w')
            f_tex.write(texwrapper)
            f_tex.close()
            if not os.path.exists('%s.tex' % file):
                raise cm_exc, ("LaTeX File\n", "Can't create tempory file %s.tex" % file)

            res = self.exec_command('cd %s; pdflatex %s %s < /dev/null 2>&1' % (temppath, latexOpts, file))
            if not os.path.exists('%s.pdf' % file):
                raise cm_exc, ("pdfLaTeX\n", res)
            msgs = msgs + '--pdflatex--\n' + res

            # Exec pstoedit: eps -> sk
            res = self.exec_command('pstoedit %s -f sk %s.pdf %s.sk 2>&1' % (pstoeditOpts, file, file))
            if not os.path.exists('%s.sk' % file):
                raise cm_exc, ("pstoedit",res)
            msgs = msgs + '--pstoedit--\n' + res

            # Exec skconvert: sk -> svg
            res = self.exec_command('skconvert %s.sk %s.svg' % (file, file))
            if not os.path.exists('%s.svg' % file):
                raise cm_exc, ("skconvert",res)
            msgs = msgs + '--skconvert--\n' + res

        except Exception, e:
            traceback.print_exc()

        self.remove_temp_files(file)
        return '%s.svg' % file
    ### End of tex2svg

    def exec_command(self, command):
        file = os.popen(command, 'r')
        message = file.read()
        file.close()
        return message
    ### End of exec_command

    def remove_temp_files(self, filename):
        """Remove files made in /tmp"""
        self.try_remove(filename + '.tex')
        self.try_remove(filename + '.dvi')
        self.try_remove(filename + '.log')
        self.try_remove(filename + '.aux')
        self.try_remove(filename + '.pdf')
        self.try_remove(filename + '.sk')

    def try_remove(self, filename):
        try:
            os.remove(filename)
        except OSError:
            pass

    def get_latex_text(self, text_node):
        """
        get texts of text element of inkscape SVG
        text_node: text element node of DOM
        return: texts in text_node
        """
        tex_text = ""
        for child in text_node.childNodes:
            if (child.nodeName == 'tspan'):
                for txt in child.childNodes:
                    if txt.nodeType == txt.TEXT_NODE:
                        tex_text = tex_text + txt.data
        return tex_text

e = TexText()
e.affect()
