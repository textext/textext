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
# Note that "bin" has to be added to that directory
INKSCAPE_REG_KEY = r"SOFTWARE\Inkscape\Inkscape"


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

    # Try standard registry and the 32bit as well as 64bit mapping of it
    for access_right in [_wr.KEY_READ, _wr.KEY_READ | _wr.KEY_WOW64_32KEY, _wr.KEY_READ | _wr.KEY_WOW64_64KEY]:
        # Global instalations put their keys in HKLM (HKEY_LOCAL_MACHINE), user installations
        # put their keys in HKCU (HKEY_CURRENT_USER)
        for hkey in [_wr.HKEY_LOCAL_MACHINE, _wr.HKEY_CURRENT_USER]:
            try:
                key = _wr.OpenKey(hkey, INKSCAPE_REG_KEY, 0, access_right)
                try:
                    # Inkscape stores its installation location in a Standard key -> ""
                    value, _ = _wr.QueryValueEx(key, "")
                    _wr.CloseKey(key)
                    dirname = _os.path.join(value, "bin")
                    return [dirname] if _os.path.isdir(dirname) else []
                except WindowsError:
                    _wr.CloseKey(key)
            except WindowsError:
                pass

    # Last chance: Guess at the two common locations
    for dirname in ["C:\\Program Files\\Inkscape\\bin", "C:\\Program Files (x86)\\Inkscape\\bin"]:
        if _os.path.isfile(_os.path.join(dirname, "inkscape.exe")):
            return [dirname]

    # Give up
    return []
