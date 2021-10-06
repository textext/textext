.. |TexText| replace:: **TexText for Inkscape 1.x**
.. |Inkscape| replace:: **Inkscape 1.x**
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

.. _linux-install-preparation:

Preparation
===========

1. Make sure that |Inkscape| or later is installed on your system via your favorite
   package manager.

   On **Ubuntu 18.04** + **20.04** and its derivates |Inkscape| is not part of
   the default distribution. Perform the following steps to install it:

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
   a terminal. It should output a version number greater or equal then 1.0.

   .. important::
       |TexText| will not function if you installed |Inkscape| via **SNAP** or **FLATPACK**.
       The reason is that |Inkscape| will run in sandboxed mode in these environments and, hence,
       cannot access you LaTeX distribution to compile your snippets! This is a conceptional
       problem of snap/ flatpack, not of |TexText|.

2. Make sure that an operational LaTeX distribution is installed on your system. You can verify
   this by invoking at least one of :bash:`pdflatex --version`, :bash:`xelatex --version`, and
   :bash:`lualatex --version` in a terminal.

3. Optional: If you wish to have syntax highlighting and some other :ref:`nice features <usage-gui-config>`
   enabled in the |TexText|-Gui install GTKSourceView:

   .. code-block:: bash

        sudo apt install gir1.2-gtksource-3.0


.. _linux-install-textext:

Download and install |TexText|
==============================

.. important::

   Compared to previous versions |TexText| does not need any conversion utilities like
   ghostscript, pstoedit or pdfsvg.

1. If you are on Debian Bullseye or later refer to section :ref:`linux-textext-packages`.
   Otherwise download the most recent package from the
   :textext_current_release_page:`GitHub release page <release>`
   (direct links: :textext_download_zip:`.zip <Linux>`, :textext_download_tgz:`.tar.gz <Linux>`)

2. Extract the package and change into the created directory.

3. If you installed Inkscape via a package manager run :bash:`setup.py` from your terminal:

   .. code-block:: bash

        python3 setup.py

   or

   .. code-block:: bash

        python setup.py

   In both cases it will copy the required files into the user's Inkscape
   configuration directory (usually this is ``~/.config/inkscape/extensions``)

   Setup will inform you if some of the prerequisites needed by |TexText| are missing.
   Install them. If setup complains about missing GTK or Tkinter bindings please go to
   :ref:`linux-install-gui`.

   See :ref:`advanced-install` for further options provided by
   :bash:`setup.py`.

   .. note::

        If you use an Inkscape AppImage |TexText| should be installed as follows. However,
        due to an `Inkscape bug in AppImages <https://gitlab.com/inkscape/inkscape/-/issues/1306>`_
        all Python extensions are currently broken:

        .. code-block:: bash

            python setup.py --skip-requirements-check --inkscape-executable /home/path/to/your/appimage/Inkscape-4035a4f-x86_64.AppImage

.. note::

    In case of installation problems refer to the :ref:`trouble_installation` in the :ref:`troubleshooting` section!

You are done. Now you can consult the :ref:`usage instructions <gui>`.

.. _linux-install-gui:

Manually install the GUI library bindings
=========================================

In the case that |Inkscape| has not been automatically installed together with the necessary
Python GUI bindings you need to install them manually. You have two options: ``GTK3`` (recommended)
or ``Tkinter``.

At first you need to discover the Python interpreter that is used by your
Inkscape installation. Enter the following command in a terminal

.. code-block:: bash

        python --version

Keep the returned major version number (Python **2** or Python **3**) in mind
for the following instructions. If the command fails try :bash:`python3 --version`. The
major version is then **3** in the following steps.


.. _linux-install-gtk3:

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


.. _linux-install-tkinter:

Install Tkinter (not recommended)
---------------------------------

.. important::
    Tkinter support is deprecated and will be removed in future versions of |TexText|.
    If you really need this interface please leave a comment in `this issue on github <https://github.com/textext/textext/issues/209>`_.

Tkinter is functioning but has a limited interface compared to GTK version, so it's not
recommended. To use ``Tkinter`` install the  Python ``tk`` package.

If your Inkscape installation runs **Python 2**:

.. code-block:: bash

    sudo apt-get install python-tk


If your Inkscape installation runs **Python 3**:

.. code-block:: bash

    sudo apt-get install python3-tk


.. _linux-textext-packages:

Installation on Debian Bullseye and later
=========================================

TexText can be installed directly from the official repositories:

   .. code-block:: bash

        sudo apt install inkscape-textext

Then consult the :ref:`usage instructions <gui>`.
