; Installer / UnInstaller Script for PyGTK for Inkscape
; Use only for Inkscape 0.48 and 0.91

; Product name and version information
!define PRODUCT_NAME "PyGTK 2.24 for Inkscape"
!define PRODUCT_VERSION "0.48+0.91"
!define PRODUCT_REGKEY "${PRODUCT_NAME} ${PRODUCT_VERSION}"

; Names of the installer and uninstaller executables
!define INSTALLER_NAME "Install-PyGTK-2.24-Inkscape-${PRODUCT_VERSION}.exe" 
!define UNINSTALLER_NAME "UnInstall-PyGTK-2.24-Inkscape-${PRODUCT_VERSION}.exe" 
 
; Use modern user interface
!include "MUI2.nsh"

; MUI Settings
!define MUI_ABORTWARNING

; Welcome page (with detailed information what is going to be installed)
!define MUI_WELCOMEPAGE_TITLE "Welcome to the installation of ${PRODUCT_NAME} ${PRODUCT_VERSION}!"
!define MUI_TEXT_WELCOME_INFO_TEXT "${PRODUCT_NAME} ${PRODUCT_VERSION} will be installed into the \
python folder of your Inkscape installation. \
PyGTK as required by Inkscape-plugins contains of the following components:$\n$\n\
- PyCairo 1.8.10$\n\
- PyGObject 2.28.3$\n\
- PyGTK 2.24.0$\n\
- PyGtkSourceView2 2.10.1$\n\
- GTK+Runtime 2.24.8-1$\n$\n\
You can always uninstall all files of this intallation using the provided uninstaller which can be invoked via the well known Windows control panel.$\n$\n\
Now, Setup will guide you through the installation of PyGTK.$\n$\n"
!define MUI_PAGE_CUSTOMFUNCTION_SHOW MyWelcomeShowCallback
!insertmacro MUI_PAGE_WELCOME

; License page
!insertmacro MUI_PAGE_LICENSE "COPYING"

; Directory page
!define MUI_DIRECTORYPAGE_TEXT_TOP "If not already done automatically, please select the folder of your Inkscape installation, \
i.e. the folder that contains the binary inkscape.exe.$\n$\n\
${PRODUCT_NAME} ${PRODUCT_VERSION} will then be installed in the python subdirectory of your Inkscape installation.$\n$\n\
Installation proceeds only when you select a valid Inkscape installation directory!"
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Automatically detected Inkscape installation directory"
!define MUI_PAGE_CUSTOMFUNCTION_PRE DirPageInitFunc
!insertmacro MUI_PAGE_DIRECTORY

; Instfiles page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!insertmacro MUI_PAGE_FINISH

; Uninstaller welcome page
!insertmacro MUI_UNPAGE_WELCOME

; Uninstaller confirmation page
!insertmacro MUI_UNPAGE_CONFIRM

; Define what is going to be uninstalled
!insertmacro MUI_UNPAGE_INSTFILES

; Uninstaller finish page
!insertmacro MUI_UNPAGE_FINISH

; Language files
!insertmacro MUI_LANGUAGE "English"
; MUI end ------


; Set some variables

; Since we install into the progam files directory we need administrator privileges
RequestExecutionLevel admin

; The full name of the product
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"

; Define where the installer is built
OutFile "build\${INSTALLER_NAME}"

; For details
ShowInstDetails show


Function MyWelcomeShowCallback
SendMessage $mui.WelcomePage.Text ${WM_SETTEXT} 0 "STR:$(MUI_TEXT_WELCOME_INFO_TEXT)"
FunctionEnd

; In this function we try to find where Inkscape is installed. Since the Inkscape installer
; does not write anything useful into the windows registry we have to guess:
; At first we try to look in the 64-bit Program Files directory. If this fails we check
; the 32-bit Program Files directory. If this also fails a message is shown and the user
; has to select the correct directory manually later.
Function DirPageInitFunc
	IfFileExists $PROGRAMFILES64\Inkscape\inkscape.exe 0 check_32bit
	StrCpy $INSTDIR $PROGRAMFILES64\Inkscape
	goto func_end

	check_32bit:
	IfFileExists $PROGRAMFILES32\Inkscape\inkscape.exe 0 show_error
	StrCpy $INSTDIR $PROGRAMFILES32\Inkscape
	goto func_end

	show_error:
	StrCpy $INSTDIR ""
	MessageBox MB_OK|MB_ICONEXCLAMATION  "The installer was unable to detect the Inkscape installation directory automatically!\
	Hence, you have to select the proper directory manually in the next step!" IDOK func_end

	func_end:
FunctionEnd

; We check if the directory which has been selected by the user really contains inkscape.exe
; If not "Abort" is sent and the user cannot proceed the installation.
Function .onVerifyInstDir
	IfFileExists $INSTDIR\inkscape.exe path_ok 0
	Abort
	
	path_ok:
FunctionEnd

; A helper function which is used during uninstallation to check if a directory is empty
; and then delete it. The function receives the directory via the stack. If the
; directory is not empty, the directory will not be deleted.
; Based on http://nsis.sourceforge.net/Check_if_dir_is_empty
Function un.RemoveDirIfEmpty
  # Stack ->                    # Stack: <directory>
  Exch $0                       # Stack: $0
  Push $1                       # Stack: $1, $0
  Push $2						# Stack: $2, $1, $0
  StrCpy $2 $0
  FindFirst $0 $1 "$0\*.*"
  strcmp $1 "." 0 _notempty
    FindNext $0 $1
    strcmp $1 ".." 0 _notempty
      ClearErrors
      FindNext $0 $1
      IfErrors 0 _notempty
        FindClose $0
		RMDir $2
		Pop $2					# Stack: $1, $0
        Pop $1                  # Stack: $0
		Pop $0					# Stack is empty
        goto _end
     _notempty:
       FindClose $0
       ClearErrors
	   Pop $2					# Stack: $1, $0
       Pop $1                   # Stack: $0
	   Pop $0					# Stack is empty
  _end:
FunctionEnd


; Installer section
Section "Hauptgruppe" SEC_INSTALL 
	; Our stuff goes into the python subdirectory of the Inkscape installation directory
	SetOutPath $INSTDIR\python
	SetOverwrite ifnewer

	; The files we want to pack in the installer
	File /r "files\*"
	;File /r "testfiles\*"

	; Uninstaller is put into the Inkscape installation directory
	WriteUninstaller "$INSTDIR\${UNINSTALLER_NAME}"

	; Some Registry strings for proper uninstallation
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_REGKEY}" "DisplayName" "${PRODUCT_NAME} ${PRODUCT_VERSION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_REGKEY}" "DisplayVersion" "${PRODUCT_VERSION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_REGKEY}" "InstallLocation" "$INSTDIR"  
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_REGKEY}" "UninstallString" "$INSTDIR\${UNINSTALLER_NAME}"

	; Determine how many bytes we have installed (displayed later in the windows control panel)
	Push $0
	SectionGetSize ${SEC_INSTALL} $0
	IntFmt $0 "0x%08X" $0
	WriteRegDWORD  HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_REGKEY}" "EstimatedSize" "$0"
	Pop $0
SectionEnd


; Uninstaller Section
; $INSTDIR is the directory in which the uninstaller resides!
Section "Uninstall"
	; Delete all registry keys
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_REGKEY}"
	
	; Delete the installer
	Delete "$INSTDIR\${UNINSTALLER_NAME}"
	
	; Delete all installed files, remove PyGTK spcific directories also
	; and remove the include, pkgconfig, Scripts and share subdirectories
	; if they are empty (in the original Inkscape installation they are, but maybe
	; other things have been installed into them by the user so we have to be careful)
	; TODO: Create uninstall.log to simplify this process!
	RMDir /r "$INSTDIR\python\include\pycairo"
	RMDir /r "$INSTDIR\python\include\pygtk-2.0"
	Push "$INSTDIR\python\include\"
	Call un.RemoveDirIfEmpty
	
	Delete "$INSTDIR\python\Lib\pkgconfig\pycairo.pc"
	Delete "$INSTDIR\python\Lib\pkgconfig\pygobject-2.0.pc"
	Delete "$INSTDIR\python\Lib\pkgconfig\pygtk-2.0.pc"
	Delete "$INSTDIR\python\Lib\pkgconfig\pygtksourceview-2.0.pc"
	Push "$INSTDIR\python\Lib\pkgconfig\"
	Call un.RemoveDirIfEmpty
	
	RMDir /r "$INSTDIR\python\Lib\site-packages\cairo"
	RMDir /r "$INSTDIR\python\Lib\site-packages\gtk-2.0"
	Delete "$INSTDIR\python\Lib\site-packages\pycairo-1.8.10-py2.6.egg-info"
	Delete "$INSTDIR\python\Lib\site-packages\pygtk.pth"
	Delete "$INSTDIR\python\Lib\site-packages\pygtk.py"

	Delete "$INSTDIR\python\Scripts\pygobject-codegen-2.0"
	Delete "$INSTDIR\python\Scripts\pygobject_postinstall.py"
	Delete "$INSTDIR\python\Scripts\pygtk_postinstall.py"
	Delete "$INSTDIR\python\Scripts\pygtk_setup_config_files.py"
	Delete "$INSTDIR\python\Scripts\pygtksourceview_postinstall.py"
	Push "$INSTDIR\python\Scripts\"
	Call un.RemoveDirIfEmpty
	
	RMDir /r "$INSTDIR\python\share\gtk-doc"
	RMDir /r "$INSTDIR\python\share\pygobject"
	RMDir /r "$INSTDIR\python\share\pygtk"
	Push "$INSTDIR\python\share\"
	Call un.RemoveDirIfEmpty
SectionEnd