.. |TexText| replace:: **TexText 0.11**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. |tt0x-usage-label-1| image:: ../images/annotation_label_1.png
            :height: 1em
            :width: 1em
            :target: tt0x-usage-dialog-overview_

.. |tt0x-usage-label-2| image:: ../images/annotation_label_2.png
            :height: 1em
            :width: 1em
            :target: tt0x-usage-dialog-overview_

.. |tt0x-usage-label-3| image:: ../images/annotation_label_3.png
            :height: 1em
            :width: 1em
            :target: tt0x-usage-dialog-overview_

.. |tt0x-usage-label-4| image:: ../images/annotation_label_4.png
            :height: 1em
            :width: 1em
            :target: tt0x-usage-dialog-overview_

.. |tt0x-usage-label-5| image:: ../images/annotation_label_5.png
            :height: 1em
            :width: 1em
            :target: tt0x-usage-dialog-overview_

.. |tt0x-usage-label-6| image:: ../images/annotation_label_6.png
            :height: 1em
            :width: 1em
            :target: tt0x-usage-dialog-overview_

.. |tt0x-usage-label-7| image:: ../images/annotation_label_7.png
            :height: 1em
            :width: 1em
            :target: tt0x-usage-dialog-overview_

.. |tt0x-usage-label-8| image:: ../images/annotation_label_8.png
            :height: 1em
            :width: 1em
            :target: tt0x-usage-dialog-overview_

.. |tl| image:: ../images/alignment-top-left.svg.png
            :target: tt0x-usage-alignment_

.. |tc| image:: ../images/alignment-top-center.svg.png
            :target: tt0x-usage-alignment_

.. |tr| image:: ../images/alignment-top-right.svg.png
            :target: tt0x-usage-alignment_

.. |ml| image:: ../images/alignment-middle-left.svg.png
            :target: tt0x-usage-alignment_

.. |mc| image:: ../images/alignment-middle-center.svg.png
            :target: tt0x-usage-alignment_

.. |mr| image:: ../images/alignment-middle-right.svg.png
            :target: tt0x-usage-alignment_

.. |bl| image:: ../images/alignment-bottom-left.svg.png
            :target: tt0x-usage-alignment_

.. |bc| image:: ../images/alignment-bottom-center.svg.png
            :target: tt0x-usage-alignment_

.. |br| image:: ../images/alignment-bottom-right.svg.png
            :target: tt0x-usage-alignment_

.. _tt0x-gui:

The GUI (TexText 0.11)
======================

.. contents:: :local:

.. _tt0x-usage-extension-entry:

|TexText| extension entry
-------------------------

After installation |TexText| will appear under :menuselection:`Extensions --> Tex Text`:

.. figure:: ../images/inkscape-extension.png
   :alt: Extension entry

When you select it, a dialog will appear that lets you enter any LaTeX
code you want (presumably your formula).

.. _tt0x-usage-dialog-overview:

Dialog overview
---------------

.. figure:: ../images/textext-dialog-annotated.png
   :alt: Annotated TexText dialog


You enter your LaTeX code into the edit box |tt0x-usage-label-5|. In the case you
installed PyGTK it will show you line and column numbers. If you
additionally installed PyGTKSourceView it will also highlight the syntax
with colors. You can add any valid and also multi-line LaTeX code.
There are additional settings which can be adjusted to your needs:

-  The TeX command to be used for compiling your code (group box |tt0x-usage-label-1|).
   Possible options are: :bash:`pdflatex`, :bash:`xelatex`, :bash:`lualatex`. See
   section :ref:`tt0x-usage-tex-compilers` for more details.
-  Custom :ref:`tt0x-usage-preamble-file` (group box |tt0x-usage-label-2|)
-  The scale factor (group box |tt0x-usage-label-3|). See section :ref:`tt0x-usage-scaling`.
-  The alignment relative to the previous version of your code (group
   box |tt0x-usage-label-4|, only available when re-editing your code). See section :ref:`tt0x-usage-alignment`.
-  The coloring of the output using TeX commands or Inkscape settings.
   See section :ref:`tt0x-usage-colorization`.
-  The default math environment in new nodes (menu |tt0x-usage-label-7|), see section :ref:`tt0x-usage-default-math-environment-config`.
-  The appearance of the editor (menu |tt0x-usage-label-8|), see section :ref:`tt0x-usage-gui-config`.

Your LaTeX code and the accompanying settings will be stored within the
new SVG node in the document. This allows you to edit the LaTeX node
later by selecting it and running the *Tex Text* extension (which will
then show the dialog containing the saved values).

There is a preview button |tt0x-usage-label-6| as well, which shortens the feedback cycle
from entry to result considerably, so use it! See section :ref:`tt0x-usage-preview`


.. _tt0x-usage-tex-compilers:

Available TeX compilers
-----------------------

.. versionadded:: 0.8.0

Your LaTeX code can be compiled using three different compilers:
:bash:`pdflatex`, :bash:`xelatex`, :bash:`lualatex` (as long as the corresponding
commands are found by your system). You can select the command in the
combobox |tt0x-usage-label-1|. The last two ones are especially useful for using UTF-8
input or if you require Lua commands. Of course you can use UTF-8 input
with the :bash:`pdflatex` command as well as long as you provide
:latex:`\usepackage[utf8]{inputenc}` in your preamble file (see :ref:`tt0x-usage-preamble-file`).

Some things to be kept in mind:

 - Place the required lua packages in your `preamble file <tt0x-usage-preamble-file_>`_ if you want to
   compile your code with :bash:`lualatex`.
 - If you use :bash:`lualatex`/ :bash:`xelatex` for the very first time on your
   system it may take some time until the fonts are setup properly.
   During that time |TexText| might be unresponsive.
 - Windows: :bash:`xelatex`\ tends to be very slow on Windows machines, see
   this post on
   `Stackexchange <https://tex.stackexchange.com/questions/357098/compiling-tex-files-with-xelatex-is-insanely-slow-on-my-windows-machine/357100>`__.

.. _tt0x-usage-preamble-file:

Preamble file
-------------
Be aware of including the required packages in the *preamble file* if you
use special commands in your code that rely on such packages. The
preamble file can be chosen by the selector |tt0x-usage-label-2|. The default preamble
file shipped with |TexText| includes the following packages:

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

.. _tt0x-usage-scaling:

Scaling of the output
---------------------

In most of the cases you will need to adjust the size of the produced
SVG output to match the conditions of your drawing. This can be done by
two methods:

1. After compilation adjust the size of the SVG output using the mouse
   in Inkscape. You should lock the width and height to keep the
   proportion. Be careful to not break the group!
2. Before compilation you specify a scale factor in the spinbox of the
   groupbox |tt0x-usage-label-3|.

Both methods are fully compatible. If you scale your SVG output in
Inkscape the numerical value of the spinbox will be adjusted
appropriately when you open |TexText| on that node later. In both cases
the scale factor is preserved when you re-edit your code.

A scale factor of 1 means that the output is sized as it would appear in
a regular LaTeX document, i.e., a font size of ``x pt`` in LaTex matches
that of ``x pt`` in Inkscape:

.. figure:: ../images/texttext-fontsize-example.png
   :alt: Font size example


There are two additional buttons in the groupbox |tt0x-usage-label-3|:

-  *Reset*: This button is only available when re-editing existing
   |TexText| nodes. It resets the scale factor to the value the code has
   been compiled with the last time. This is useful when playing around
   with the scale factor and decide to not change the scale factor.
-  *As previous*: This button sets the scale factor of the currently
   edited node to the value of the node which has been edited
   previously. This is useful when you found a scale factor to be
   suitable and want to apply this scale factor also to any new or
   existing nodes you open for editing.

If you have re-sized the SVG output in Inkscape *without* keeping the
proportions the re-compiled output will be placed with correct
proportions according to the `alignment <tt0x-usage-alignment_>`_.

.. _tt0x-usage-alignment:

Alignment of the output
-----------------------

.. versionadded:: 0.8.0

When you edit existing nodes it is likely that the size of the produced
output will change, for example if you modify the input :latex:`$\sin(x)$` to
:latex:`$\int\sin(x)\text{d}x$`. The entries of the spinbox |tt0x-usage-label-4| determine how
the new node is aligned relatively to the old node. The default
behaviour is ``middle center``, i.e. the middle of the new node is placed
on the middle of the old node. Available options are:

+-----------------+-------------------+------------------+
| |tl|            | |tc|              | |tr|             |
|                 |                   |                  |
| ``top left``    | ``top center``    | ``top right``    |
+-----------------+-------------------+------------------+
| |ml|            | |mc|              | |mr|             |
|                 |                   |                  |
| ``middle left`` | ``middle center`` | ``middle right`` |
+-----------------+-------------------+------------------+
| |bl|            | |bc|              | |br|             |
|                 |                   |                  |
| ``bottom left`` | ``bottom center`` | ``bottom right`` |
+-----------------+-------------------+------------------+

.. figure:: ../images/textext-alignment-example.png
   :alt: Alignment example


Of course, the content of the groupbox |tt0x-usage-label-4| is only available when
editing existing nodes.

.. _tt0x-usage-colorization:

Colorization of the output
--------------------------

There are two ways for colorization of the output:

 1. The most natural way is to select the produced SVG output in Inkscape and set the fill
    **and** the contour color to the same value according to your needs.
    When you re-compile your node this color will be persevered as long as
    you do not use any color specifications in your LaTeX code. You can also
    colorize characters individually be selecting them with the mouse after
    having pressed :kbd:`F2`. Be careful not to break the group.

    .. caution::

       Individual symbol colorization done in Inkscape *will not* be kept after
       re-compilation.


 2. Alternatively, you can use LaTeX commands like
    :latex:`\textcolor` in your code to colorize the node according to your
    needs. If you use such commands any colorization done by Inkscape will
    be lost after re-compilation. This method is the recommended one if you
    would like a character wise colorization of your output.

.. _tt0x-usage-preview:

Preview button
--------------

When pressing the ``Preview`` button |tt0x-usage-label-6| your code will be compiled and the result
is displayed as an image in the area below the LaTeX code input field. If the
output extends a certain size it is displayed scaled so it fits into the available
area. You can double click into the preview image to obtain the result in original
size. Then, you can use the horizontal and vertical scroll bars to navigate along
your result. Double clicking again will bring you back to the scaled version of the
output.

.. figure:: ../images/textext-dialog-preview.png
   :alt: Annotated TexText dialog

Finally, click the ``Save`` button to insert the compiled code into your document.

.. note::

    This feature is not available in the Tkinter GUI!

.. _tt0x-usage-default-math-environment-config:

Configuration of the default TeX math-environment
-------------------------------------------------

.. versionadded:: 0.10.0

You can open the ``Settings`` menu |tt0x-usage-label-7| and then ``New Node Content``
to define which environment should be selected by default when creating new nodes.

.. figure:: ../images/textext-dialog-with-settings-menus-new-node.png
    :alt: TexText settings menu (new node content)

You have the following options:

- ``Empty``: The code editor is empty.

- ``Inline math``: The code editor is filled with ``$$`` for typesetting an inline math expression.

- ``Display math``: The code editor is filled with ``$$$$`` for typesetting a display math expression.

(`Reminder on the difference between inline and display math <https://en.wikibooks.org/wiki/LaTeX/Mathematics#Mathematics_environments>`_)

.. note::

    Currently, this feature is not available in the Tkinter GUI!

.. _tt0x-usage-close-shortcut-config:

Selecting the shortcut for closing the |TexText| window
-------------------------------------------------------

.. versionadded:: 0.11.0

In the ``Settings`` menu |tt0x-usage-label-7| you can configure by ``Confirm Closing Window`` if |TexText| should ask for
confirmation to close the window in case you made changes to your text. Furthermore, under ``Close TexText Shortcut``
you can select a shortcut for closing the |TexText| window.

.. figure:: ../images/textext-dialog-with-settings-menus-close-shortcut.png
    :alt: TexText settings menu (close shortcut)

You have the following options:

- ``Escape`` (default)

- ``CTRL + Q``

- ``None``: No shortcut active. Depending on your operating system a standard shortcut maybe
  available (e.g. ``ALT`` + ``F4`` on Windows).

.. note::

    Currently, this feature is not available in the Tkinter GUI!

.. _tt0x-usage-gui-config:

Configuration of the code editor
--------------------------------

You can open the ``View`` menu |tt0x-usage-label-8| which offers some possibilities
to configure the code editor:

.. figure:: ../images/textext-dialog-with-view-menus.png
    :alt: TexText view menu

- ``Word Wrap``: If this option is checked long lines are wrapped automatically to window width.

- ``Show line numbers``: If this option is checked line numbers are printed on the left hand side of the editor.

- ``Enabled auto indent``: If this option is checked current indentation is preserved when breaking a new line (this is not an intelligent code dependent indentation feature).

- ``Insert spaces instead of Tabs`` If this option is checked each time you press the ``Tab`` key a number of spaces as defined in ``Tabs Width`` is inserted instead of a tabulator character.

.. note::

   The last three options are only available if you have ``GTKSourceView`` installed
   together with ``PyGTK`` (see installation instructions :ref:`tt0x-linux-install`,
   :ref:`tt0x-windows-install`, :ref:`tt0x-macos-install`)


Further reading
---------------

See :ref:`tt0x-faq` and :ref:`tt0x-troubleshooting`
