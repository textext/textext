
; Script generated by the HM NIS Edit Script Wizard.

; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "TexText for Inkscape"
!define /file PRODUCT_VERSION "extension\textext\VERSION"
!define PRODUCT_PUBLISHER "TexText developers"
!define PRODUCT_WEB_SITE "https://github.com/textext/textext"
!define PRODUCT_DOC_SITE "https://textext.github.io/textext"

; MUI 1.67 compatible ------
!include "MUI2.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"

; Welcome page
!define MUI_WELCOMEPAGE_TEXT "Setup will guide you through the installation of ${PRODUCT_NAME} \
${PRODUCT_VERSION}$\n$\nClick Next to continue."
!insertmacro MUI_PAGE_WELCOME

; License page
!define MUI_LICENSEPAGE_BUTTON "Next >"
!define MUI_LICENSEPAGE_TEXT_TOP "TexText is published under the modified BSD License \
(3-clause BSD License):"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "Click Next to continue!"
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

; Directory page
!define MUI_DIRECTORYPAGE_TEXT_TOP "${PRODUCT_NAME} ${PRODUCT_VERSION} will be installed into the \
Inkscape extension directory. Please change this directory only if you know what you are doing!"
!insertmacro MUI_PAGE_DIRECTORY

; Instfiles page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_TEXT_LARGE
!define MUI_FINISHPAGE_TEXT "${PRODUCT_NAME} ${PRODUCT_VERSION} has been installed on your computer. \
It is recommended to carefully read the documentation on ${PRODUCT_DOC_SITE} with instructions \
for additional software and a short TexText user guide.$\n$\nClick Finish to close Setup."
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Open documentation ${PRODUCT_DOC_SITE}"
!define MUI_FINISHPAGE_RUN_FUNCTION "ShowDoc"
!insertmacro MUI_PAGE_FINISH

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Function ShowDoc
  ExecShell "open" "${PRODUCT_DOC_SITE}"
FunctionEnd

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "TexText-Windows-${PRODUCT_VERSION}.exe"
InstallDir "$APPDATA\inkscape\extensions\"
ShowInstDetails show
RequestExecutionLevel user
  
Section -SETTINGS
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
SectionEnd

Section "TexText" -SEC01
  ; The extension files are installed in the subdir "textext" of the
  ; Inkscape extension directory $INSTDIR. Only the .inx file is put
  ; into the extension directory itself
  File "extension\textext.inx"

  SetOutPath "$INSTDIR\textext"
  File /x "*.pyc" /x "*.log" "extension\textext\*.*"
  SetOutPath "$INSTDIR\textext\icons"
  File /r "extension\textext\icons\*.png"
  
  ; Make sure that extension files from old TexText versions < 0.9
  ; are removed (they were put directly into Inkscape's extension
  ; directory and not in a subdirectory)
  ; Keep old default_packages.tex, i.e. move it to the new location
  IfFileExists "$INSTDIR\textext.py" OldExtensionFound InstallFinished
  
  OldExtensionFound:
  Delete $INSTDIR\textext\default_packages.tex
  Rename $INSTDIR\default_packages.tex $INSTDIR\textext\default_packages.tex
  Delete "$INSTDIR\textext.py"
  Delete "$INSTDIR\textext.pyc"
  Delete "$INSTDIR\asktext.py"
  Delete "$INSTDIR\asktext.pyc"
  Delete "$INSTDIR\typesetter.py"
  Delete "$INSTDIR\typesetter.pyc"
  Delete "$INSTDIR\latexlogparser.py"
  Delete "$INSTDIR\latexlogparser.pyc"
  Delete "$INSTDIR\win_app_paths.py"
  Delete "$INSTDIR\win_app_paths.pyc"
  
  InstallFinished:
SectionEnd
