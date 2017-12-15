Instructions how to build the PyGTK-Installer for Inkscape >= 0.92.2

All this suff really needs to be scripted!!

1. Create a directory with the name "files"

2. Create a directory with the name "build"

3. Populate the directory "files" with the content of the MINGW-directories of the following 
   archives from http://repo.msys2.org/mingw/x86_64/ (for 64-bit installation):
      
	mingw-w64-x86_64-glib2-2.54.2-1-any.pkg.tar	
	mingw-w64-x86_64-gtksourceview2-2.10.5-3-any.pkg.tar
	mingw-w64-x86_64-python2-cairo-1.15.3-1-any.pkg.tar
	mingw-w64-x86_64-python2-gobject2-2.28.6-6-any.pkg.tar
	mingw-w64-x86_64-python2-pygtk-2.24.0-6-any.pkg.tar
	mingw-w64-x86_64-pygtksourceview2
	
   and with the content of the MINGW-directories of the following 
   archives from http://repo.msys2.org/mingw/i686/ (for 32-bit installation):
	mingw-w64-i686-glib2-2.54.2-1-any.pkg.tar
	mingw-w64-i686-gtksourceview2-2.10.5-3-any.pkg.tar
	mingw-w64-i686-python2-cairo-1.15.3-1-any.pkg.tar
	mingw-w64-i686-python2-gobject2-2.28.6-6-any.pkg.tar
	mingw-w64-i686-python2-pygtk-2.24.0-6-any.pkg.tar
    mingw-w64-i686-pygtksourceview2
	
   After this operation the files directory should contain the directories mingw32 and mingw64 
   each of them containing four subdirectories: bin, inlcude, Lib, share

   If one or more of these packages are missing in the above link build them on your own using
   MINGW (you will have to do this at least with pygtksourceview). 
   Repository: https://github.com/Alexpux/MINGW-packages
   Infos about installation of MinGW/MSYS: http://www.msys2.org/
   
4. Move the content of the bin directory of mingw32/mingw64 one level above and remove the empty 
   bin directory. The mingw32/ mingw64 directories should now contain the subdirs include, Lib, and 
   share and the content of the former bin directory.
   
5. Build the file installation list using the Python script create_installer_file_lists.py
   In the script adapt the directory to use either files/mingw32 or files/mingw64 

6. Compile the installer script installer_pygtk_inkscape_0.9x using 
   nullsoft scriptable install system 3.01 (adapt the architecture flag in the script -> 32 or 64)

7. You will find the package in the build directory.