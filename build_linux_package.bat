@echo off
rem Batch Script for building Linux installation package on Windows.
rem
rem The script creates a directory "textext-[Version]-linux" with a
rem subdirectoy "extension". The extension files go into the extension
rem subdirectory while the license and the setup-script are placed into
rem the "textext-[Version]-linux" directory

rem Some variables
set TexTextVersion=0.8.1
set PackagePath=textext-%TexTextVersion%-linux
set ExtensionPath=%PackagePath%\extension
set PackageName=TexText-Linux-%TexTextVersion%

rem Delete old stuff and setup new directory structure
if exist %PackagePath% (
   echo Directory %PackagePath% already exists, content will be deleted!
   rmdir /S /Q %PackagePath%

   echo Creating new directory %PackagePath%
   mkdir %PackagePath%
)
echo Creating new directory %ExtensionPath%
mkdir %ExtensionPath%

rem Copy files
call :copy_func asktext.py %ExtensionPath%
call :copy_func default_packages.tex %ExtensionPath%
call :copy_func latexlogparser.py %ExtensionPath%
call :copy_func textext.inx %ExtensionPath%
call :copy_func textext.py %ExtensionPath%
call :copy_func typesetter.py %ExtensionPath%
call :copy_func win_app_paths.py %ExtensionPath%
call :copy_func setup.py %PackagePath%
call :copy_func LICENSE.txt %PackagePath%

rem If we have tar available on this machine build a tgz package
rem (Output is directed to nul, errors ("2") are directed to nul)
WHERE tar >nul 2>nul
IF %ERRORLEVEL% EQU 0 tar --verbose -czf %PackageName%.tgz %PackagePath%

rem If we have zip available on this machine build a zip package
WHERE zip >nul 2>nul
IF %ERRORLEVEL% EQU 0 zip -r %PackageName%.zip %PackagePath%

exit /B

rem Copy helper function
:copy_func
echo Copying file %1 into directory %2
copy %1 %2
exit /B
