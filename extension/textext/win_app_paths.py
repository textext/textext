"""
:Author: Jan Winkler
:Date: 2017-12-13
:License: BSD

win_app_paths.py: Provides some crude functions trying to determine the paths to pstoedit,
imagemagick, and ghostscript. Furthermore a function is provided that safely checks if a command is
available on the system or not.

You can modify the lists _STR_KEYS_PSTOEDIT, _STR_KEYS_IMAGEMAGICK,
_STR_KEYS_GHOSTSCRIPT to search further path locations
"""
import os as _os
import subprocess as _sp
import _winreg as _wr

__all__ = ['get_last_error', 'get_pstoedit_dir', 'get_imagemagick_command',
           'get_ghostscript_dir', 'check_command', 'IS_IN_PATH']

# path to pstoedit is usually found under SOFTEWARE/wglunz/pstoedit in subkey InstallPath. Other
# key-subkey pairs to be checked for maybe added as list elements:
# STR_KEYS_PSTOEDIT = [['key1', 'subkey1'],['key2', 'subkey2'], ['key3', 'subkey3']]
_STR_KEYS_PSTOEDIT = [[r'SOFTWARE\wglunz\pstoedit', r'InstallPath']]

# path to ImageMagick is usually found under SOFTWARE/ImageMagick/Current in key LibPath. The 
# version of the lib is found under the key Version. Other
# key-subkey triples to be checked for maybe added as list elements:
# STR_KEYS_IMAGEMAGICK = [['key1', 'pathkey1', 'versionkey1'], ['key2', 'pathkey2', versionkey2]]
_STR_KEYS_IMAGEMAGICK = [[r'SOFTWARE\ImageMagick\Current', r'LibPath', r'Version']]

# path to ghostscript is usually found under SOFTWARE/Artifex/GPL Ghostscript/[VersionsNummer]/bin
# other keys to be checked for maybe added as list elements:
# STR_KEYS_GHOSTSCRIPT = ['key1', 'key2', 'key3']
_STR_KEYS_GHOSTSCRIPT = [r'SOFTWARE\Artifex\GPL Ghostscript']

# Since the Python interpreter in Inkscape is 32-bit for both, the 32- and 64-bit Version of
# Inkscape a standard call of OpenKey only refers to the WOW6432-tree of the registry. Hence, to
# check if the 64-bit version of a program is installed on 64-bit Windows we have to force to also
# look in the standard tree. This is done by adding the Flag KEY_WOW64_64KEY to the read access
# flag.
_REG_ACCESS_RIGHTS = [_wr.KEY_READ, _wr.KEY_READ | _wr.KEY_WOW64_64KEY]

_LAST_ERROR = ''

IS_IN_PATH = 1


def get_last_error():
    """
    Returns the last set error
    """
    return _LAST_ERROR


def _set_last_error(err_msg):
    """
    Sets _LAST_ERROR to err_msg so it can be retrieved by get_last_error()
    """
    global _LAST_ERROR
    _LAST_ERROR = err_msg


def get_pstoedit_dir():
    """
    Tries to determine the directory in which pstoedit is installed. If successful the path is
    returned. If pstoedit is found in the system path then the constant IS_IN_PATH is returned. If
    nothing is found the function returns None.

    The function searches the Windows registry under HKLM an HKCU for the keys defined in the list
    STR_KEYS_PSTOEDIT. If a key is found it looks for the path defined under the Subkey defined in
    STR_KEYS_PSTOEDIT. The elements of the list STR_KEYS_PSTOEDIT are lists each of them owns two
    elements: The first one is the key, the second one the subkey. If nothing is found in the
    registry it is checked if pstoedit can be found in the system path (which usually is not the
    case).
    """

    # At first check if we find the appropriate keys in HKLM or HKCU
    for access_right in _REG_ACCESS_RIGHTS:
        for hkey in [_wr.HKEY_LOCAL_MACHINE, _wr.HKEY_CURRENT_USER]:
            for str_key in _STR_KEYS_PSTOEDIT:
                try:
                    key = _wr.OpenKey(hkey, str_key[0], 0, access_right)
                    try:
                        value, _ = _wr.QueryValueEx(key, str_key[1])
                        _wr.CloseKey(key)
                        return value
                    except WindowsError:
                        _wr.CloseKey(key)
                except WindowsError:
                    pass

    # If nothing has been found in registry try to check if pstoedit is found
    # in the system path
    if check_command(['pstoedit', '--help']):
        return IS_IN_PATH
    else:
        _set_last_error('pstoedit seems not to be installed on the system '
                        '(neither found in path nor found under '
                        'the usual registry keys %s !' %
                        (' / '.join(['%s -> %s' % (val[0], val[1]) for val in _STR_KEYS_PSTOEDIT])))
        return None


def get_imagemagick_command():
    """
    Tries to determine the directory in which imagemagick is installed. If successful the path 
    including the raw command depending on the installed version is returned. If nothing is found 
    the function returns None.

    The function searches the Windows registry under HKLM an HKCU for the keys defined in the list
    STR_KEYS_IMAGEMAGICK. If a key is found it looks for the path defined under the Subkey defined
    in STR_KEYS_IMAGEMAGICK. The elements of the list STR_KEYS_IMAGEMAGICK are lists each of them
    owns three elements: The first one is the key, the second one the subkey specifying the library
    path and the third one is the key where the version should be found. If nothing is found in
    the registry it is checked if imagemagick can be found in the system path (which usually is not
    the case).
    """

    # 1. Try to find the required information in the registry
    for access_right in _REG_ACCESS_RIGHTS:
        for hkey in [_wr.HKEY_LOCAL_MACHINE, _wr.HKEY_CURRENT_USER]:
            for str_key in _STR_KEYS_IMAGEMAGICK:
                try:
                    key = _wr.OpenKey(hkey, str_key[0], 0, access_right)
                    try:
                        pathname, _ = _wr.QueryValueEx(key, str_key[1])
                        version, _ = _wr.QueryValueEx(key, str_key[2])
                        _wr.CloseKey(key)
                        if int(version[0]) >= 7.0:
                            return _os.path.join(pathname, 'magick')
                        else:
                            return _os.path.join(pathname, 'convert')
                    except WindowsError:
                        pass
                except WindowsError:
                    pass

    # 2. If nothing is found in the registry try to check if imagemagick is found in the system path
    if check_command(['convert', '--help']): # ImageMagick 6
        return "convert"
    elif check_command(['magick', '--help']): # ImageMagick 7
        return "magick"
    else:
        _set_last_error('imagemagick seems not to be installed on the system '
                        '(neither found in path nor found under '
                        'the usual registry keys %s !)' %
                        (' / '.join(['%s -> %s'
                                     % (val[0], val[1]) for val in _STR_KEYS_IMAGEMAGICK])))
        return None


def get_ghostscript_dir():
    """
    Tries to determine the directory in which ghostscript is installed. If successful the path is
    returned. If nothing is found the function returns None.

    The function searches the Windows registry under HKLM an HKCU for the keys defined in the list
    STR_KEYS_GHOSTSCRIPT. If a key is found it iterates over all available subkeys found under the
    key and checks if they contain the directory.
    """

    for access_right in _REG_ACCESS_RIGHTS:
        for hkey in [_wr.HKEY_LOCAL_MACHINE, _wr.HKEY_CURRENT_USER]:
            for str_key in _STR_KEYS_GHOSTSCRIPT:
                try:
                    key = _wr.OpenKey(hkey, str_key, 0, access_right)

                    # Ghostscript stores the information in a subkey the name
                    # of which is the installed version number. If several
                    # subkeys are found we iterate over them until we find a
                    # valid directory
                    num_subkeys = _wr.QueryInfoKey(key)[0]
                    for i in range(0, num_subkeys):
                        subkey_str = _wr.EnumKey(key, i)
                        subkey = _wr.OpenKeyEx(key, subkey_str)
                        dirname = _wr.QueryValue(subkey, None) + r'\bin'
                        _wr.CloseKey(subkey)
                        _wr.CloseKey(key)
                        if _os.path.isdir(dirname):
                            return dirname
                except WindowsError:
                    pass

    _set_last_error('Path to ghostscript not found (%s not found in registry!)'
                    % _STR_KEYS_GHOSTSCRIPT)
    return None


def check_command(cmd):
    """
    Checks if cmd can be executed without throwing FileNotFoundError. cmd is a list the first
    element is the name of the command and the subsequent elements contain a option to be passed
    (e.g.: ['my_prog', '--help']). If the command could be executed True is returned, otherwise
    False.
    """
    try:
        info = _sp.STARTUPINFO()
        info.dwFlags |= _sp.STARTF_USESHOWWINDOW
        info.wShowWindow = _sp.SW_HIDE

        proc = _sp.Popen(cmd, stdout=_sp.PIPE, stderr=_sp.PIPE, stdin=_sp.PIPE, startupinfo=info)
        out, err = proc.communicate()
        #print(out)
        #print(err)
        return True
    except WindowsError as excpt:
        _set_last_error('Execution of command \"%s\" failed: %s' % (' '.join(cmd), excpt))
        return False
