import os
import pytest
import sys
import textext
import tempfile
import subprocess
import shutil
import json


class TempDirectory(object):
    def __init__(self):
        self.__name = None

    def __enter__(self):
        self.__name = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__name is not None:
            shutil.rmtree(self.__name)

    @property
    def name(self):
        return self.__name


def svg_to_png(svg, png, dpi=None, height=None, render_area="drawing"):
    assert os.path.isfile(svg)
    options = []
    if dpi:
        options.append("--export-dpi=%d" % dpi)
    if height:
        options.append("--export-height=%d" % height)
    if render_area == "drawing":
        options.append("--export-area-drawing")
    elif render_area == "document":
        pass
    else:
        raise RuntimeError("Unknwon export option `%s`" % render_area)

    subprocess.call([
                        "inkscape",
                        "--export-png=%s" % png
                    ] + options + [
                        svg
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    assert os.path.isfile(png)


def images_are_same(png1, png2, fuzz="0%"):
    """
    :param (str) png1: path to first image
    :param (str) png2: path to second image
    :param (str) fuzz: colors within this distance are considered equal
    :return (bool):
    """

    assert os.path.isfile(png1)
    assert os.path.isfile(png2)

    proc = subprocess.Popen([
        "compare",
        "-metric", "ae",
        "-fuzz", fuzz,
        png1,
        png2,
        os.devnull  # we don't want to generate diff image
    ])

    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        if stdout: sys.stdout.write(stdout)
        if stderr: sys.stderr.write(stderr)

    return proc.returncode == 0


def is_current_version_compatible(svg_original,
                                  svg_modified,
                                  json_config
                                  ):
    """
    :param (str) svg_original: path to snippet
    :param (str) svg_modified: path to empty svg created with same version of inkscape as `svg_snippet`
    :param (str) json_config: path to json config
    """

    assert os.path.isfile(svg_original)
    assert os.path.isfile(svg_modified)
    assert os.path.isfile(json_config)

    with TempDirectory() as tempdir:
        tmp_dir = tempdir.name

        png1 = os.path.join(tmp_dir, "1.png")
        png2 = os.path.join(tmp_dir, "2.png")

        config = json.load(open(json_config))
        check_render = config["check"]["render"]

        render_options = {}
        if check_render:
            if check_render["scale-is-preserved"]:
                assert "height" not in check_render
                render_options["dpi"] = check_render.get("dpi", 90)
            else:
                assert "dpi" not in check_render
                render_options["height"] = check_render.get("height", 100)

            render_options["render_area"] = check_render.get("render-area", "document")

        svg_to_png(svg_modified, png1, **render_options)

        # inherit all from original
        mod_args = config["original"]  # type: dict
        # overwrite with modified
        mod_args.update(config["modified"])

        if not "preamble-file" not in mod_args \
                or not mod_args["preamble-file"] \
                or not os.path.isfile(mod_args["preamble-file"]):
            mod_args["preamble-file"] = os.path.expanduser("~/.config/inkscape/extensions/textext/default_packages.tex")

        # run TexText
        tt = textext.TexText()
        tt.affect([
            r"--id=%s" % "content",  # todo: find a TexText node to avoid hard-coded ids
            r"--text=%s" % mod_args["text"],
            r"--scale-factor=%f" % mod_args["scale-factor"],
            r"--preamble-file=%s" % mod_args["preamble-file"],
            svg_original
        ], output=False)

        svg2 = os.path.join(tmp_dir, "svg2.svg")

        with open(svg2, "w") as f:
            tt.document.write(f)

        svg_to_png(svg2, png2, **render_options)

        fuzz = config["check"]["compare"].get("fuzz", "0%")
        test_case_description = config.get("description", "")
        assert images_are_same(png1, png2, fuzz=fuzz), test_case_description


def test_compatibility(root, inkscape, snippet):
    if inkscape.startswith("_"):
        pytest.skip("skip %s/%s (remove underscore to enable)" % (inkscape, snippet))
    if snippet.startswith("_"):
        pytest.skip("skip %s/%s (remove underscore to enable)" % (inkscape, snippet))

    is_current_version_compatible(
        svg_original=os.path.join(root, inkscape, snippet, "original.svg"),
        svg_modified=os.path.join(root, inkscape, snippet, "modified.svg"),
        json_config=os.path.join(root, inkscape, snippet, "config.json")
    )
