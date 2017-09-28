# Tex Text 0.6.1 - A LaTeX extension for Inkscape (releases 0.92.1, 0.91 and 0.48)
 
![blank line](spacer.png)
 
> ##Very important - Inkscape 0.92.2
> On Windows TexText **does not** work in Inkscape 0.92.2. Please, use the 0.92.1 Inkscape release instead until a solution is found (See Issue #44)!

![blank line](spacer.png)

**Note:** There are more sophisticated instructions, including pictures in the docs directory of this repository:  [README-TexText.pdf](docs/README-TexText.pdf) or [README-TexText.html](docs/README.html)

## Features
- Typesetting of beautiful equations using LaTeX which are placed as SVG objects in your document.
- LaTeX equation objects can be edited later (in contrast to the built in LaTeX-tool).
- Free scaling and coloring of the objects possible.
- Usage of user defined preamble files (e.g., to include special packages, etc.).

## New in release 0.6.1 (2017-02-10)
- Fixed bug #18
- Introduced proposals #19 and #20
- Full compatibility with Inkscape 0.92
- Full compatibility with 64-bit installations of Inkscape under MS Windows
- See [CHANGELOG.txt](CHANGELOG.txt) for more information and history

## Prerequisites

- A LaTeX distribution (e.g., TeX Live [Linux, Windows, MaxOS] or MiKTeX [Windows only]) has to be installed, especially `pdflatex` is needed.
- You need the 32-bit or 64-bit version of Inkscape releases 0.92, 0.91 or 0.48
- Depending on your operating system some extra software is required, see the specific instructions below.
- **Important:** If you use Inkscape 0.92 please ensure that the python 2.7 interpreter has been selected during the installation of Inkscape (by default this is the case).


## Installation for Linux [(go to Windows instructions...)](#markdown-header-installation-for-windows).

### Tex Text Extension

 Download    | SHA-256 Checksum
-------------|-------------------
[TexText-Linux-0.6.1.tgz](https://bitbucket.org/pitgarbe/textext/downloads/TexText-Linux-0.6.1.tgz) | 0ed8be7442e80cc248a9c0eb524bc5f34a10fb990075e268cca4d7962eb3a34b
[TexText-Linux-0.6.1.zip](https://bitbucket.org/pitgarbe/textext/downloads/TexText-Linux-0.6.1.zip) | 8459b5a4dcacfd791685867a2499a7139d9afbfb085cbb6938765e51ef2296a3

To install *Tex Text*, simply download the package and extract it. A directory with the name `textext-0.6.1-linux` will be created. Change into the directory and run `python setup.py` in your terminal. All it does, is copying the necessary files to your Inkscape extension directory. If you don't trust this script, you'll have to copy all the files within the `extensions` directory of the extracted archive to `~/.config/inkscape/extensions/`.

### Additional required software

- You'll need to install GtkSourceView (`python-gtksourceview2` on Ubuntu/Debian) to take advantage of all the GUI features of *Tex Text*. This package should install `python-gtk2` as well, but if your distribution works differently, make sure you install the Python Gtk+ bindings.

- Next, please install `pstoedit`.

- Finally, to enable the preview feature of *Tex Text*, you need to install `ImageMagick`.

*(The extension also needs Ghostscript, but this should already be included with your LaTeX distribution.)*

### Congratulations, you're done! [Show Usage...](#markdown-header-usage)


## Installation for Windows

### Tex Text Extension

 Download   | SHA-256 Checksum
------------|-------------------
[TexText-Windows-0.6.1.exe](https://bitbucket.org/pitgarbe/textext/downloads/TexText-Windows-0.6.1.exe) | 2683b8f9b0bb4dfdf384e8fc6da8ce8e6e9354491c6bddf1ae03ba0c7261636b

The installation of *Tex Text for Inkscape* is straightforward: Simply use the installer and follow the instructions (basically, click *Next*, *Install* and *Done*, since you usually won't even have to change the installation directory). It will copy the required files into the user's Inkscape configuration directory (usually this is `%USERPROFILE%\AppData\Roaming\Inkscape`) and put a key into the Windows registry which is used to store configuration data of the extension.


## Additional required software

### PyGTK

After that, you have to install PyGTK. Depending on your Inkscape version you need to download one of the following installers:

 Inkscape Version | PyGTK Installer (SHA-256 Checksum)
------------------|-----------------------------------
Inkscape 0.91 and 0.48 | [Install-PyGTK-2.24-Inkscape-0.48+0.91.exe](https://bitbucket.org/pitgarbe/textext/downloads/Install-PyGTK-2.24-Inkscape-0.48+0.91.exe)
 | 1189df2eb90d1229b850bbba75def3b39306f303f9e34415d34eaf58cda6a05c
Inkscape 0.92 | [Install-PyGTK-2.24-Inkscape-0.92.exe](https://bitbucket.org/pitgarbe/textext/downloads/Install-PyGTK-2.24-Inkscape-0.92.exe)
 | a2ea5842084aa5f6fdc1880ae4ad135135f5ff0423bb0cd527a8f0cf95f7ffd6

The installer will search for your Inkscape installation and puts the required files into the `python` directory of Inkscape. An uninstaller is installed by the installer, too.

If you do not trust the installer you can download one of the following zip archives and copy its content into the `python` directory of your Inkscape installation:

 Inkscape Version | PyGTK zip-archive (SHA-256 Checksum)
------------------|-------------------------------------
Inkscape 0.91 and 0.48 | [PyGTK-2.24.2-Python-2.6-Inkscape-0.48+0.91.zip](https://bitbucket.org/pitgarbe/textext/downloads/PyGTK-2.24.2-Python-2.6-Inkscape-0.48+0.91.zip) 
 | 15f35a48d7b3558aadc9f8c7a2b9da8da0f66c8dfb88fb6c5e0230e58d64c080
Inkscape 0.92| [PyGTK-2.24.2-Python-2.7-Inkscape-0.92.zip](https://bitbucket.org/pitgarbe/textext/downloads/PyGTK-2.24.2-Python-2.7-Inkscape-0.92.zip)
 | ff3dac6e6a01dfad1b4bfe831e8d363a06500c2673e5e692a36e0fdee065e2e0



### Even more software that you might need to install

If you don't already have *Ghostscript*, *pstoedit* and *ImageMagick* installed on your machine, you'll have to install these as well. Depending on your machines architecture (32- or 64-bit) you find the corresponding packages under the following links:

- The installers for *pstoedit* are `pstoeditsetup-win32.exe` (32-bit) or `pstoeditsetup-x64.exe` (64-bit) which  can be found under [https://sourceforge.net/projects/pstoedit/files/pstoedit/3.70](https://sourceforge.net/projects/pstoedit/files/pstoedit/3.70)
- To install *ImageMagick*, run `ImageMagick-6.9.7-x-Q16-x86-static.exe` (32-bit) or `ImageMagick-6.9.7-x-Q16-x64-static.exe`(64-bit)  which can be downloaded from [ftp://ftp.imagemagick.org/pub/ImageMagick/binaries/](ftp://ftp.imagemagick.org/pub/ImageMagick/binaries/) (more recent versions have not been tested yet)
-  The installers for *Ghostscript* `gs910w32.exe` (32-bit) or `gs910w64.exe` (64-bit) can be downloaded from [https://ghostscript.com/download/gsdnld.html](https://ghostscript.com/download/gsdnld.html).

**Note:** The 32-bit version of Inkscape is able to use the 64-bit versions of these programs and vice versa.


### Congratulations, you're done!

## Usage

The extension menu in Inkscape will now contain a new entry named *Tex Text*.

When you select it, a dialog will appear that lets you enter any LaTeX code you want (presumably your formula). It will highlight the syntax with colors, show you line numbers and more. Above the text field you can choose a scale factor between 0.1 and 10 in increments of 0.1. You can also choose a preamble file from your disk which shall be used for rendering your LaTeX code.

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