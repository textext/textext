@echo off
rem setup_win.bat
rem Wrapper for setup.py on Windows systems using the Python installation
rem shipped with Inkscape. You can pass all arguments to setup.py
rem using the syntax setup_win.bat /p:"arg list".


rem Enable "if defined" etc.
setlocal EnableExtensions

rem Allow access to modified variables in if and for constructs by
rem !VAR! (%VAR% would not result in modified value as one would expect...)
setlocal EnableDelayedExpansion

set "INKSCAPE_DIR="
set "INKSCAPE_EXE="
set "PYTHON_ARGS="
set "PATHON_EXE="
set "PYTHON_COMMAND="

rem Iterate over command line arguments (if there are any). If nothing useful
rem is found in the passed arguments fall through to usage info and quit.
rem (if /I -> case insensitive comparison, %%~B -> remove double quotes from %%B)
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
                        set INKSCAPE_EXE="%%~B\inkscape.exe"
                    )
                ) else (
                    echo The directory %%B does not exist!
                    goto FINAL
                )
            ) else (
                if /I "%%A"=="/p" (
                    set PYTHON_ARGS=%%~B
                ) else (
                    echo Illegal option passed or invalid syntax.
                    echo.
                    goto PRINT_USAGE
                )
            )
        )
    )
) else (
    goto DETECT_INKSCAPE_LOCATION
)

if defined INKSCAPE_DIR goto INKSCAPE_FOUND
if defined PYTHON_ARGS goto DETECT_INKSCAPE_LOCATION


:PRINT_USAGE
echo.
echo setup_win [/D:InkscapePath] [/P:SetupPara]
echo Tries to install the TexText extension using the Python distribution
echo shipped with Inkscape and the Python script setup.py. In fact this is
echo only a wrapper around setup.py which ensures that Python is correctly
echo identified in the Inkscape installation. If you have a system wide
echo Python installation you can directly call setup.py using that installation.
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
echo setup_win /d:"C:\Path\to\Inkscape installation\"
echo Installs TexText with the default options assuming that Inkscape is located
echo in the directory "C:\Path\to\Inkscape installation\". This syntax is only
echo required if you have not installed Inkscape via an installer but from a
echo zip package.
echo.
echo setup_win /p:"--option1 'value 1' --option2 'value 2'"
echo Installs TexText using the Python distribution shipped with
echo Inkscape and directly passes the parameter string
echo --option1 "value 1" --option2 "value 2" to setup.py. You can pass any
echo parameters understood by setup.py. Note the single quotes enclosing
echo white space containing option values in the _batch_ file call!!
echo.
echo You can combine the last two calling syntaxes, of course.
echo.
echo Example:
echo setup_win.bat /d:"C:\Program Files\Inkscape" /p:"--pdflatex-executable
echo 'C:\Program Files\MiKTeX 2.9\miktex\bin\x64\pdflatex.exe'
goto FINAL


:DETECT_INKSCAPE_LOCATION
echo Trying to find Inkscape...

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
        set INKSCAPE_EXE=%%B
    )
    if defined INKSCAPE_EXE (
        echo Inkscape found as !INKSCAPE_EXE!
        echo.
        for %%S in ("!INKSCAPE_EXE!") do set INKSCAPE_DIR=%%~dpS
        goto INKSCAPE_FOUND
    )
)

rem Check if Inkscape is in the system path (not very likely)
echo Trying system path...
for %%c in (inkscape.exe) do (
    set INKSCAPE_DIR=%%~dp$PATH:c
    set INKSCAPE_EXE=!INKSCAPE_DIR!\inkscape.exe
)
if defined INKSCAPE_DIR (
    echo Inkscape found in system path, installed in %INKSCAPE_DIR%
    echo.
    goto INKSCAPE_FOUND
)

rem Give up
goto INKSCAPE_NOT_FOUND


:INKSCAPE_FOUND
rem Replace quotes by double quotes in arguments for setup.py
if defined PYTHON_ARGS (
    set PYTHON_ARGS=%PYTHON_ARGS:'="%
)

rem We already know where Inkscape is, so setup.py does not need to detect it again
set PYTHON_ARGS=--inkscape-executable="%INKSCAPE_DIR%\inkscape.exe" %PYTHON_ARGS%

rem Check where the Python interpreter is in the Inkscape installation
rem Inskcape >= 0.92.2
echo Trying to detect Python interpreter in Inkscape installation directory...
if exist "%INKSCAPE_DIR%\python.exe" (
    echo Success!
    echo.
    set PYTHON_EXE="%INKSCAPE_DIR%\python.exe"
goto RUN_SETUP_PY
) else (
    rem Inkscape < 0.92.2
    echo Trying to detect Python interpreter in python directory of Inkscape installation...
    if exist "%INKSCAPE_DIR%\python\python.exe" (
        echo Success!
        echo.
        set PYTHON_EXE="%INKSCAPE_DIR%\python\python.exe"
        goto RUN_SETUP_PY
    ) else (
        goto PYTHON_NOT_FOUND
    )
)


:RUN_SETUP_PY
rem Command to be executed
set PYTHON_COMMAND=%PYTHON_EXE% setup.py %PYTHON_ARGS%
echo Trying to run %PYTHON_COMMAND%...
echo.
%PYTHON_COMMAND%
goto FINAL


:INKSCAPE_NOT_FOUND
echo Inkscape neither found in the registry nor on the system path!
echo Specifiy an explicit directory via the /d option to look for if
echo you installed Inkscape from a zip package. E.g.:
echo setup_win /D:"C:\Path\to\Inkscape installation\"
echo.
echo Cannot continue!
echo.
goto FINAL


:PYTHON_NOT_FOUND
echo No Python interpreter found within your Inkscape installation.
echo You have to install Inkscape with the Python option enabled
echo in the Inkscape installer.
echo.
goto FINAL


:FINAL
echo.
pause
