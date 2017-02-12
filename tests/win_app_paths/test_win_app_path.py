import win_app_paths as wap

res = wap.check_command(['C:\\Program Files (x86)\\gs\\gs9.14\\bin\\gswin32c.exe', '--help'])
if res:
    print('GS OK')
else:
    print('GS not found!')
    print(wap.get_last_error())

res = wap.check_command(['C:\\Program Files (x86)\\pstoedit\\pstoedit.exe', '-v'])
if res:
    print('pstoedit OK')
else:
    print('pstoedit not found!')

res = wap.check_command(['pdflatex', '--help'])
if res:
    print('pdflatex OK')
else:
    print('pdflatex not found!')

res = wap.check_command(['c:\\Program Files (x86)\\ImageMagick-6.8.8-Q16\\convert.exe', '--version'])
if res:
    print('ImageMagick OK')
else:
    print('ImageMagick not found!')

dirname = wap.get_pstoedit_dir()
if not dir:
    print(wap.get_last_error())
else:
    print(dirname)

dirname = wap.get_imagemagick_dir()
if not dir:
    print(wap.get_last_error())
else:
    print(dirname)

dirname = wap.get_ghostscript_dir()
if not dir:
    print(wap.get_last_error())
else:
    print(dirname)
