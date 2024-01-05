"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Provides a class for managing the TexText settings. In fact
a convenience wrapper around a json dict.
"""
from dataclasses import dataclass
import json
import os
from utils.environment import Cmds, system_env


@dataclass(frozen=True)
class Align:
    HCENTER = "center"
    HLEFT = "left"
    HRIGHT = "right"
    VBOTTOM = "bottom"
    VMIDDLE = "middle"
    VTOP = "top"
    LABELS = [f"{VTOP} {HLEFT}", f"{VTOP} {HCENTER}", f"{VTOP} {HRIGHT}",
              f"{VMIDDLE} {HLEFT}", f"{VMIDDLE} {HCENTER}", f"{VMIDDLE} {HRIGHT}",
              f"{VBOTTOM} {HLEFT}", f"{VBOTTOM} {HCENTER}", f"{VBOTTOM} {HRIGHT}"]


@dataclass(frozen=True)
class GuiOptions:
    NEW_NODE_DISPLAY_MATH = "DisplayMath"
    NEW_NODE_EMPTY = "Empty"
    NEW_NODE_INLINE_MATH = "InlineMath"
    NEW_NODE_CONTENT = [NEW_NODE_EMPTY, NEW_NODE_INLINE_MATH, NEW_NODE_DISPLAY_MATH]

    CLOSE_CTRLQ = "CtrlQ"
    CLOSE_ESCAPE = "Escape"
    CLOSE_NONE = "None"
    CLOSE_SHORTCUT = [CLOSE_ESCAPE, CLOSE_CTRLQ, CLOSE_NONE]
    CLOSE_SHORTCUT_TEXT = ["_ESC", "CTRL + _Q", "None"]


@dataclass(frozen=True)
class Defaults:
    ALIGNMENT = Align.LABELS[5]
    FONTSIZE_PT = 10
    INKEX_VERSION = "0.0"
    INKSCAPE_VERSION = "0.0"
    JACOBIAN_SQRT = 1.0
    PREAMBLE = "packages.tex"
    SCALE = 1.0
    STROKE_TO_PATH = False
    TEXCMD = Cmds.PDFLATEX
    TEXTEXT_VERSION = "<=0.7"
    GUI_NEW_NODE_CONTENT = GuiOptions.NEW_NODE_EMPTY
    GUI_CLOSE_SHORTCUT = GuiOptions.CLOSE_CTRLQ


class SettingsError(OSError):
    pass


class SettingsBase:
    """
    Adds some convenient stuff around a dict which can saved to /loaded from
    a json file
    """

    def __init__(self, basename="config.json", directory=None, ignore_file_errors=False):
        """

        Args:
            basename (str): The file name the config is stored. Default: "config.json"
            directory (str): The directory in which the file is located. Set to None if
                             file should be stored in the current working directory
        """
        if directory is None:
            directory = os.getcwd()
        else:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        self._data = {}
        self.directory = directory
        self.data_path = os.path.join(directory, basename)
        try:
            self.load(ignore_file_errors)
        except SettingsError:
            raise

    def load(self, ignore_errors: bool = False):
        """
        Loads the content of the underlying dictionary from the json file
        specified during object construction. If the file does not exist
        the underlying dictionary is not changed.

        :param ignore_errors: If True any errors are ignored and the underlying
                              dictionary will be empty.
        :raises: SettingsError if an error occurs and ignore_errors = False
        """
        if os.path.isfile(self.data_path):
            try:
                with open(self.data_path, mode="r", encoding="utf-8") as f_handle:
                    self._data = json.load(f_handle)
            except (OSError, ValueError) as err:
                if not ignore_errors:
                    raise SettingsError(f"Bad config `{self.data_path}`: {str(err)}. "
                                        f"Please fix it and re-run.") from err
                self._data = {}

    def save(self, ignore_errors: bool = False):
        """
        Saves the content of the underlying dictionary to the json file
        specified during object construction

        :param ignore_errors: If True any errors are ignored and the underlying
                              dictionary will be empty.
        :raises: SettingsError if an error occurs and ignore_errors = False
        """
        try:
            with open(self.data_path, mode="w", encoding="utf-8") as f_handle:
                json.dump(self._data, f_handle, indent=2)
        except (OSError, ValueError) as err:
            if not ignore_errors:
                raise SettingsError(f"Bad config `{self.data_path}`: {str(err)}. "
                                    f"Please fix it and re-run.") from err

    def delete_file(self, ignore_errors: bool = False):
        """
        Deletes the json file specified during object construction

        :param ignore_errors: If True any errors are ignored and the underlying
                              dictionary will be empty.

        :raises: SettingsError if an error occurs and ignore_errors = False
        """
        if os.path.exists(self.data_path):
            try:
                os.remove(self.data_path)
            except OSError as err:
                if not ignore_errors:
                    raise SettingsError(f"Config `{self.data_path}` could not be deleted. "
                                        f"Error message: {str(err)}")


class SettingsTexText(SettingsBase):
    def __init__(self, basename="config.json", directory=None):
        """

        Args:
            basename (str): The file name the config is stored. Default: "config.json"
            directory (str): The directory in which the file is located. Set to None if
                             file should be stored in the current working directory
        """
        super().__init__(basename, directory, ignore_file_errors=False)

    def load(self, ignore_file_errors=False):
        super().load(ignore_file_errors)
        if "gui" not in self._data:
            self._data["gui"] = {}

    @property
    def preamble_file(self) -> str:
        return self._data.get("preamble", Defaults.PREAMBLE)

    @preamble_file.setter
    def preamble_file(self, preamble: str):
        self._data["preamble"] = preamble

    @property
    def scale_factor(self) -> float:
        return self._data.get("scale", Defaults.SCALE)

    @scale_factor.setter
    def scale_factor(self, value: float):
        self._data["scale"] = value

    @property
    def font_size_pt(self) -> float:
        return self._data.get("font_size", Defaults.FONTSIZE_PT)

    @font_size_pt.setter
    def font_size_pt(self, value: float):
        self._data["font_size"] = value

    @property
    def previous_command(self):
        return self._data.get("previous_tex_command", Defaults.TEXCMD)

    @previous_command.setter
    def previous_command(self, command: str):
        self._data["previous_tex_command"] = command

    @property
    def gui_auto_indent(self) -> bool:
        return self._data["gui"].get("auto_indent", False)

    @gui_auto_indent.setter
    def gui_auto_indent(self, value: bool):
        self._data["gui"]["auto_indent"] = value

    @property
    def gui_close_shortcut(self) -> str:
        return self._data["gui"].get("close_shortcut", GuiOptions.CLOSE_CTRLQ)

    @gui_close_shortcut.setter
    def gui_close_shortcut(self, value: str):
        self._data["gui"]["close_shortcut"] = value

    @property
    def gui_confirm_close(self) -> bool:
        return self._data["gui"].get("confirm_close", True)

    @gui_confirm_close.setter
    def gui_confirm_close(self, value: bool):
        self._data["gui"]["confirm_close"] = value

    @property
    def gui_font_size(self) -> int:
        return self._data["gui"].get("font_size", 11)

    @gui_font_size.setter
    def gui_font_size(self, value: int):
        self._data["gui"]["font_size"] = value

    @property
    def gui_insert_spaces(self) -> bool:
        return self._data["gui"].get("insert_spaces", False)

    @gui_insert_spaces.setter
    def gui_insert_spaces(self, value: bool):
        self._data["gui"]["insert_spaces"] = value

    @property
    def gui_new_node_content(self) -> str:
        return self._data["gui"].get("new_node_content", GuiOptions.NEW_NODE_EMPTY)

    @gui_new_node_content.setter
    def gui_new_node_content(self, value: str):
        self._data["gui"]["new_node_content"] = value

    @property
    def gui_preview_white_bg(self) -> bool:
        return self._data["gui"].get("white_preview_background", False)

    @gui_preview_white_bg.setter
    def gui_preview_white_bg(self, value: bool):
        self._data["gui"]["white_preview_background"] = value
        
    @property
    def gui_line_numbers(self) -> bool:
        return self._data["gui"].get("line_numbers", True)

    @gui_line_numbers.setter
    def gui_line_numbers(self, value: bool):
        self._data["gui"]["line_numbers"] = value

    @property
    def gui_tab_width(self) -> int:
        return self._data["gui"].get("tab_width", 4)

    @gui_tab_width.setter
    def gui_tab_width(self, value: int):
        self._data["gui"]["tab_width"] = value
        
    @property
    def gui_word_wrap(self) -> bool:
        return self._data["gui"].get("word_wrap", False)

    @gui_word_wrap.setter
    def gui_word_wrap(self, value: bool):
        self._data["gui"]["word_wrap"] = value

    def get_executable(self, command: str) -> str:
        return self._data.get(f"{command}-executable", system_env.executable_names[command])

    def set_executable(self, command: str, exe: str):
        self._data[f"{command}-executable"] = exe


class Cache(SettingsBase):
    """
    Basically a dictionary which can be saved to and loaded from disk but which silently
    discards any OS errors, hence, if something goes wrong during file saving any data
    will be lost after object destruction. If loading of file fails one ends up with an
    empty dictionary.
    """
    def __init__(self, basename=".cache.json", directory=None):
        super().__init__(basename, directory, ignore_file_errors=True)

    def get(self, key, default=None):
        result = self._data.get(key, default)
        if result is None:
            return default
        return result

    def has_key(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data.get(key)

    def __setitem__(self, key, value):
        if value is not None:
            self._data[key] = value
        else:
            self._data.pop(key, None)
