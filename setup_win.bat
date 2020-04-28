@echo off
rem setup_win.bat
rem Wrapper for TexText's setup.py on Windows systems using the Python 
rem installation shipped with Inkscape. You can use the same syntax
rem for setup_win.bat as for setup.py.
rem Example: setup_win.bat --inkscape-executable [exename]


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
set args=%*


if not defined args (
	rem If no arguments are passed try to detect inkscape location automatically
	goto DETECT_INKSCAPE_LOCATION
) else (
	rem Check valid argument syntax
	if not "!args:~0,2!"=="--" goto PRINT_USAGE
)


rem Iterate over command line arguments to detect manually given inkscape
rem location. It is required to call the Python interpreter. To do this 
rem we replace the -- keyword marker by ? so we can split the arguments
rem in keyword value groups using the delims feature of the for loop
rem (delims does not work with multiple characters. Since ? is not 
rem allowed in file names on Windows using ? as a subsitute should be safe)
rem Furthermore, we cannot split at whitespaces due to possible 
rem whitespaces in filenames
:PARSE_ARGS
if defined args (
	set args=%args:--=?%
	
	rem Split argument list into first "keyword value" pair (in %%A) and 
	rem remaining arguments in %%B
	for /f "usebackq tokens=1* delims=?" %%A in ('!args!') do (
		rem Split first pair into its two components %%C and %%D
		for /f "usebackq tokens=1* delims= " %%C in ('%%A') do (
			rem Check for explicitely given inkscape executable
			if /I "%%C"=="inkscape-executable" if not "%%D"=="" (
				set INKSCAPE_EXE=%%D
				if not exist "!INKSCAPE_EXE!" (
					echo !INKSCAPE_EXE! not found!
					goto FINAL
				) else (
					echo !INKSCAPE_EXE! found!
					for %%i in (!INKSCAPE_EXE!) do (
						set INKSCAPE_DIR=%%~dpi
					)
				)				
			) else (
				echo No value specified for key --%%C
				goto PRINT_USAGE
			)
			set PYTHON_ARGS=!PYTHON_ARGS!--%%A
		)
		rem Repeat operation with remaining argument list
		if /I not "%%B"=="" (
			set args=%%B
			goto PARSE_ARGS
		)
	)
)


if defined INKSCAPE_DIR goto INKSCAPE_FOUND
if defined PYTHON_ARGS goto DETECT_INKSCAPE_LOCATION


:PRINT_USAGE
echo.
echo setup_win
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
echo setup_win --inkscape-executable "C:\Path\to\Inkscape installation\inkscape.exe"
echo Installs TexText with the default options assuming that Inkscape is located
echo in the directory "C:\Path\to\Inkscape installation\". This syntax is only
echo required if you have not installed Inkscape via an installer but from a
echo zip package.
echo.
echo setup_win --option1 "value 1" --option2 "value 2"
echo Installs TexText using the Python distribution shipped with
echo Inkscape and directly passes the parameter string
echo --option1 "value 1" --option2 "value 2" to setup.py. You can pass any
echo parameters understood by setup.py. Call setup_win --help to list all available
echo options.
echo.
echo You can combine the last two calling syntaxes, of course.
echo.
echo Example:
echo setup_win.bat --inkscape-executable "C:\Program Files\Inkscape" 
echo --pdflatex-executable "C:\Program Files\MiKTeX 2.9\miktex\bin\x64\pdflatex.exe"
goto FINAL


:DETECT_INKSCAPE_LOCATION
echo Trying to find Inkscape...

rem Inkscape installation path is usually found in the registry
rem "SOFTWARE\Inkscape\Inkscape"
rem under HKLM (Local Machine -> machine wide installation) or
rem HKCU (Current User -> user installation)
rem We also have to keep in mind that the values might be in the 32bit or 64bit 
rem version of the registry (i.e., under SOFTWARE\WOW6432Node\Inkscape\Inkscape
rem or SOFTWARE\Inkscape\Inkscape)
for %%R in (HKLM HKCU) do (
	for %%T in (32 64) do (
		rem Output of REG QUERY "KeyName" /ve is (first line is a blank line):
		rem ----
		rem
		rem HKEY_LOCAL_MACHINE\SOFTWARE\Inkscape\Inkscape
		rem     (Standard)    REG_SZ    C:\Program Files\Inkscape
		rem ----
		rem so we skip the first two lines (skip=2) and then we take the second token
		rem and the reamining output (tokens=2*), so %%A is REG_SZ and %%B is the path
		rem even if it contains spaces (tokens are delimited by spaces)
		echo Trying registry root %%R [%%T]...
		for /f "usebackq skip=2 tokens=2*" %%A in (`REG QUERY "%%R\SOFTWARE\Inkscape\Inkscape" /ve /reg:%%T 2^>nul`) do (
			set INKSCAPE_DIR=%%B
		)
		if defined INKSCAPE_DIR (
			echo Inkscape considered to be installed in !INKSCAPE_DIR!
			set INKSCAPE_DIR=!INKSCAPE_DIR!\bin
			echo Setting executable path to !INKSCAPE_DIR!
			set INKSCAPE_EXE=!INKSCAPE_DIR!\inkscape.exe
			if exist "!INKSCAPE_EXE!" (
			    echo !INKSCAPE_EXE! found
				echo.
				goto INKSCAPE_FOUND
			) else (
				echo !INKSCAPE_EXE! not found
			)
			rem for %%S in ("!INKSCAPE_EXE!") do set INKSCAPE_DIR=%%~dpS
		)
	)
)

rem Check if Inkscape is in the system path (not very likely)
echo Trying system path...
for %%c in (inkscape.exe) do (
    set INKSCAPE_DIR=%%~dp$PATH:c
    set INKSCAPE_EXE=!INKSCAPE_DIR!inkscape.exe
)
if defined INKSCAPE_DIR (
    echo Inkscape found in system path, installed in %INKSCAPE_DIR%
    echo.
    goto INKSCAPE_FOUND
)

rem Give up
goto INKSCAPE_NOT_FOUND


:INKSCAPE_FOUND
rem Check where the Python interpreter is in the Inkscape installation
echo Trying to detect Python interpreter in Inkscape installation directory...
set PYTHON_EXE="%INKSCAPE_DIR%\python.exe"
if exist "%PYTHON_EXE%" (
    echo %PYTHON_EXE% found
    echo.
    
goto RUN_SETUP_PY
) else (
	goto PYTHON_NOT_FOUND
)


:RUN_SETUP_PY
rem The Python interpreter proccessing setup.py must be invoked directly from 
rem the directory in which it resides. Otherwise import test of gi 
rem retroinspection/ tkinter fails. It is not enough to call 
rem %PYTHON_EXE% setup.py or tweaking PYTHON_PATH.
rem Hence, we change into INKSCAPE_DIR (Attention! Maybe on another drive
rem as setup_win.bat!) and then call setup.py with its absolute path (%~dp0)
%INKSCAPE_DIR:~0,2%
cd %INKSCAPE_DIR%
set PYTHON_COMMAND=%PYTHON_EXE% %~dp0setup.py %PYTHON_ARGS%
echo Trying to run %PYTHON_COMMAND%...
echo.
%PYTHON_COMMAND%
goto FINAL


:INKSCAPE_NOT_FOUND
echo Inkscape neither found in the registry nor on the system path!
echo Specifiy an explicit directory via the --inkscape-executable option 
echo to look for if you installed Inkscape from a zip package. E.g.:
echo setup_win --inkscape-executable "C:\Path\to\Inkscape installation\"
echo.
echo Cannot continue!
echo.
goto FINAL


:PYTHON_NOT_FOUND
echo No Python interpreter found within your Inkscape installation.
echo Expected as %PYTHON_EXE%
echo You have to install Inkscape with the Python option enabled
echo in the Inkscape installer.
echo.
goto FINAL


:FINAL
echo.
pause
