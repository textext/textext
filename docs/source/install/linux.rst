.. |TexText| replace:: **TexText**
.. |Inkscape| replace:: **Inkscape 1.4**
.. |InkscapeOld| replace:: **Inkscape 0.92.x**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _linux-install:

==================
|TexText| on Linux
==================

.. contents:: :local:
   :depth: 1

For Ubuntu based systems with apt-get package manager
=====================================================

.. _linux-install-preparation:

Preparation
-----------

1. Make sure that |Inkscape| is installed on your system .
   (You can also use older Inkscape versions, see below)

   On **Ubuntu (24.04, 22.04, etc.)** and its derivates the most recent version of
   |Inkscape| is not part of the default distribution. Perform the following steps
   to install it:

   - Remove any old version of Inkscape

       .. code-block:: bash

            sudo apt remove inkscape

   - Add the Inkscape repository to your apt package manager:

       .. code-block:: bash

            sudo add-apt-repository ppa:inkscape.dev/stable
            sudo apt update

   - Install |Inkscape|

       .. code-block:: bash

            sudo apt install inkscape

   Check if it is able to launch. You can verify this by invoking :bash:`inkscape --version` from
   a terminal. It should output a version number greater or equal then 1.2.

   .. warning::
       |TexText| will not function if you installed |Inkscape| via **SNAP** or **FLATPACK**.
       The reason is that |Inkscape| will run in sandboxed mode in these environments and, hence,
       cannot access you LaTeX distribution to compile your snippets! This is a conceptional
       problem of snap/ flatpack, not of |TexText|.

2. Make sure that an operational LaTeX distribution and/ or typst is installed on your system. You can verify
   this by invoking at least one of :bash:`pdflatex --version`, :bash:`xelatex --version`,
   :bash:`typst --version` and :bash:`lualatex --version` in a terminal.

3. Optional: If you wish to have syntax highlighting and some other :ref:`nice features <usage-gui-config>`
   enabled in the |TexText|-Gui install GTKSourceView:

   .. code-block:: bash

        sudo apt install gir1.2-gtksource-3.0


.. _linux-install-textext:

Download and install |TexText|
------------------------------

1. Download the most recent package from the
   :textext_current_release_page:`release`
   (direct links: :textext_download_zip:`Linux`, :textext_download_tgz:`Linux`).
   In case you are using Inkscape 1.2, 1.1, or 1.0 download
   `TexText 1.8.2 <https://github.com/textext/textext/releases/tag/1.8.2>`_!

2. Extract the package and change into the created directory.

3. Run :bash:`setup.py` from your terminal:

   .. code-block:: bash

        python3 setup.py

   It will copy the required files into the user's Inkscape
   configuration directory (usually this is ``~/.config/inkscape/extensions``)

   Setup will inform you if some of the prerequisites needed by |TexText| are missing.
   Install them. If setup complains about missing GTK or Tkinter bindings please go to
   :ref:`linux-install-gui`.

   See :ref:`advanced-install` for further options provided by
   :bash:`setup.py`.

4. Due to a packaging error (as of Oct 25th 2024, see `this issue on GitLab <https://gitlab.com/inkscape/inkscape/-/issues/5070>`_)
   also install the following Python package:

   .. code-block:: bash

        sudo apt install python3-tinycss2

.. note::

    In case of installation problems refer to the :ref:`trouble_installation` in the :ref:`troubleshooting` section!

You are done. Now you can consult the :ref:`usage instructions <gui>`.



For ArchLinux based systems with pacman as package manager
==========================================================

1. Make sure that |Inkscape| is installed on your system. If not, install it:

   .. code-block:: bash

        sudo pacman -S inkscape

2. Due to a packaging error (as of Oct 25th 2024, see `this issue <https://gitlab.archlinux.org/archlinux/packaging/packages/inkscape/-/issues/6>`_)
   also install the following Python package:

   .. code-block:: bash

        sudo pacman -S python-tinycss2

3. Optional: If you wish to have syntax highlighting and some other :ref:`nice features <usage-gui-config>`
   enabled in the |TexText|-Gui install GTKSourceView:

   .. code-block:: bash

        sudo pacman -S gtksourceview3

4. Make sure you have a basic LaTeX system on your machine. At least the packages
   :bash:`texlive-latex`, :bash:`texlive-latexrecommended`, :bash:`texlive-latexextra`
   are required. If not, install them:

   .. code-block:: bash

        pacman -S texlive-latex texlive-latexrecommended texlive-latexextra

5. Download the most recent |TexText| package from the
   :textext_current_release_page:`release`
   (direct links: :textext_download_zip:`Linux`, :textext_download_tgz:`Linux`).

6. Extract the package and change into the created directory.

7. Run :bash:`setup.py` from your terminal:

   .. code-block:: bash

        python setup.py

   It will copy the required files into the user's Inkscape
   configuration directory (usually this is ``~/.config/inkscape/extensions``)

   Setup will inform you if some of the prerequisites needed by |TexText| are missing.
   Install them. If setup complains about missing GTK or Tkinter bindings please go to
   :ref:`linux-install-gui`.

   See :ref:`advanced-install` for further options provided by
   :bash:`setup.py`.

.. note::

    In case of installation problems refer to the :ref:`trouble_installation` in the :ref:`troubleshooting` section!

You are done. Now you can consult the :ref:`usage instructions <gui>`.


For systems using an AppImage of Inkscape
=========================================

Preparation
-----------

1. Download the AppImage from the Inkscape homepage

2. Make it executable

   .. code-block:: bash

        chmod +x Inkscape-dc2aeda-x86_64.AppImage

3. Test it:

   .. code-block:: bash

        ./Inkscape-dc2aeda-x86_64.AppImage

   (Replace Inkscape-dc2aeda-x86_64.AppImage by the correct file name.)

Download and install |TexText|
------------------------------

1. Download the most recent package from the
   :textext_current_release_page:`release`
   (direct links: :textext_download_zip:`Linux`, :textext_download_tgz:`Linux`)

2. Extract the package and change into the created directory.

3. Install TexText via the the command

   .. code-block:: bash

        python3 setup.py --skip-requirements-check --inkscape-executable /path/to/your/appimage/Inkscape-dc2aeda-x86_64.AppImage

   (Replace Inkscape-dc2aeda-x86_64.AppImage by the correct file name.)
   It will copy the required files into the user's Inkscape
   configuration directory (usually this is ``~/.config/inkscape/extensions``)

4. Install the GTK-GUI bindings as explained here: :ref:`linux-install-gui`

You are done. Now you can consult the :ref:`usage instructions <gui>`.

.. _linux-install-gui:

Manual installation of the GUI library bindings
===============================================

In the case that |Inkscape| has not been automatically installed together with the necessary
Python GUI bindings or if you are using an Inkscape AppImage you need to install them manually.
You have two options: ``GTK3`` (recommended) or ``Tkinter``.

.. _linux-install-gtk3:

Install Python GTK3 bindings (recommended)
------------------------------------------

You need to install the Python 3.x bindings for gobject-introspection libraries (``python3-gi``),
the GTK+ graphical user interface library (``gir1.2-gtk-3.0``) and the gir files for the GTK+
syntax highlighting widget (``gir1.2-gtksource-3.0``):

.. code-block:: bash

    sudo apt-get install python3-gi gir1.2-gtk-3.0 gir1.2-gtksource-3.0

.. _linux-install-tkinter:

Install Tkinter (not recommended)
---------------------------------

.. important::
    Tkinter support is deprecated and will be removed in future versions of |TexText|.
    If you really need this interface please leave a comment in `this issue on github <https://github.com/textext/textext/issues/209>`_.

Tkinter is functioning but has a limited interface compared to GTK version, so it's not
recommended. To use ``Tkinter`` install the  Python ``tk`` package.

.. code-block:: bash

    sudo apt-get install python3-tk
