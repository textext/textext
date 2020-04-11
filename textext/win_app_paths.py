"""
:Author: Jan Winkler
:Date: 2019-12-02
:License: BSD

win_app_paths.py: Provides a crude mechanism trying to determine the install dir of inkscape
"""
import os as _os
import subprocess as _sp
import winreg as _wr

# Windows Registry key under which the installation dir of Inkscape is stored
INKSCAPE_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\App Paths\inkscape.exe"


def check_cmd_in_syspath(command_name):
    """
    Checks if command_name can be executed without throwing FileNotFoundError.
    If the command could be executed True is returned, otherwise False.

    (Currently not used, but might be useful in the future...)
    """
    try:
        info = _sp.STARTUPINFO()
        info.dwFlags |= _sp.STARTF_USESHOWWINDOW
        info.wShowWindow = _sp.SW_HIDE

        proc = _sp.Popen([command_name, "--help"], stdout=_sp.PIPE, stderr=_sp.PIPE, stdin=_sp.PIPE, startupinfo=info)
        _, _ = proc.communicate()
        return True
    except WindowsError as excpt:
        return False


def get_non_syspath_dirs():
    """Returns a list containing the directories of the applications which are not found in the system path"""
    additional_dirs = []

    # Attention! Since the Python interpreter in Inkscape might be 32-bit for both, the 32- and 64-bit Version of
    # Inkscape, a standard call of OpenKey from within Python only refers to the WOW6432-tree
    # of the registry. Hence, to check if the 64-bit version of a program is installed on a
    # 64-bit Windows we have to force to also look in the standard tree. This is done by adding
    # the Flag KEY_WOW64_64KEY to the read access flag.
    for access_right in [_wr.KEY_READ, _wr.KEY_READ | _wr.KEY_WOW64_64KEY]:
        # Global instalations put their keys in HKLM (HKEY_LOCAL_MACHINE), user installations
        # put their keys in HKCU (HKEY_CURRENT_USER)
        for hkey in [_wr.HKEY_LOCAL_MACHINE, _wr.HKEY_CURRENT_USER]:
            try:
                key = _wr.OpenKey(hkey, INKSCAPE_REG_KEY, 0, access_right)
                try:
                    # Inkscape stores its installation location in a Standard key -> ""
                    value, _ = _wr.QueryValueEx(key, "")
                    _wr.CloseKey(key)
                    # Remove exe name
                    dirname = _os.path.dirname(value)
                    return [dirname] if _os.path.isdir(dirname) else []
                except WindowsError:
                    _wr.CloseKey(key)
            except WindowsError:
                pass
    return []
