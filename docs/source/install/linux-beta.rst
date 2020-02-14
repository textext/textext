.. |TexText| replace:: **TexText for Inkscape 1.0 beta**
.. |Inkscape| replace:: **Inkscape 1.0 beta**
.. |InkscapeOld| replace:: **Inkscape 0.92.x**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _linux-beta-install:

=================================
|TexText| on Linux (Ubuntu 18.04)
=================================

This guide explains how to install and use |TexText| together with |Inkscape| on a system
on which also |InkscapeOld| is installed. Unfortunately, this approach works only with
Ubuntu 18.04.

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

1. You can download |Inkscape| from https://inkscape.org/release/1.0beta2/ . Or
   execute

    .. code-block:: bash

        wget -c https://inkscape.org/gallery/item/16199/Inkscape-2b71d25-x86_64.AppImage

2. Change into the directory into which you downloaded the AppImage. Then, make it executable:

    .. code-block:: bash

        chmod u+x Inkscape-2b71d25-x86_64.AppImage

3. Extract the AppImage:

    .. code-block:: bash

        ./Inkscape-2b71d25-x86_64.AppImage --appimage-extract

4. Optional, if you are not in your home directory: Move the created directory ``squashfs-root``
   into your home directory:

    .. code-block:: bash

        mv squashfs-root ~

After this operation |Inkscape| will reside in ``~/squashfs-root/bin``. You can test it by
executing

.. code-block:: bash

    ~/squashfs-root/bin/inkscape &


Install GUI library
===================

Install the Python bindings for the graphical user interface of
|TexText|. You have two options: ``GTK3`` (recommended) or ``Tkinter``.

At first you need to discover the Python interpreter that is used by your
Inkscape installation. Enter the following command in a terminal

.. code-block:: bash

        python --version

Keep the returned major version number (Python **2** or Python **3**) in mind
for the following instructions:


.. _linux-beta-install-gtk3:

Install Python GTK3 bindings (recommended)
------------------------------------------

If your Inkscape installation runs **Python 2** you need the Python 2.x bindings for
gobject-introspection libraries (``python-gi``), the GTK+ graphical user interface library
(``gir1.2-gtk-3.0``) and the gir files for the GTK+ syntax highlighting widget
(``gir1.2-gtksource-3.0``)

.. code-block:: bash

    sudo apt-get install python-gi gir1.2-gtk-3.0 gir1.2-gtksource-3.0

If your Inkscape installation runs **Python 3** you need the Python 3 version of the
gobject-introspection. The rest remains the same:

.. code-block:: bash

    sudo apt-get install python3-gi gir1.2-gtk-3.0 gir1.2-gtksource-3.0


.. _linux-beta-install-tkinter:

Install Tkinter (not recommended)
---------------------------------

Tkinter is functioning but has a limited interface compared to GTK version, so it's not
recommended. To use ``Tkinter`` install the  Python ``tk`` package.

If your Inkscape installation runs **Python 2**:

.. code-block:: bash

    sudo apt-get install python-tk


If your Inkscape installation runs **Python 3**:

.. code-block:: bash

    sudo apt-get install python3-tk


Download and install |TexText|
==============================

1. Download the most recent **preview** package from :textext_current_release_page:`GitHub release page <release>`
2. Extract the package and change into the created directory.
3. Run :bash:`setup.py` with (**Important!!**) specification of the path to your |Inkscape| executable
   from your terminal:

    .. code-block:: bash

        python3 setup.py --inkscape-executable ~/squashfs-root/bin/inkscape

    Setup will inform you if some of the prerequisites needed by |TexText| are missing.
    Install them.

    .. important::

        Compared to previous versions of **TexText** for |InkscapeOld| |TexText| does
        not need any conversion utilities like ghostscript, pstoedit or pdfsvg.

Now you can launch |Inkscape| by typing :bash:`~/squashfs-root/bin/inkscape &` and work
with |TexText|

Please report any issues! Thank you!


Switching back to |InkscapeOld|
===============================

.. code-block:: bash

    mv ~/.config/inkscape/extensions ~/.config/inkscape/extensions.beta
    cp -r ~/.config/inkscape/extensions.backup/ ~/.config/inkscape/extensions
