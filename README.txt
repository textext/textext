=======
textext
=======

Inkscape is a great program. But if you try to make a conference poster with
it, you'll see that what is missing is scientific typesetting.

Some solutions, such as Inklatex, have been written, but generally these do not
allow editing the generated objects afterwards. Textext aims to cover this
need, by adding re-editable LaTeX objects to Inkscape's repertoire.


Usage
=====

To create a new LaTeX object, choose Effects -> Tex Text, and type in your
LaTeX code. The dialog has two additional fields:

- Preamble file: name of a LaTeX preamble file, where you can put common definitions.

- Scale factor: this affects how much a newly created LaTeX object is
  magnified. You can later change/reset this via Object -> Transform -> Matrix.

- Page width.

- Whether to do text-to-path conversion.

  Note that if you want to have real text objects in your SVG files, you need
  to have Truetype/OTF/etc. versions of the Latex font set installed.

Afterwards, the object can be re-edited by selecting it and choosing Effects ->
Tex Text again.

Note: for Inkscape versions earlier than 0.46, Inkscape's user interface
freezes while you are editing the LaTeX object. This is a limitation of the
Inkscape extension model. (If you know better, please inform me how it should
be done ;)


Installation
============

On Linux, you'll need to have pdflatex and one of the following installed:

- Inkscape >= 0.47
- Pdf2svg (the one by David Barton & Matthew Flaschen, not the one by PDFtron)
- Pstoedit with its plot-svg back-end compiled in, or,
- Pstoedit and Skconvert, or,

Unpack the newest version of the Textext package and copy its files to
``~/.config/inkscape/extensions/``. If you are using Inkscape version earlier than
0.47 then the correct place is ``~/.inkscape/extensions/``.

Note that Textext (starting from version 0.4), like the other Inkscape 0.46
extensions, requires that lxml is installed. (On Ubuntu, this is in the
python-lxml package.) Textext 0.4 requires Inkscape 0.46, so if you are using
an older version of Inkscape, stick with Textext 0.3.4.

On Windows with Inkscape 0.46, the easiest way is to get the installer from the
Textext home page. Note that you can "Upgrade" to newer Textext versions from older
ones, just by finding the "textext.py" file and replacing it with a newer one!

On Mac OS X, you will need to install a working version of pstoedit (apparently
Fink and MacPorts offer binaries). After that, you may be lucky and get Textext
to work on Inkscape 0.46 by copying textext.py and textext.inx to the
extensions folder under the Inkscape folder; but I haven't tested this.

