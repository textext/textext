.. |TexText| replace:: **TexText**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _faq:

Frequently Asked Questions (FAQ)
--------------------------------

.. contents:: :local:

.. _faq-font-size:

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

.. figure:: ../images/texttext-fontsize-example.png
   :alt: Font size example

.. _faq-font-custom-font:

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


.. _faq-utf8:

Using special characters like German Umlaute (äüö) etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to use special characters which are not understood by plain LaTeX
in your nodes you have two options:

1. Include the directive ``\usepackage[utf-8]{inputenc}`` in the preamble file,
   see :ref:`usage-preamble-file`.

2. Use ``xelatex`` or ``lualatex`` as TeX command, see :ref:`usage-tex-compilers`.


Extension not shown in the Inkscape Extension menu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the the |TexText| entry is not shown in the ``Extension`` menu of Inkscape proceed with
the following checks:

1. Make sure that the setup procedure completed successfully. Double check its final output.

2. Launch Inkscape, open the ``Edit`` menu, select ``Preferences``, then select ``System`` in
   the tree-view to the left and check the entry ``User exentsions`` in the right part of
   the window. Its entry MUST be

   - on Linux/ MacOS: ``/home/[your user name]/.config/inkscape/extensions``

   - on Windows: ``C:\Users\[Your user name]\AppData\Roaming\inkscape\extensions``
