#! /usr/bin/env python
# Time-stamp: <06/03/17 13:50:56 arakit>

import sys
sys.path.append('/usr/share/inkscape/extensions/')

import Tkinter as Tk

import inkex
import tempfile, traceback
import os, sys
import xml.dom.ext.reader.Sax2

######################################################################

class AskText(object):
    def __init__(self, text, preamble_file):
        self.text = text
        self.preamble_file = preamble_file

    def ask(self):
        root = Tk.Tk()
        #
        self._frame = Tk.Frame(root)
        self._frame.pack()
        #
        self._preamble = Tk.Entry(self._frame)
        self._preamble.pack()
        self._preamble.insert(Tk.END, self.preamble_file)
        #
        self._text = Tk.Text(self._frame)
        self._text.pack()
        self._text.insert(Tk.END, self.text)
        #
        self._btn = Tk.Button(self._frame, text="OK", command=self.cb_ok)
        self._btn.pack()
        #
        root.mainloop()

        return self.text, self.preamble_file
    
    def cb_ok(self):
        self.text = self._text.get(1.0, Tk.END)
        self.preamble_file = self._preamble.get()
        self._frame.quit()

class TexText(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

    def effect(self):
        # options.ids = [...]
        # options.text = "..."

        # Find root element
        root, text, preamble_file = self.get_tex_code()
        
        # Ask for TeX code
        asker = AskText(text, preamble_file)
        text, preamble_file = asker.ask()

        # Convert & read SVG
        try:
            self.convert(root, text, preamble_file)
        except Exception, e:
            traceback.print_exc()

    def get_tex_code(self):
        for i in self.options.ids:
            node = self.selected[i]
            if node.tagName == 'g' and node.hasAttribute('textext'):
                return (node,
                        node.getAttribute('textext').decode('string-escape'),
                        node.getAttribute('preamble').decode('string-escape'))
        newone = self.document.createElement('g')
        self.document.documentElement.appendChild(newone)
        return newone, "", "header.inc"

    def convert(self, root, latex_text, preamble_file):
        parent = root.parentNode
        parent.removeChild(root)

        paths = self.tex_to_paths(latex_text, preamble_file)
        newgroup = self.document.createElement('svg:g')

        parent.appendChild(newgroup)
        #newgroup.setAttribute('transform',
        #                      'translate(%s, %s)'%(x_pos.value, y_pos.value))
        newgroup.setAttribute('textext',latex_text.encode('string-escape'))
        newgroup.setAttribute('preamble',preamble_file.encode('string-escape'))

        for p in paths:
            if p.nodeType == p.ELEMENT_NODE:
                attr_style = p.getAttributeNode('style')
                attr_d =  p.getAttributeNode('d')
                newpath = self.document.createElement('svg:path')
                newgroup.appendChild(newpath)
                newpath.setAttribute('style', attr_style.value)
                newpath.setAttribute('d', attr_d.value)

    def tex_to_paths(self, latex_text, preamble_file):
        # Set scale from size
        scale = 56.0/10.0
        # Set use_times & use_sans
        text = latex_text
        preamble = ""

        if os.path.exists(preamble_file):
            f = open(preamble_file, 'r')
            preamble += f.read()
            f.close()

        # Create SVG file
        svg_out = self.tex_svg(text, scale, preamble)

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

    def tex_svg(self, latex_text, scale, preamble):
        """
        Create a SVG file from latex_text and returns filename of
        generated SVG file.
        latex_text: String that will pass to latex,
                    e.g., '$$\sum_{0 \leq k \leq n} x_k$$'
        scale: Use (scale x 10) point fonts
        preamble: TeX going into preamble
        """
        # Options pass to LaTeX-related commands
        latexOpts = '-interaction=nonstopmode'
    
        # Options for pstoedit command
        pstoeditOpts = '-dt -psarg "-r9600x9600"'
        if scale != 1:
            pstoeditOpts = pstoeditOpts + ' ' + '-xscale %s -yscale %s' % (scale, scale)

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

        cm_exc = 'cm_exc'
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
            traceback.print_exc(file=log)

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

