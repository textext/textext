import os
import sys

sys.path.append(os.path.join("../../", "textext"))

import win_app_paths as wap

print("Installation directories of executables:")
print(wap.get_non_syspath_dirs())
