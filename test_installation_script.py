"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

This script creates fake executables (pdflatex, python2.7, etc...)
to test requirements check in setup.py

All fake executables are created in temporary directory and safely
deleted at the end.

setup.py is running with PATH set to temporary directory, so
actual environment does not affect this test
"""
import os
import shutil
import sys
import subprocess
import tempfile


class TempDirectory(object):
    def __init__(self):
        self.name = None

    def __enter__(self):
        self.name = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.name is not None:
            shutil.rmtree(self.name)


class FakeExecutablesMaker(object):
    def __init__(self, dirname):
        assert os.path.isdir(dirname)
        self.dirname = dirname

    def __call__(self, name, output="", channel='stdout'):
        assert channel in ["stdout", "stderr"]
        command_name = os.path.join(self.dirname, name)
        with open(command_name, "w") as fout:
            fout.write("#!%s\n" % sys.executable)
            fout.write("from __future__ import print_function\n")
            fout.write("import sys\n")
            fout.write("print(%s, file=sys.%s)" % (repr(output), channel))
        os.chmod(command_name, 0o755)


def test_configuration(fake_commands, expected_exit_code):
    with TempDirectory() as f:
        env = dict(os.environ, PATH=f.name)
        make_fake_executable = FakeExecutablesMaker(f.name)
        for args in fake_commands:
            make_fake_executable(*args)

        ret_code = subprocess.call([sys.executable,
                                    'setup.py',
                                    "--skip-extension-install"],
                                   env=env
                                   )
        assert ret_code == expected_exit_code, '%d != %d' % (ret_code, expected_exit_code)
        print("\033[92m  ====> Test %s successfully with expected exit code %d passed!\033[0m\n" % (
            fake_commands, expected_exit_code))


REQUIREMENT_CHECK_SUCCESS = 0
REQUIREMENT_CHECK_UNKNOWN = 64
REQUIREMENT_CHECK_ERROR = 65

good_configurations = []

# Definition of working combinations of Inkscape and LaTeX
for latex in [("pdflatex",), ("lualatex",), ("xelatex",)]:
    good_configurations.append([("inkscape", "Inkscape 1.3 (1:1.3+202307231459+0e150ed6c4)"), latex])

# Test: Installation of working combinations must succeed
for good_configuration in good_configurations:
    test_configuration(good_configuration, REQUIREMENT_CHECK_SUCCESS)

# Test: If one component of the working combinations is missing
# installation must fail
for good_configuration in good_configurations:
    for i in range(len(good_configuration)):
        # good configuration without one element is bad
        bad_configuration = good_configuration[:i] + good_configuration[i + 1:]
        print(bad_configuration)
        test_configuration(bad_configuration, REQUIREMENT_CHECK_ERROR)

# Test wrong Inkscape version and no pdflatex installed
test_configuration([
    ("inkscape", "Inkscape 0.92.3 (2405546, 2018-03-11)"),
], REQUIREMENT_CHECK_ERROR)

# Test wrong Inkscape version and pdflatex installed
test_configuration([
    ("inkscape", "Inkscape 0.92.3 (2405546, 2018-03-11)"),
    ("pdflatex",)
], REQUIREMENT_CHECK_ERROR)

# Test what's happening when no version information
# is returned by Inkscape
test_configuration([
    ("inkscape",),
    ("pdflatex",),
], REQUIREMENT_CHECK_UNKNOWN)

# Test: Nothing is installed -> Installation must fail
test_configuration([
], REQUIREMENT_CHECK_ERROR)
