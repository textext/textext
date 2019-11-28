.. |TexText| replace:: **TexText for Inkscape 1.0 beta**
.. |Inkscape| replace:: **Inkscape 1.0 beta**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _linux-beta-install:

==================
|TexText| on Linux
==================

This guide explains how to install and use |TexText| together with |Inkscape| on a system
on which also Inkscape 0.94.x is installed.

Preparation
===========

1. Backup your existing Inkscape extension directory

    .. code-block:: bash

        cp -r ~/.config/inkscape/extensions ~/.config/inkscape/extensions.backup

2. Remove the old TexText installation:

    .. code-block:: bash

        rm -rf ~/.config/inkscape/extensions/textext
        rm ~/.config/inkscape/extensions/textext.inx


Download and install the |Inkscape| app image file
==================================================

1. You can download |Inkscape| from https://inkscape.org/release/inkscape-1.0beta1/. Or
   execute

    .. code-block:: bash

        wget -c https://inkscape.org/gallery/item/14918/Inkscape-fe3e306-x86_64.AppImage

2. Change into the directory into which you downloaded the AppImage. Then, make it executable:

    .. code-block:: bash

        chmod u+x Inkscape-fe3e306-x86_64.AppImage

3. Extract the AppImage:

    .. code-block:: bash

        ./Inkscape-fe3e306-x86_64.AppImage --appimage-extract

4. Optional, if you are not in your home directory: Move the created directory ``squashfs-root``
   into your home directory:

    .. code-block:: bash

        mv squashfs-root ~

After this operation |Inkscape| will reside in ``~/squashfs-root/bin``. You can test it by
executing

.. code-block:: bash

    ~/squashfs-root/bin/inkscape &


Download and install |TexText|
==============================

1. Download the most recent **preview** package from https://github.com/textext/textext/releases
2. Extract the package and change into the created directory.
3. Run :bash:`setup.py` with (**Important!!**) specification of the path to your |Inkscape| executable
   from your terminal:

    .. code-block:: bash

        python3 setup.py --inkscape-executable ~/squashfs-root/bin/inkscape

    Setup will inform you if some of the prerequisites needed by |TexText| are missing.
    Install them.

    .. important::

        Compared to previous versions of **TexText** for Inkscape 0.94.x |TexText| does
        not need any conversion utilities like ghostscript, pstoedit or pdfsvg.

Now you can launch |Inkscape| by typing :bash:`~/squashfs-root/bin/inkscape &` and work
with |TexText|

Please report any issues! Thank you!


Switching back to Inkscape 0.94.x
=================================

.. code-block:: bash

    mv ~/.config/inkscape/extensions ~/.config/inkscape/extensions.beta
    cp -r ~/.config/inkscape/extensions.backup/ ~/.config/inkscape/extensions
