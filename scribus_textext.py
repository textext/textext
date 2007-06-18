#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============
scribus_textext
===============

:Author: Pauli Virtanen <pav@iki.fi>
:Date: 2007-06-17
:License: BSD

Scribus_textext is an extension for Scribus_ that allows adding
LaTeX-generated text objects to your SVG drawing. What's more, you can
also *edit* these text objects after creating them.

This brings some of the power of TeX typesetting to Scribus.

.. _Scribus: http://www.scribus.net/
"""

__version__ = "0.2"
__author__ = "Pauli Virtanen <pav@iki.fi>"
__docformat__ = "restructuredtext en"

#------------------------------------------------------------------------------

import os, sys, tempfile, traceback, subprocess, time, shutil, Image, glob

try:
    import scribus
except ImportError, err:
    print "This script will not work outside Scribus"
    sys.exit(1)

try:
    from qt import *
except ImportError, err:
    print "This script will not work without pyQt"
    scribus.messageBox("Error",
                       "This script will not work without pyQt\n"
                       "Please install pyQt and try again",
                       scribus.ICON_WARNING)
    sys.exit(1)

# NOTE:: We *must* keep a reference to the main_widget
#        on the top level of the module. Otherwise,
#        created QWidget objects are deleted too early.
main_widget = qApp.mainWidget()

#------------------------------------------------------------------------------

class LatexDialog(QDialog):
    """GUI for editing TexText objects"""

    def __init__(self, text, preamble_file, scale_factor,
                 parent=None, root=None):
        QDialog.__init__(self, parent)
        self.setCaption("TeX text object")
        
        self.preamble = QLineEdit(self)
        self.scale    = QSpinBox(0.1, 10, 1, self)
        self.text     = QMultiLineEdit(self)
        self.ok       = QPushButton("OK", self)
        self.cancel   = QPushButton("Cancel", self)
        
        self.text.setText(text)
        self.preamble.setText(preamble_file)
        self.scale.setValue(scale_factor)
        
        layout = QVBoxLayout(self)
        layout_btn = QHBoxLayout(None)
        
        layout.addWidget(self.preamble)
        layout.addWidget(self.scale)
        layout.addWidget(self.text)

        layout_btn.addWidget(self.ok)
        layout_btn.addWidget(self.cancel)
        layout.addLayout(layout_btn)
        
        self.connect(self.ok, SIGNAL("clicked()"), self.slotOkClicked)
        self.connect(self.cancel, SIGNAL("clicked()"), self, SLOT("reject()"))

        self.fetch_info()

    def get_new_image_name(self):
        count = 0
        while True:
            name = 'latex-image-%d' % count
            if not os.path.exists('%s.png' % name):
                return name
            count += 1

    def fetch_info(self):
        try:
            name = scribus.getImageFile()
            info_name = '%s.info' % name

            if os.path.exists(info_name):
                f = open(info_name, 'r')
                try:
                    preamble = f.readline().strip()
                    scale = float(f.readline().strip())
                    text = f.read()

                    self.text.setText(text)
                    self.scale.setValue(scale)
                    self.preamble.setText(preamble)
                finally:
                    f.close()
        except scribus.NoValidObjectError:
            return

    def slotOkClicked(self):
        text = self.text.text()
        preamble = self.preamble.text()
        scale = self.scale.value()

        DPI = 600.0

        try:
            img = scribus.getSelectedObject()
            img_file = scribus.getImageFile()
        except scribus.NoValidObjectError:
            
            img = scribus.createImage(0, 0, 10, 10, self.get_new_image_name())
            img_file = os.path.abspath('%s.png' % img)

        self.generate_latex(text, preamble, scale, img_file, DPI*scale)

        info = open(img_file + '.info', 'w')
        info.write("%s\n" % preamble)
        info.write("%g\n" % scale)
        info.write(text)
        info.close()

        x = Image.open(img_file, 'r')
        w, h = x.size
        del x

        scribus.loadImage(img_file, img)
        scribus.setScaleImageToFrame(True, True, img)
        x, y = scribus.getPosition(img)
        scribus.sizeObject(x + w*25.4/DPI, y + h*25.4/DPI, img)
        
        self.accept()

    def generate_latex(self, text, preamble, scale, output, dpi):
        if os.path.isfile(preamble):
            f = open(preamble, 'r')
            try:
                preamble = f.read()
            finally:
                f.close()
        else:
            preamble = ""
        
        latexOpts = ['-interaction=nonstopmode']
        texwrapper = r"""
        \documentclass[landscape,a0]{article}
        %s
        \pagestyle{empty}
        \begin{document}
        \noindent
        %s
        \end{document}
        """ % (preamble, text)

        path = tempfile.mkdtemp()
        cwd = os.getcwd()
        os.chdir(path)

        def tmp(name):
            return os.path.join(path, name)

        # Convert TeX to SVG
        try:
            # Write tex
            f_tex = open(tmp('x.tex'), 'w')
            try:
                f_tex.write(texwrapper.strip())
            finally:
                f_tex.close()

            self.exec_command(['latex', tmp('x.tex')] + latexOpts)
            if not os.path.exists(tmp('x.dvi')):
                raise RuntimeError("latex didn't produce output")

            self.exec_command(['dvipng', '-D', '%d' % dpi, '-o', tmp('x.png'),
                               '-T', 'tight', tmp('x.dvi')])
            if not os.path.exists(tmp('x.png')):
                raise RuntimeError("dvipng didn't produce output")

            os.chdir(cwd)
            shutil.copy(tmp('x.png'), output)
        finally:
            os.chdir(cwd)
            self.remove_temp_files(path)

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
                         'x.pdf.sk', 'x.eps', 'x.dvi', 'x.ps', 'x.png']:
            self.try_remove(os.path.join(path, filename))
        self.try_remove(path)

    def try_remove(self, filename):
        """Try to remove given file, skipping if not exists."""
        if os.path.isfile(filename):
            os.remove(filename)
        elif os.path.isdir(filename):
            os.rmdir(filename)

def cleanup_dead_images(self):
    files = glob.glob('latex-image-*.png')
    for filename in files:
        imgname = filename[:-4]
        try:
            img_file = scribus.getImageFile(imgname)
            continue
        except scribus.NoValidObjectError:
            pass
        
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(filename + '.info'):
            os.remove(filename + '.info')

def insert_latex_object():
    main_widget = qApp.mainWidget()
    text = ""
    preamble_file = "header.inc"
    dlg = LatexDialog(text, preamble_file, 1.0, main_widget)
    dlg.show()

def get_extension_menu():
    main_widget = qApp.mainWidget()
    menus =  main_widget.queryList("QPopupMenu", "extensionsMenu")
    if menus:
        menu = menus[0]
    else:
        menu = QPopupMenu(main_widget, "extensionsMenu")
        try:
            menu_bar = main_widget.menuBar()
        except AttributeError:
            # old pyqt
            menu_bar = main_widget.queryList("QMenuBar", None, True, False)[0]
        menu_bar.insertItem("Extensions", menu, -1, menu_bar.count()-1)
    return menu

def main(argv):
    menu = get_extension_menu()
    menu.insertItem("Insert/modify LaTeX object", insert_latex_object)
    menu.insertItem("Clean up dead LaTeX images", cleanup_dead_images)

if __name__ == "__main__":
    main(sys.argv[1:])
