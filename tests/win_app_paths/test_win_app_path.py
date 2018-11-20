import os
import sys

sys.path.append(os.path.join("../../", "extension", "textext"))

import win_app_paths as wap

for cls in [wap.InkscapeCommandInfo, wap.Pdf2SvgCommandInfo, wap.PsToEditCommandInfo, wap.GhostScriptCommandInfo]:
    obj = cls()
    dirname = obj.get_path()
    if not dirname:
        print("%s not found" % obj._cmd)
    else:
        if dirname == wap.IS_IN_PATH:
            print("%s is in path" % obj._cmd)
        else:
            print("%s found in %s" % (obj._cmd, dirname))

print("Dirs not in system path")
print(wap.get_non_syspath_dirs())
