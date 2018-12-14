.. |TexText| replace:: **TexText**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _tips-and-tricks:

Tips and Tricks
---------------

This page presents a collection of hints which may be helpful in your daily work
with |TexText|.

.. contents:: :local:

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

.. figure:: images/texttext-fontsize-example.png
   :alt: Font size example

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


Using special characters like German Umlaute (äüö) etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to use special characters which are not understood by plain LaTeX
in your nodes you have two options:

1. Include the directive ``\usepackage[utf-8]{inputenc}`` in the preamble file,
   see :ref:`usage-preamble-file`.

2. Use ``xelatex`` or ``lualatex`` as TeX command, see :ref:`usage-tex-compilers`.