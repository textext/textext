.. |TexText| replace:: **TexText**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. |usage-label-1| image:: images/annotation_label_1.png
            :height: 1em
            :width: 1em
            :target: usage-dialog-overview_

.. |usage-label-2| image:: images/annotation_label_2.png
            :height: 1em
            :width: 1em
            :target: usage-dialog-overview_

.. |usage-label-3| image:: images/annotation_label_3.png
            :height: 1em
            :width: 1em
            :target: usage-dialog-overview_

.. |usage-label-4| image:: images/annotation_label_4.png
            :height: 1em
            :width: 1em
            :target: usage-dialog-overview_

.. |usage-label-5| image:: images/annotation_label_5.png
            :height: 1em
            :width: 1em
            :target: usage-dialog-overview_

.. |usage-label-6| image:: images/annotation_label_6.png
            :height: 1em
            :width: 1em
            :target: usage-dialog-overview_

.. _usage:

.. _usage-extension-entry:

|TexText| extension entry
-------------------------

After installation |TexText| will appear under :menuselection:`Extensions --> Tex Text`:

.. figure:: images/inkscape-extension.png
   :alt: Extension entry

When you select it, a dialog will appear that lets you enter any LaTeX
code you want (presumably your formula).

.. _usage-dialog-overview:

Dialog overview
---------------

.. figure:: images/textext-dialog-annotated.png
   :alt: Annotated TexText dialog


You enter your LaTeX code into the edit box |usage-label-5|. In the case you
installed PyGTK it will show you line and column numbers. If you
additionally insalled PyGTKSourceView it will also highlight the syntax
with colors. You can add any valid and also multiline LaTeX code.
There are additional settings which can be adjusted to your needs:

-  Custom :ref:`usage-preamble-file`
-  The TeX command to be used for compiling your code (group box |usage-label-2|).
   Possible options are: :bash:`pdflatex`, :bash:`xelatex`, :bash:`lualatex`. See
   section :ref:`usage-tex-compilers` for more details.
-  The scale factor (group box |usage-label-3|). See section :ref:`usage-scaling`.
-  The alignment relative to the previous version of your code (group
   box |usage-label-4|, only available when re-editing your code). See section :ref:`usage-alignment`.
-  The coloring of the output using TeX commands or Inkscape settings.
   See section :ref:`usage-colorization`.

Your LaTeX code and the accompanying settings will be stored within the
new SVG node in the document. This allows you to edit the LaTeX node
later by selecting it and running the *Tex Text* extension (which will
then show the dialog containing the saved values).

There is a preview button |usage-label-6| as well, which shortens the feedback cycle
from entry to result considerably, so use it! See section :ref:`usage-preview`

.. _usage-preamble-file:

Preamble file
-------------
Be aware of including the required packages in the *preamble file* if you
use special commands in your code that rely on such packages. The
preamble file can be choosen by the selector |usage-label-1|. The default preamble
file shipped with TexText includes the following packages:

.. code-block:: latex

    \usepackage{amsmath,amsthm,amssymb,amsfonts}
    \usepackage{color}

Basically, your LaTeX code will be inserted into this environment:

.. code-block:: latex

    \documentclass{article}
    % ***preamble file content***
    \pagestyle{empty}
    \begin{document}
    % ***Your code***
    \end{document}

This will be typeset, converted to SVG and inserted into your Inkscape
document.


.. _usage-tex-compilers:

Available TeX compilers
-----------------------

.. versionadded:: 0.8.0

Your LaTeX code can be compiled using three different compilers:
:bash:`pdflatex`, :bash:`xelatex`, :bash:`lualatex` (as long as the corresponding
commands are found by your system). You can select the command in the
combobox |usage-label-2|. The last two ones are especially useful for using UTF-8
input or if you require Lua commands. Of course you can use UTF-8 input
with the :bash:`pdflatex` command as well as long as you provide
:latex:`\usepackage[utf8]{inputenc}`
in your preamble file.

Some things to be kept in mind:

 - Place the required lua packages in your preamble file if you want to
   compile your code with :bash:`lualatex`.
 - If you use :bash:`lualatex`/ :bash:`xelatex` for the very first time on your
   system it may take some time until the fonts are setup properly.
   During that time TexText might be unresponsive.
 - Windows: :bash:`xelatex`\ tends to be very slow on Windows machines, see
   this post on
   `Stackexchange <https://tex.stackexchange.com/questions/357098/compiling-tex-files-with-xelatex-is-insanely-slow-on-my-windows-machine/357100>`__.

.. _usage-scaling:

The scaling of the output
-------------------------

In most of the cases you will need to adjust the size of the produced
SVG output to match the conditions of your drawing. This can be done by
two methods:

1. After compilation adjust the size of the SVG output using the mouse
   in Inkscape. You should lock the width and height to keep the
   proportion. Be careful to not break the group!
2. Before compilation you specifiy a scale factor in the spinbox of the
   groupbox |usage-label-3|.

Both methods are fully compatible. If you scale your SVG output in
Inkscape the numerical value of the spinbox will be adjusted
appropriately when you open TexText on that node later. In both cases
the scale factor is preserved when you re-edit your code.

A scale factor of 1 means that the output is sized as it would appear in
a regular LaTeX document, i.e., a font size of ``x pt`` in LaTex matches
that of ``x pt`` in Inkscape:

.. figure:: images/texttext-fontsize-example.png
   :alt: Font size example


There are two additional buttons in the groupbox |usage-label-3|:

-  *Reset*: This button is only available when re-editing existing
   TexText nodes. It resets the scale factor to the value the code has
   been compiled with the last time. This is useful when playing around
   with the scale factor and decide to not change the scale factor.
-  *As previous*: This button sets the scale factor of the currently
   edited node to the value of the node which has been edited
   previously. This is useful when you found a scale factor to be
   suitable and want to apply this scale factor also to any new or
   existing nodes you open for editing.

If you have re-sized the SVG output in Inkscape *without* keeping the
proportions the re-compiled output will be placed with correct
proportions according to the `alignment <usage-alignment_>`_.

.. _usage-alignment:

The alignment of the output
---------------------------

.. versionadded:: 0.8.0

When you edit existing nodes it is likely that the size of the produced
output will change, for example if you modify the input :latex:`$\sin(x)$` to
:latex:`$\int\sin(x)\text{d}x$`. The entries of the spinbox |usage-label-4| determine how
the new node is aligned relatively to the old node. The default
behaviour is ``middle center``. Available options are: ``top left``,
``middle left``, ``bottom left``, ``top center``, ``middle center``,
``bottom center``, ``top right``, ``middle right``, ``bottom right``.

.. figure:: images/textext-alignment-example.png
   :alt: Alignment example


Of course, the content of the groupbox |usage-label-4| is only available when
editing existing nodes.

.. _usage-colorization:

The colorization of the output
------------------------------

There are two ways for colorization of the output:

 1. The most natural way is to select the produced SVG output in Inkscape and set the fill
    **and** the contour color to the same value according to your needs.
    When you re-compile your node this color will be persevered as long as
    you do not use any color specifications in your LaTeX code. You can also
    colorize characters individually be selecting them with the mouse after
    having pressed :kbd:`F2`. Be careful not to break the group.

 .. caution::

    Individual symbol colorization done in inkscape *will not* be kept after
    re-compilation.


 2. Alternatively, you can use LaTeX commands like
    :latex:`\textcolor` in your code to colorize the node according to your
    needs. If you use such commands any colorization done by Inkscape will
    be lost after re-compilation. This method is the recommended one if you
    would like a character wise colorization of your output.


.. _usage-preview:

The preview button
------------------

.. important::

    This feature is not available in the Tkinter GUI!

When pressing the ``Preview`` button your code will be compiled and the result
is displayed as an image in the area below the LaTeX code input field. If the
output extends a certain size it is displayed scaled so it fits into the available
area. You can double click into the preview image to obtain the result in original
size. Then, you can use the horizontal and vertical scroll bars to navigate along
your result. Double clicking again will bring you back to the scaled version of the
output.

.. figure:: images/textext-dialog-preview.png
   :alt: Annotated TexText dialog

Finally, click the ``Save`` button to insert the compiled code into your document.


.. _usage-font:

Using specific font sizes or special fonts
------------------------------------------

.. _usage-font-size:

Explicit setting of font size
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want the font size of your compiled LaTeX code to be of a
specific size then you have to do two things:

1. Set the scale factor of the node to 1.0

2. Enter your code as following if you want to have a ``14pt`` sized font
   for the text `This is my Text`\:

.. code-block:: latex

    \fontsize{14pt}{1em}{\selectfont This is my Text.}


The resulting text should be of equal height as if has been typeset directly in Inkscape.

.. _usage-font-custom-font:

Selection of special fonts
~~~~~~~~~~~~~~~~~~~~~~~~~~

Usually your code is typeset in the LaTeX standard fonts. As usual, you
can use commands like :latex:`\textbf{}`, :latex:`\textsf{}` etc. in your code. If
you want to select a special font, e.g. the beloved *Times New Roman*
from MS Word, then proceed as follows:


1. Open the file ``default_packages.tex`` which resides in the extension
   subdirectory (``%USERPROFILE%\AppData\Roaming\Inkscape\extensions\textext`` on Windows,
   ``~/.config/inkscape/extensions/textext`` on Linux) and enter the following
   two lines:


.. code-block:: latex

    \usepackage{fontspec}
    \setmainfont{Times New Roman}



2. Save the file and recompile your node. You can also define different
   preamble files and load them dependent on your node, see :ref:`usage-dialog-overview`.


..