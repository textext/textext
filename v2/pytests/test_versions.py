from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
from typing import List, Tuple

UNSUPPORTED_INKSCAPE_VERSIONS = ["Inkscape 0.92.3 (2405546, 2018-03-11)",
                                 "Inkscape 1.2 (1dd7bebcbd, 2021-12-20)",
                                 "Inkscape 1.3.2 (1:1.3.2+202311252150+091e20ef0f)"]
MINIMUM_SUPPORTED_INKSCAPE_VERSION = "Inkscape 1.3 (1:1.3.2+202311252150+091e20ef0f)"
CURRENT_INKSCAPE_VERSION = "Inkscape 1.3 (1:1.3.2+202311252150+091e20ef0f)"
INKSCAPE_EXE_NAME = "inkscape"
PDFLATEX_EXE_NAME = "pdflatex"
XELATEX_EXE_NAME = "xelatex"
LUALATEX_EXE_NAME = "lualatex"
TYPST_EXE_NAME = "typst"

SETUP_DIR = os.path.abspath("..")

SETUP_CHECK_SUCCESS = 0


@contextmanager
def change_directory(new_dir: Path):
    old_dir = Path().absolute()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(old_dir)


def make_fake_executable(exe_name: str, output: str = "", channel: str = "stdout"):
    with open(exe_name, "w") as file:
        file.write(f"#!{sys.executable}\n")
        file.write(f"import sys\n")
        file.write(f"print('{output}', sys.{channel})\n")
    os.chmod(exe_name, mode=0o755)


def get_good_configs() -> List[List[Tuple[str, str]]]:
    good_configs = list()
    for inkscape_output in [MINIMUM_SUPPORTED_INKSCAPE_VERSION, CURRENT_INKSCAPE_VERSION]:
        good_configs.append([(INKSCAPE_EXE_NAME, inkscape_output),
                             (PDFLATEX_EXE_NAME, ""),
                             (XELATEX_EXE_NAME, ""),
                             (LUALATEX_EXE_NAME, ""),
                             (TYPST_EXE_NAME, "")])
    return good_configs


def test_versions(tmp_path, monkeypatch):
    with change_directory(tmp_path):
        monkeypatch.setenv("PATH", os.getcwd())
        good_configs = get_good_configs()
        for config in good_configs:
            for exe_name, exe_output in config:
                make_fake_executable(exe_name, exe_output)

            print(SETUP_DIR)
            ret_code = subprocess.call([sys.executable,
                                        f"{SETUP_DIR}/setup.py",
                                        "--skip-extension-install"])
            assert ret_code == SETUP_CHECK_SUCCESS, '%d != %d' % (ret_code, SETUP_CHECK_SUCCESS)
            print("\033[92m  ====> Test %s successfully with expected exit code %d passed!\033[0m\n" % (
                config, SETUP_CHECK_SUCCESS))
