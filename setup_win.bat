@echo off
rem setup_win.bat
rem Wrapper for setup.py on Windows systems using the Python installation
rem shipped with Inkscape. You can pass all arguments to setup.py
rem using the syntax setup_win.bat /p:"arg list".
rem
rem ToDo:
rem -Refer to different python location in Inkscape < 0.92.2

setlocal EnableExtensions
setlocal EnableDelayedExpansion
set "INKSCAPE_DIR="
set "INKSCAPE_CMD="
set "PYTHON_ARGS="

rem Iterate over command line arguments (if there are any). If nothing useful
rem is found in the passed arguments fall through to usage info and quit.
set args=%*
if defined args (
    for %%X in (%args%) do (
        for /f "usebackq delims=: tokens=1*" %%A in ('%%X') do (
            if "%%A"=="/d" (
                if /I "%%B"=="" (
                    echo No path specified
                    goto PRINT_USAGE
                )
                if exist "%%~B" (
                    if not exist "%%~B\inkscape.exe" (
                        echo inkscape.exe not found in directory %%B
                        goto FINAL
                    ) else (
                        echo inkscape.exe found in specified directory %%B
                        set INKSCAPE_DIR=%%~B
                    )
                ) else (
                    echo The directory %%B does not exist!
                    goto FINAL
                )
            ) else (
                if "%%A"=="/p" (
                    set PYTHON_ARGS=%%~B
                )
            )
        )
    )
) else (
    goto END_PARSE_ARGS
)

if defined INKSCAPE_DIR goto INKSCAPE_FOUND
if defined PYTHON_ARGS goto END_PARSE_ARGS

:PRINT_USAGE
echo.
echo setup_win [/D:InkscapePath] [/P:SetupPara]
echo Tries to install the TexText extension using the Python distribution
echo shipped with Inkscape and the Python script setup.py. In fact this is
echo only a wrapper around setup.py which ensures that Python is correctly
echo identified in the Inkscape installation. If you have a system wide
echo Python installation you can directly call setup.py using this installation.
echo.
echo Usage:
echo ======
echo setup_win
echo Installs TexText with the default options and using the Python installation
echo shipped with Inkscape. Installation fails if no Inkscape is detected by the
echo script or Inkscape has been installed without Python or the requirements to
echo use TexText are not met. In the last case the script lists the steps to
echo be done for an successfull installation.
echo.
echo setup_win /D:"C:\Path\to\Inkscape installation\"
echo Installs TexText with the default options assuming that Inkscape is located
echo in the directory "C:\Path\to\Inkscape installation\". This syntax is only
echo required if you have not installed Inkscape via an installer but from a
echo zip package.
echo.
echo setup_win /P:"--option1 --option2"
echo Installs TexText using the Python distribution shipped with
echo Inkscape and directly passes the parameter string "--option1 --option2"
echo to setup.py. You can pass any parameters understood by setup.py
echo.
echo You can combine the last two calling syntaxes, of course.
echo.
goto FINAL


:END_PARSE_ARGS

rem Inkscape installation path is usually found in the registry
rem "Software\Microsoft\Windows\CurrentVersion\App Paths\inkscape.exe"
rem under HKLM (Local Machine -> machine wide installation) or
rem HKCU (Current User -> user installation)
for %%R in (HKLM HKCU) do (
    rem Output of REG QUERY "KeyName" /ve is (first line is a blank line):
    rem ----
    rem
    rem HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\App Paths\inkscape.exe
    rem     (Standard)    REG_SZ    C:\Program Files\Inkscape\inkscape.exe
    rem ----
    rem so we skip the first two lines (skip=2) and then we take the second token
    rem and the reamining output (tokens=2*), so %%A is REG_SZ and %%B is the path
    rem even if it contains spaces (tokens are delimited by spaces)
    echo Trying registry root %%R...
    for /f "usebackq skip=2 tokens=2*" %%A in (`REG QUERY "%%R\Software\Microsoft\Windows\CurrentVersion\App Paths\inkscape.exe" /ve 2^>nul`) do (
        set INKSCAPE_CMD=%%B
    )
    if defined INKSCAPE_CMD (
        echo Inkscape found as !INKSCAPE_CMD!
        for %%S in ("!INKSCAPE_CMD!") do set INKSCAPE_DIR=%%~dpS
        goto INKSCAPE_FOUND
    )
)

rem Check if Inkscape is in the system path (not very likely)
for %%c in (inkscape.exe) do set INKSCAPE_DIR=%%~dp$PATH:c
if defined INKSCAPE_DIR (
    echo Inkscape found in system path, installed in %INKSCAPE_DIR%
    goto INKSCAPE_FOUND
)

goto FAILED

:INKSCAPE_FOUND
set PYTHON_COMMAND="%INKSCAPE_DIR%\python" setup.py %PYTHON_ARGS%
echo Trying to run %PYTHON_COMMAND%...
%PYTHON_COMMAND%
goto FINAL

:FAILED
echo Inkscape neither found in the registry nor on the system path! Cannot continue!

:FINAL

