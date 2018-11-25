"""
:Author: Jan Winkler
:Date: 2018-11-20
:License: BSD

win_app_paths.py: Provides a crude mechanism trying to determine the install dirs of inkscape, pdf2svg, pstoedit,
and ghostscript.
"""
import os as _os
import subprocess as _sp
import _winreg as _wr


IS_IN_PATH = 1


class WinCommandInfo(object):

    def __init__(self, cmd, key_list=None):
        """
        :param cmd: String holding the name of the executable
        :param key_list: A list holding the names of keys and subkeys to look for the path of the executable
                         in the registry. Two possibilities:
                         1. [[key1, subkey1], [key2, subkey2], ...] -> Iterate over the keys and query the
                            specified subkeys for their values
                         2. [[key1], [key2], ...] -> Iterate over the keys and returning the values of
                            ALL available subkeys of the key
        """
        self._cmd = cmd
        self._key_list = key_list

    def _get_reg_key_value_list(self):
        """
        Queries the Windows registry for the keys specified in _key_list. For the first occurence
        of a key the following happens: A 1-element list holding the value of the corresponding subkey
        is returned if such a subkey is specified in _key_list. Otherwise a list holding the values of all
        available subkeys of the key is returned if no subkey is specified in key_list.
        If the operation fails None is returned.
        """

        # Attention! Since the Python interpreter in Inkscape is 32-bit for both, the 32- and 64-bit Version of
        # Inkscape, a standard call of OpenKey from within Python only refers to the WOW6432-tree
        # of the registry. Hence, to check if the 64-bit version of a program is installed on a
        # 64-bit Windows we have to force to also look in the standard tree. This is done by adding
        # the Flag KEY_WOW64_64KEY to the read access flag.
        for access_right in [_wr.KEY_READ, _wr.KEY_READ | _wr.KEY_WOW64_64KEY]:
            # Global instalations put their keys in HKLM (HKEY_LOCAL_MACHINE), user installations
            # put their keys in HKCU (HKEY_CURRENT_USER)
            for hkey in [_wr.HKEY_LOCAL_MACHINE, _wr.HKEY_CURRENT_USER]:
                for str_key in self._key_list:
                    try:
                        key = _wr.OpenKey(hkey, str_key[0], 0, access_right)
                        if len(str_key) == 2:
                            # Subkey explicitely specified
                            value_list = [None]
                            try:
                                value_list[0], _ = _wr.QueryValueEx(key, str_key[1])
                                _wr.CloseKey(key)
                                return value_list
                            except WindowsError:
                                _wr.CloseKey(key)
                        else:
                            # Collect and return ALL subkeys
                            num_subkeys = _wr.QueryInfoKey(key)[0]
                            value_ist = [None]*num_subkeys
                            for i in range(0, num_subkeys):
                                subkey_str = _wr.EnumKey(key, i)
                                subkey = _wr.OpenKeyEx(key, subkey_str)
                                value_ist[i] = _wr.QueryValue(subkey, None)
                                _wr.CloseKey(subkey)
                                _wr.CloseKey(key)
                            return value_ist
                    except WindowsError:
                        pass
        return None

    def _reg_value_to_path(self, value_list):
        """
        In the default implentation it is assumed that the value contains the path. Overwrite this
        method to your needs it this is not the case.
        """
        for val in value_list:
            if _os.path.isdir(val):
                return val
        return None

    def _check_cmd_in_syspath(self):
        """
        Checks if cmd can be executed without throwing FileNotFoundError.
        If the command could be executed True is returned, otherwise False.
        """
        try:
            info = _sp.STARTUPINFO()
            info.dwFlags |= _sp.STARTF_USESHOWWINDOW
            info.wShowWindow = _sp.SW_HIDE

            proc = _sp.Popen([self._cmd, "--help"], stdout=_sp.PIPE, stderr=_sp.PIPE, stdin=_sp.PIPE, startupinfo=info)
            _, _ = proc.communicate()
            return True
        except WindowsError as excpt:
            return False

    def get_path(self):
        """
        Tries to determine the directory in which _cmd is installed. If successful the path is
        returned. If _cmd is found in the system path then the constant IS_IN_PATH is returned. If
        nothing is found the function returns None.
        """
        value_list = self._get_reg_key_value_list()
        if value_list:
            return self._reg_value_to_path(value_list)
        else:
            return IS_IN_PATH if self._check_cmd_in_syspath() else None


class WinCommandInfoExeName(WinCommandInfo):
    def __init__(self, cmd, key_list=None): super(WinCommandInfoExeName, self).__init__(cmd, key_list)

    def _reg_value_to_path(self, value_list):
        # Key value also contains exe name
        dirname = _os.path.dirname(value_list[0])
        return dirname if _os.path.isdir(dirname) else None


class InkscapeCommandInfo(WinCommandInfoExeName):
    def __init__(self): super(InkscapeCommandInfo, self).__init__("inkscape", [
        [r"Software\Microsoft\Windows\CurrentVersion\App Paths\inkscape.exe", ""]])


class Pdf2SvgCommandInfo(WinCommandInfoExeName):
    def __init__(self): super(Pdf2SvgCommandInfo, self).__init__("pdf2svg", [
        [r"Software\Microsoft\Windows\CurrentVersion\App Paths\pdf2svg.exe", ""],
        [r"Software\Microsoft\Windows\CurrentVersion\Uninstall\pdf2svg for windows", "InstallDir"],
        [r"Software\Microsoft\Windows\CurrentVersion\Uninstall\pdf2svg for windows 0.2.3", "InstallDir"]])


class PsToEditCommandInfo(WinCommandInfo):
    def __init__(self): super(PsToEditCommandInfo, self).__init__("pstoedit",
                                                                  [[r"SOFTWARE\wglunz\pstoedit", r"InstallPath"]])


class GhostScriptCommandInfo(WinCommandInfo):
    def __init__(self): super(GhostScriptCommandInfo, self).__init__("gs", [[r"SOFTWARE\Artifex\GPL Ghostscript"]])

    def _reg_value_to_path(self, value_list):
        # Take the most recent version of ghostscript
        for val in reversed(value_list):
            dirname = val + r"\bin"
            if _os.path.isdir(dirname):
                return dirname
        return None


def get_non_syspath_dirs():
    """Returns a list containing the directories of the applications which are not found in the system path"""
    additional_dirs = []
    for cls in [InkscapeCommandInfo, Pdf2SvgCommandInfo, PsToEditCommandInfo, GhostScriptCommandInfo]:
        dirname = cls().get_path()
        if dirname and dirname is not IS_IN_PATH:
            additional_dirs.append(dirname)
    return additional_dirs
