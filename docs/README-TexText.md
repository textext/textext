# Tex Text - A LaTeX extension for Inkscape

## Features
- Typesetting of beautiful equations using LaTeX which are placed as SVG objects in your document.
- LaTeX equation objects can be edited later (in contrast to the built in LaTeX-tool).
- Free scaling and coloring of the objects possible.
- Usage of user defined preamble files (e.g., to include special packages, etc.).

## Prerequisites

- A LaTeX distribution (e.g., TeX Live [Linux, Windows, MaxOS] or MiKTeX [Windows only]) has to be installed, especially `pdflatex` is needed.
- You need the 32-bit or 64-bit version of Inkscape releases 0.92, 0.91 or 0.48
- Depending on your operating system some extra software is required, see the specific instructions below.
- **Important:** If you use Inkscape 0.92 please ensure that the python 2.7 interpreter has been selected during the installation of Inkscape (by default this is the case).


## Installation for Linux [(or for Windows...)](#installation-for-windows).

### Tex Text Extension

\footnotesize

- [TexText-Linux-0.7.1.tgz](https://github.com/textext/textext/releases/download/0.7.1/TexText-Linux-0.7.1.tgz)
- [TexText-Linux-0.7.1.zip](https://github.com/textext/textext/releases/download/0.7.1/TexText-Linux-0.7.1.zip)

To install *Tex Text*, simply download the package and extract it. A directory with the name `textext-0.7.1-linux` will be created. Change into the directory and run `python setup.py` in your terminal. All it does, is copying the necessary files to your Inkscape extension directory. If you don't trust this script, you'll have to copy all the files within the `extensions` directory of the extracted archive to `~/.config/inkscape/extensions/`.

### Additional required software

- You'll need to install GtkSourceView (`python-gtksourceview2` on Ubuntu/Debian) to take advantage of all the GUI features of *Tex Text*. This package should install `python-gtk2` as well, but if your distribution works differently, make sure you install the Python Gtk+ bindings.

- Next, please install `pstoedit`.

- Finally, to enable the preview feature of *Tex Text*, you need to install `ImageMagick`.

*(The extension also needs Ghostscript, but this should already be included with your LaTeX distribution.)*

### Congratulations, you're done! [Show Usage...](#usage)


## Installation for Windows

### Tex Text Extension

\footnotesize

- [TexText-Windows-0.7.1.exe](https://github.com/textext/textext/releases/download/0.7.1/TexText-Windows-0.7.1.exe)

The installation of *Tex Text for Inkscape* is straightforward: Simply use the installer and follow the instructions (basically, click *Next*, *Install* and *Done*, since you usually won't even have to change the installation directory). It will copy the required files into the user's Inkscape configuration directory (usually this is `%USERPROFILE%\AppData\Roaming\Inkscape`) and put a key into the Windows registry which is used to store configuration data of the extension.


## Additional required software

### PyGTK

After that, you have to install PyGTK. Depending on your Inkscape version you need to download one of the following installers **(please uninstall any previous version of PyGTK for Inkscape before)**:

 Inkscape Version (**important!**) | PyGTK Installer
-----------------------------------|-----------------------------------
 Inkscape 0.92.2 - 64-bit | [Install-PyGTK-2.24-Inkscape-0.92.2-64bit.exe](https://github.com/textext/textext/releases/download/0.7/Install-PyGTK-2.24-Inkscape-0.92.2-64bit.exe)
 Inkscape 0.92.2 - 32-bit | [Install-PyGTK-2.24-Inkscape-0.92.2-32bit.exe](https://github.com/textext/textext/releases/download/0.7/Install-PyGTK-2.24-Inkscape-0.92.2-32bit.exe)
 Inkscape 0.92.0 and 0.92.1 (64- and 32-bit)| [Install-PyGTK-2.24-Inkscape-0.92.exe](https://github.com/textext/textext/releases/download/0.7/Install-PyGTK-2.24-Inkscape-0.92.exe)
 Inkscape 0.91 and 0.48  (64- and 32-bit) | [Install-PyGTK-2.24-Inkscape-0.48+0.91.exe](https://github.com/textext/textext/releases/download/0.7/Install-PyGTK-2.24-Inkscape-0.48+0.91.exe)

The installer will search for your Inkscape installation and puts the required files into the directory of Inkscape. An uninstaller is installed by the installer, too.

If you do not trust the installer you can download one of the following zip archives and copy its content into the directory in which inkscape.exe resides (Inkscape version 0.92.2) or directly into the `python` directory of your Inkscape installation (Inkscape versions 0.48, 0.91, 0.92.0, 0.92.1):

 Inkscape Version | PyGTK zip-archive
------------------|-------------------------------------
Inkscape 0.92.2 - 64-bit | [PyGTK-2.24.2-Python-2.7-Inkscape-0.92.2-64bit.zip](https://github.com/textext/textext/releases/download/0.7/PyGTK-2.24.2-Python-2.7-Inkscape-0.92.2-64bit.zip)
Inkscape 0.92.2 - 32-bit | [PyGTK-2.24.2-Python-2.7-Inkscape-0.92.2-32bit.zip](https://github.com/textext/textext/releases/download/0.7/PyGTK-2.24.2-Python-2.7-Inkscape-0.92.2-32bit.zip)
Inkscape 0.92.0 and 0.92.1 | [PyGTK-2.24.2-Python-2.7-Inkscape-0.92.zip](https://github.com/textext/textext/releases/download/0.7/PyGTK-2.24.2-Python-2.7-Inkscape-0.92.zip)
Inkscape 0.91 and 0.48 | [PyGTK-2.24.2-Python-2.6-Inkscape-0.48+0.91.zip](https://github.com/textext/textext/releases/download/0.7/PyGTK-2.24.2-Python-2.6-Inkscape-0.48+0.91.zip) 




### Even more software that you might need to install

If you don't already have *Ghostscript*, *pstoedit* and *ImageMagick* installed on your machine, you'll have to install these as well. Depending on your machines architecture (32- or 64-bit) you find the corresponding packages under the following links:

- The installers for *pstoedit* are `pstoeditsetup-win32.exe` (32-bit) or `pstoeditsetup-x64.exe` (64-bit) which  can be found under [https://sourceforge.net/projects/pstoedit/files/pstoedit/3.70](https://sourceforge.net/projects/pstoedit/files/pstoedit/3.70)

- To install *ImageMagick*, run `ImageMagick-6.9.7-x-Q16-x86-static.exe` (32-bit) or `ImageMagick-6.9.7-x-Q16-x64-static.exe`(64-bit)  which can be downloaded from [ftp://ftp.imagemagick.org/pub/ImageMagick/binaries/](ftp://ftp.imagemagick.org/pub/ImageMagick/binaries/) (more recent versions have not been tested yet)

-  The installers for *Ghostscript* `gs920w32.exe` (32-bit) or `gs920w64.exe` (64-bit) can be downloaded from [32-bit]( https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs920/gs920w32.exe) and [64-bit](https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs920/gs920w64.exe
) **DO NOT install ghostscript 9.21 or 9.22!!**

**Note:** The 32-bit version of Inkscape is able to use the 64-bit versions of these programs and vice versa.


### Congratulations, you're done!

## Usage

The extension menu in Inkscape will now contain a new entry named *Tex Text*.

![Select the menu item *TexText* in order to open the window for editing your LaTeX-Code.](readme-images/inkscape-extension-winxp.png){ width=60% }

When you select it, a dialog will appear that lets you enter any LaTeX code you want (presumably your formula). It will highlight the syntax with colors, show you line numbers and more. Above the text field you can choose a scale factor between 0.1 and 10 in increments of 0.1. By hitting the Global button the scale factor of the node which has been edited before the current node is used. By pressing Reset the scale factor is reset to the value used when compiling the current node the last time. You can also choose a preamble file from your disk which shall be used for rendering your LaTeX code.

![The TexText editing dialog.](readme-images/textext-dialog-winxp.png){ width=75% }

Basically, your LaTeX code will be inserted into this environment:

```
\documentclass[preview]{standalone}
***preamble file content***
\pagestyle{empty}
\begin{document}
***Your code***
\end{document}
```

This will be typeset, converted to SVG and inserted into your Inkscape document.

Your LaTeX code and the accompanying settings (scale factor and optionally a preamble file) will be stored within the new SVG node in the document. This allows you to edit the LaTeX node later by selecting it and running the *Tex Text* extension (which will then show the dialog containing the saved values).

Any applied color or other styles will be kept when you update the LaTeX node using *Tex Text*.

There is a preview button as well, which shortens the feedback cycle from entry to result considerably, so use it! (It requires ImageMagick to be installed.)

## Known Issues

- Currently, colors set within the LaTeX code (`\textcolor{...}` in combination with an added `\usepackage{color}` in the preamble file) are irgnored.
- TexText fails to produce output if a ghostscript version later 9.20 is installed on your system. This is due to broken pstoedit support by ghostscript > 9.20 and cannot directly addressed by TexText.
- Under windows the Tkinter version of the GUI fails to open due to a bug in Inkscape. This will be fixed by the Inkscape team in Inkscape 0.92.3. Use the GTK interface instead.