@echo off
rem setup_win.bat
rem Wrapper for setup.py on Windows systems using the Python installation
rem shipped with Inkscape
rem
rem ToDo:
rem -Pass command line args for setup.py
rem -Allow to pass inkscape dir directly
rem -Refer to different python location in Inkscape < 0.92.2

setlocal EnableExtensions
setlocal EnableDelayedExpansion
set "INKSCAPE_DIR="
set "INKSCAPE_CMD="

rem Inkscape installation path is usually found in
rem "Software\Microsoft\Windows\CurrentVersion\App Paths\inkscape.exe"
rem under HKLM or HKCU
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
        for %%S in ("!INKSCAPE_CMD!") do (
            set INKSCAPE_DIR=%%~dpS
        )
        goto INKSCAPE_FOUND
    )
)

rem Check if Inkscape is in the system path
rem ERRORLEVEL 9009 -> file not found
rem "C:\Program Files\Inkscape\inkscape" --version  >nul 2>nul
inkscape --version  >nul 2>nul
if not %ERRORLEVEL%==9009 (
    echo "Inkscape found in system path!"
    goto INKSCAPE_FOUND
)

rem ToDo: Allow passed path
goto FAILED

:INKSCAPE_FOUND
echo Inkscape installation directory: %INKSCAPE_DIR%
echo Trying to run %INKSCAPE_DIR%python setup.py ...
"%INKSCAPE_DIR%python" setup.py
goto FINAL

:FAILED
echo "Inkscape neither found in the registry nor on the system path! Cannot continue!"

:FINAL

