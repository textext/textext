"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

This is the GUI part of TexText, handling several more or less
sophisticated dialog windows depending on the installed tools.

It is used uniformly from base.py via the ask method of the
TexTextGuiBase class depending on the available GUI framework
(TkInter or GTK3).
"""
import os
import sys
import warnings
from abc import ABCMeta, abstractmethod
from contextlib import redirect_stderr
from .base import TexTextEleMetaData
from .errors import TexTextCommandFailed
from .settings import Settings  # (we need it for typing!) # pylint: disable=unused-import


GTKSOURCEVIEW = "GTK Source View"
GTK = "GTK"
TK = "TK"

TOOLKIT = None


# Try GTK first
#   If successful, try GTKSourceView (bonus points!)
#   If unsuccessful, try TKinter
#   When not even TK could be imported, abort with error message
try:
    import gi
    gi.require_version("Gtk", "3.0")

    # The import statement
    # from gi.repository import Gtk
    # writes a warning into stderr under Python 3.10 which always pops up after the
    # extensions has been executed:
    # "DynamicImporter.exec_module() not found; falling back to load_module()"
    # We redirect stderr here into a string, check if
    # this warning has been writen and silently discard it. If something else has
    # been written to stderr we pass it to stderr.
    # Related issues:
    # https://gitlab.com/inkscape/extensions/-/issues/463
    # ToDo: Remove the stuff around the import statement when this has been fixed in
    #       updated Python 3.10 releases or is properly handled by Inkscape
    # ======
    import io

    with redirect_stderr(io.StringIO()) as h:
        from gi.repository import Gtk  # noqa

    # Sort out messages matching the ImportWarning, keep all others and send them to stderr
    for msg in (val for val in h.getvalue().splitlines(keepends=True)
                if val and val.find("ImportWarning: DynamicImporter") == -1):
        sys.stderr.write(msg)
    # ======

    from gi.repository import Gdk, GdkPixbuf  # noqa

    try:

        gi.require_version('GtkSource', '3.0')
        from gi.repository import GtkSource  # noqa

        TOOLKIT = GTKSOURCEVIEW
    except (ImportError, TypeError, ValueError) as _:
        TOOLKIT = GTK

except (ImportError, TypeError, ValueError) as _:
    try:
        import tkinter as tk
        from tkinter import messagebox as tk_msg_boxes
        from tkinter import filedialog as tk_file_dialogs
        TOOLKIT = TK

    except ImportError:
        raise RuntimeError("\nNeither GTK nor TKinter is available!\nMake sure that at least one of these "
                           "bindings for the graphical user interface of TexText is installed! Refer to the "
                           "installation instructions on https://textext.github.io/textext/ !")


class TexTextGuiBase:
    __metaclass__ = ABCMeta

    ALIGNMENT_LABELS = ["top left", "top center", "top right",
                        "middle left", "middle center", "middle right",
                        "bottom left", "bottom center", "bottom right"]
    DEFAULT_WORDWRAP = False
    DEFAULT_SHOWLINENUMBERS = True
    DEFAULT_AUTOINDENT = True
    DEFAULT_INSERTSPACES = True
    DEFAULT_TABWIDTH = 4
    DEFAULT_FONTSIZE = 11
    DEFAULT_NEW_NODE_CONTENT = "Empty"
    DEFAULT_CLOSE_SHORTCUT = "Escape"
    DEFAULT_CONFIRM_CLOSE = True
    DEFAULT_PREVIEW_WHITE_BACKGROUND = False
    FONT_SIZE = [11, 12, 14, 16]
    NEW_NODE_CONTENT = ["Empty", "InlineMath", "DisplayMath"]
    CLOSE_SHORTCUT = ["Escape", "CtrlQ", "None"]
    TEX_COMMANDS = ["pdflatex", "lualatex", "xelatex"]

    def __init__(self, version_str, node_meta_data, config):
        """

        :param (str) version_str: TexText version
        :param (TexTextEleMetaData) node_meta_data: The meta data of the node being processed
        :param (Settings) config: TexText configuration
        """
        self._config = config
        if not self._config.has_key("gui"):
            self._config["gui"] = {}

        if len(node_meta_data.text) > 0:
            self.text = node_meta_data.text
        else:
            self.text = ""

        self.textext_version = version_str
        self._convert_callback = None
        self.current_scale_factor = node_meta_data.scale_factor
        self.global_scale_factor = self._config.get("scale", 1.0)
        self.current_alignment = node_meta_data.alignment

        if node_meta_data.tex_command in self.TEX_COMMANDS:
            self.current_texcmd = node_meta_data.tex_command
        else:
            self.current_texcmd = self.TEX_COMMANDS[0]

        self.current_convert_strokes_to_path = node_meta_data.stroke_to_path

        self.preamble_file = node_meta_data.preamble
        self._preamble_widget = None
        self._scale = None
        self._source_buffer = None
        self._ok_button = None
        self._cancel_button = None
        self._window = None

    @abstractmethod
    def show(self, callback, preview_callback=None):
        """
        Present the GUI for entering LaTeX code and setting some options
        :param callback: A callback function (basically, what to do with the values from the GUI)
        :param preview_callback: A callback function to run to create a preview rendering
        """

    @abstractmethod
    def show_error_dialog(self, title, message_text, exception):
        """Displays a dialog with information about the occurred error"""

    @staticmethod
    def cb_cancel(widget=None, data=None):
        """Callback for Cancel button"""
        raise NotImplementedError()

    @abstractmethod
    def cb_ok(self, widget=None, data=None):
        """Callback for OK / Save button"""


class TexTextGuiTK(TexTextGuiBase):
    """TK GUI for editing TexText objects"""

    def __init__(self, version_str, node_meta_data, config):

        super().__init__(version_str, node_meta_data, config)

        # ToDo: Check which of this variables are  needed as class attributes
        self._root = None
        self._frame = None
        self._scale = None
        self._preamble = None
        self._askfilename_button = None
        self._convert_strokes_to_path = None
        self._tex_command_tk_str = None
        self._reset_button = None
        self._global_button = None
        self._alignment_tk_str = None
        self._word_wrap_tkva = None
        self._word_wrap_checkbotton = None
        self._word_wrap_tkval = None
        self._text_box = None
        self._cancel = None

    @staticmethod
    def cb_cancel(widget=None, data=None):
        """Callback for Cancel button"""
        raise SystemExit(1)

    # noinspection PyUnusedLocal, PyPep8Naming
    @staticmethod
    def validate_spinbox_input(d, i, P, s, S, v, V, W):
        """ Ensure that only floating point numbers are accepted as input of a tk widget
            Inspired from:
            https://stackoverflow.com/questions/4140437/interactively-validating-entry-widget-content-in-tkinter

            S -> string coming from user, s -> current string in the box, P -> resulting string in the box
            d -> Command (insert = 1, delete = 0), i -> Index position of cursor
            Note: Selecting an entry and copying something from the clipboard is rejected by this method. Reason:
            Without validation tk appends the content of the clipboard at the end of the selection leading to
            invalid content. So with or without this validation method you need to delete the content of the
            box before inserting the new stuff.
        """
        # pylint: disable=invalid-name,unused-argument
        if S == '' or P == '':
            # Initialization of widget (S=='') and deletion of entry (P=='')
            valid = True
        else:
            # All other cases: Ensure that result is OK
            try:
                float(P)
                valid = True
            except ValueError:
                valid = False
        return valid

    def show(self, callback, preview_callback=None):
        self._convert_callback = callback

        self._root = tk.Tk()
        self._root.title(f"TexText {self.textext_version}")

        self._frame = tk.Frame(self._root)
        self._frame.pack()

        # Framebox for preamble file
        box = tk.Frame(self._frame, relief="groove", borderwidth=2)
        label = tk.Label(box, text="Preamble file:")
        label.pack(pady=2, padx=5, anchor="w")
        self._preamble = tk.Entry(box)
        self._preamble.pack(expand=True, fill="x", ipady=4, pady=5, padx=5, side="left", anchor="e")
        self._preamble.insert(tk.END, self.preamble_file)

        self._askfilename_button = tk.Button(box, text="Select...",
                                             command=self.select_preamble_file)
        self._askfilename_button.pack(ipadx=10, ipady=4, pady=5, padx=5, side="left")

        box.pack(fill="x", pady=0, expand=True)

        # Frame holding the advanced settings and the tex command
        box2 = tk.Frame(self._frame, relief="flat")
        box2.pack(fill="x", pady=5, expand=True)

        # Framebox for advanced settings
        self._convert_strokes_to_path = tk.BooleanVar()
        self._convert_strokes_to_path.set(self.current_convert_strokes_to_path)
        box = tk.Frame(box2, relief="groove", borderwidth=2)
        label = tk.Label(box, text="SVG-output:")
        label.pack(pady=2, padx=5, anchor="w")
        tk.Checkbutton(box, text="No strokes", variable=self._convert_strokes_to_path,
                       onvalue=True, offvalue=False).pack(side="left", expand=False, anchor="w")
        box.pack(side=tk.RIGHT, fill="x", pady=5, expand=True)

        # Framebox for tex command
        self._tex_command_tk_str = tk.StringVar()
        self._tex_command_tk_str.set(self.current_texcmd)
        box = tk.Frame(box2, relief="groove", borderwidth=2)
        label = tk.Label(box, text="TeX command:")
        label.pack(pady=2, padx=5, anchor="w")
        for tex_command in self.TEX_COMMANDS:
            tk.Radiobutton(box, text=tex_command, variable=self._tex_command_tk_str,
                           value=tex_command).pack(side="left", expand=False, anchor="w")
        box.pack(side=tk.RIGHT, fill="x", pady=5, expand=True)

        # Framebox for scale factor and reset buttons
        box = tk.Frame(self._frame, relief="groove", borderwidth=2)
        label = tk.Label(box, text="Scale factor:")
        label.pack(pady=2, padx=5, anchor="w")

        validation_command = (self._root.register(self.validate_spinbox_input),
                              '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self._scale = tk.Spinbox(box, from_=0.001, to=10, increment=0.001, validate="key",
                                 validatecommand=validation_command)
        self._scale.pack(expand=True, fill="x", ipady=4, pady=5, padx=5, side="left", anchor="e")
        self._scale.delete(0, "end")
        self._scale.insert(0, self.current_scale_factor)

        reset_scale = self.current_scale_factor if self.current_scale_factor else self.global_scale_factor
        self._reset_button = tk.Button(box, text=f"Reset ({reset_scale:.3f})",
                                       command=self.reset_scale_factor)
        self._reset_button.pack(ipadx=10, ipady=4, pady=5, padx=5, side="left")
        if self.text == "":
            self._reset_button.config(state=tk.DISABLED)

        self._global_button = tk.Button(box, text=f"As previous ({self.global_scale_factor:.3f})",
                                        command=self.use_global_scale_factor)
        self._global_button.pack(ipadx=10, ipady=4, pady=5, padx=5, side="left")

        box.pack(fill="x", pady=5, expand=True)

        # Alignment
        box = tk.Frame(self._frame, relief="groove", borderwidth=2)
        label = tk.Label(box, text="Alignment to existing node:")
        label.pack(pady=2, padx=5, anchor="w")

        self._alignment_tk_str = tk.StringVar()  # Does not work in ctor, and tk.tk() in front opens 2nd window
        self._alignment_tk_str.set(self.current_alignment)  # Variable holding the radio button selection

        alignment_index_list = [0, 3, 6, 1, 4, 7, 2, 5, 8]  # To pick labels columnwise: xxx-left, xxx-center, ...
        vbox = None
        tk_state = tk.DISABLED if self.text == "" else tk.NORMAL
        for i, ind in enumerate(alignment_index_list):
            if i % 3 == 0:
                vbox = tk.Frame(box)
            tk.Radiobutton(vbox, text=self.ALIGNMENT_LABELS[ind], variable=self._alignment_tk_str,
                           value=self.ALIGNMENT_LABELS[ind], state=tk_state).pack(expand=True, anchor="w")
            if (i + 1) % 3 == 0:
                vbox.pack(side="left", fill="x", expand=True)
        box.pack(fill="x")

        # Word wrap status
        self._word_wrap_tkval = tk.BooleanVar()
        self._word_wrap_tkval.set(self._config["gui"].get("word_wrap", self.DEFAULT_WORDWRAP))

        # Frame with text input field and word wrap checkbox
        box = tk.Frame(self._frame, relief="groove", borderwidth=2)
        ibox = tk.Frame(box)
        label = tk.Label(ibox, text="LaTeX code:")
        self._word_wrap_checkbotton = tk.Checkbutton(ibox, text="Word wrap", variable=self._word_wrap_tkval,
                                                     onvalue=True, offvalue=False, command=self.cb_word_wrap)
        label.pack(pady=0, padx=5, side="left", anchor="w")
        self._word_wrap_checkbotton.pack(pady=0, padx=5, side="right", anchor="w")
        ibox.pack(expand=True, fill="both", pady=0, padx=0)

        ibox = tk.Frame(box)
        iibox = tk.Frame(ibox)
        self._text_box = tk.Text(iibox, width=70, height=12)  # 70 chars, 12 lines
        hscrollbar = tk.Scrollbar(iibox, orient=tk.HORIZONTAL, command=self._text_box.xview)
        self._text_box["xscrollcommand"] = hscrollbar.set
        self._text_box.pack(expand=True, fill="both", pady=0, padx=1, anchor="w")
        hscrollbar.pack(expand=True, fill="both", pady=2, padx=5)

        vscrollbar = tk.Scrollbar(ibox, orient=tk.VERTICAL, command=self._text_box.yview)
        self._text_box["yscrollcommand"] = vscrollbar.set
        iibox.pack(expand=True, fill="both", pady=0, padx=1, side="left", anchor="e")
        vscrollbar.pack(expand=True, fill="y", pady=2, padx=1, side="left", anchor="e")
        ibox.pack(expand=True, fill="both", pady=0, padx=5)

        self._text_box.insert(tk.END, self.text)
        self._text_box.configure(wrap=tk.WORD if self._word_wrap_tkval.get() else tk.NONE)

        box.pack(fill="x", pady=2)

        # OK and Cancel button
        box = tk.Frame(self._frame)
        self._ok_button = tk.Button(box, text="OK", command=self.cb_ok)
        self._ok_button.pack(ipadx=10, ipady=4, pady=5, padx=5, side="left")
        self._cancel = tk.Button(box, text="Cancel", command=self.cb_cancel)
        self._cancel.pack(ipadx=10, ipady=4, pady=5, padx=5, side="right")
        box.pack(expand=False)

        # Ensure that the window opens centered on the screen
        self._root.update()

        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        window_width = self._root.winfo_width()
        window_height = self._root.winfo_height()
        window_xpos = (screen_width/2) - (window_width/2)
        window_ypos = (screen_height/2) - (window_height/2)
        self._root.geometry(f"{int(window_width)}x{int(window_height)}+{int(window_xpos)}+{int(window_ypos)}")

        self._root.mainloop()
        return self._config

    def cb_ok(self, widget=None, data=None):
        try:
            self.global_scale_factor = float(self._scale.get())
        except ValueError:
            tk_msg_boxes.showerror("Scale factor error",
                                   "Please enter a valid floating point number for the scale factor!")
            return
        self.text = self._text_box.get(1.0, tk.END)
        self.preamble_file = self._preamble.get()
        self.current_convert_strokes_to_path = self._convert_strokes_to_path.get()

        try:
            self._convert_callback(self.text, self.preamble_file, self.global_scale_factor,
                                   self._alignment_tk_str.get(), self._tex_command_tk_str.get(),
                                   self.current_convert_strokes_to_path)
        except Exception as error:
            self.show_error_dialog("TexText Error",
                                   "Error occurred while converting text from Latex to SVG:",
                                   error)
            return False

        self._frame.quit()
        return False

    # noinspection PyUnusedLocal
    def cb_word_wrap(self, widget=None, data=None):
        self._text_box.configure(wrap=tk.WORD if self._word_wrap_tkval.get() else tk.NONE)
        self._config["gui"]["word_wrap"] = self._word_wrap_tkval.get()

    def reset_scale_factor(self, _=None):
        self._scale.delete(0, "end")
        self._scale.insert(0, self.current_scale_factor)

    def use_global_scale_factor(self, _=None):
        self._scale.delete(0, "end")
        self._scale.insert(0, self.global_scale_factor)

    def select_preamble_file(self):
        file_name = tk_file_dialogs.askopenfilename(initialdir=os.path.dirname(self._preamble.get()),
                                                    title="Select preamble file",
                                                    filetypes=(("LaTeX files", "*.tex"), ("all files", "*.*")))
        if file_name is not None:
            self._preamble.delete(0, tk.END)
            self._preamble.insert(tk.END, file_name)

    def show_error_dialog(self, title, message_text, exception):

        # ToDo: Check Windows behavior!! --> -disable
        self._root.wm_attributes("-topmost", False)

        err_dialog = tk.Toplevel(self._frame)
        err_dialog.minsize(300, 400)
        err_dialog.transient(self._frame)
        err_dialog.focus_force()
        err_dialog.grab_set()

        def add_textview(header, text):
            err_dialog_frame = tk.Frame(err_dialog)
            err_dialog_label = tk.Label(err_dialog_frame, text=header)
            err_dialog_label.pack(side='top', fill=tk.X)
            err_dialog_text = tk.Text(err_dialog_frame, height=10)
            err_dialog_text.insert(tk.END, text)
            err_dialog_text.pack(side='left', fill=tk.Y)
            err_dialog_scrollbar = tk.Scrollbar(err_dialog_frame)
            err_dialog_scrollbar.pack(side='right', fill=tk.Y)
            err_dialog_scrollbar.config(command=err_dialog_text.yview)
            err_dialog_text.config(yscrollcommand=err_dialog_scrollbar.set)
            err_dialog_frame.pack(side='top')

        def close_error_dialog():
            # ToDo: Check Windows behavior!! -disable
            self._root.wm_attributes("-topmost", True)
            err_dialog.destroy()

        err_dialog.protocol("WM_DELETE_WINDOW", close_error_dialog)

        add_textview(message_text, str(exception))

        if isinstance(exception, TexTextCommandFailed):
            if exception.stdout:
                add_textview('Stdout:', exception.stdout.decode('utf-8'))

            if exception.stderr:
                add_textview('Stderr:', exception.stderr.decode('utf-8'))

        close_button = tk.Button(err_dialog, text='OK', command=close_error_dialog)
        close_button.pack(side='top', fill='x', expand=True)


class TexTextGuiGTK(TexTextGuiBase):
    """GTK + Source Highlighting for editing TexText objects"""

    def __init__(self, version_str, node_meta_data, config):
        super().__init__(version_str, node_meta_data, config)

        # ToDo: Check which of this variables are  needed as class attributes
        self._preview = None  # type: Gtk.Image
        self._pixbuf = None  # type: GdkPixbuf
        self.preview_representation = "SCALE"  # type: str
        self._preview_scroll_window = None  # type: Gtk.ScrolledWindow
        self._scale_adj = None
        self._texcmd_cbox = None
        self._preview_callback = None
        self._source_view = None
        self._preview_button = None
        self._alignment_combobox = None
        self._conv_stroke2path = None
        self.pos_label = None
        self._preview_button = None
        self._alignment_combobox = None
        self._conv_stroke2path = None
        self._same_height_objects = None

        self.buffer_actions = [
            ('Open', Gtk.STOCK_OPEN, '_Open', '<control>O', 'Open a file', self.open_file_cb)
        ]

        if TOOLKIT == GTKSOURCEVIEW:
            self._view_actions = [
                ('FileMenu', None, '_File'),
                ('ViewMenu', None, '_View'),
                ('SettingsMenu', None, '_Settings'),
                ('FontSize', None, 'Editor Font Si_ze'),
                ('NewNodeContent', None, '_New Node Content'),
                ('CloseShortcut', None, 'Close TexText _Shortcut'),
                ('TabsWidth', None, '_Tabs Width'),
            ]
        else:
            self._view_actions = [
                ('FileMenu', None, '_File'),
                ('ViewMenu', None, '_View'),
                ('SettingsMenu', None, '_Settings'),
                ('FontSize', None, 'Editor Font Si_ze'),
                ('NewNodeContent', None, '_New Node Content'),
                ('CloseShortcut', None, '_Close TexText Shortcut'),
            ]

        self._toggle_actions = [
            ('ShowNumbers', None, 'Show _Line Numbers', None,
             'Toggle visibility of line numbers in the left margin', self.numbers_toggled_cb),
            ('AutoIndent', None, 'Enable _Auto Indent', None, 'Toggle automatic auto indentation of text',
             self.auto_indent_toggled_cb),
            ('InsertSpaces', None, 'Insert _Spaces Instead of Tabs', None,
             'Whether to insert space characters when inserting tabulations', self.insert_spaces_toggled_cb)
        ]

        self._word_wrap_action = [
            ('WordWrap', None, '_Word Wrap', None,
             'Wrap long lines in editor to avoid horizontal scrolling', self.word_wrap_toggled_cb)
        ]

        self._font_size_actions = [
            ('FontSize11', None, '1_1 pt', None, 'Set editor font size to 11pt', 0),
            ('FontSize12', None, '1_2 pt', None, 'Set editor font size to 12pt', 1),
            ('FontSize14', None, '1_4 pt', None, 'Set editor font size to 14pt', 2),
            ('FontSize16', None, '1_6 pt', None, 'Set editor font size to 16pt', 3)
        ]
        font_size = "\n".join(
            [f"<menuitem action=\'{action}\'/>" for (action, _, _, _, _, _) in self._font_size_actions])

        self._preview_white_background_action = [
            ('WhitePreviewBackground', None, 'White preview background', None,
             'Set preview background to white', self.on_preview_background_chagned)
        ]

        self._confirm_close_action = [
            ('ConfirmClose', None, '_Confirm Closing of Window', None,
             'Request confirmation for closing the window when text has been changed', self.confirm_close_toggled_cb)
        ]

        self._radio_actions = [
            (f"TabsWidth{num}", None, f"{num}", None, f"Set tabulation width to {num} spaces", num) for num in
            range(2, 13, 2)]

        if TOOLKIT == GTK:
            gtksourceview_ui_additions = ""
        else:
            menu_actions = "\n".join([f'<menuitem action=\'{action}\'/>' for (action, _, _, _, _, _) in self._radio_actions])
            gtksourceview_ui_additions = f"""
            <menuitem action='ShowNumbers'/>
            <menuitem action='AutoIndent'/>
            <menuitem action='InsertSpaces'/>
            <menu action='TabsWidth'>
            {menu_actions}
            </menu>
            """

        self._new_node_content_actions = [
            #     name of action ,   stock id,    label, accelerator,  tooltip, callback/value
            ('NewNodeContentEmpty', None, '_Empty', None, 'New node will be initialized with empty content', 0),
            ('NewNodeContentInlineMath', None, '_Inline math', None, 'New node will be initialized with $ $', 1),
            ('NewNodeContentDisplayMath', None, '_Display math', None, 'New node will be initialized with $$ $$', 2)
        ]
        new_node_content = "\n".join(
            [f'<menuitem action=\'{action}\'/>' for (action, _, _, _, _, _) in self._new_node_content_actions])

        self._close_shortcut_actions = [
            ('CloseShortcutEscape', None, '_ESC', None, 'TexText window closes when pressing ESC', 0),
            ('CloseShortcutCtrlQ', None, 'CTRL + _Q', None, 'TexText window closes when pressing CTRL + Q', 1),
            ('CloseShortcutNone', None, '_None', None, 'No shortcut for closing TexText window', 2)
        ]
        close_shortcut = "\n".join(
            [f'<menuitem action=\'{action}\'/>' for (action, _, _, _, _, _) in self._close_shortcut_actions])

        self._view_ui_description = f"""
        <ui>
          <menubar name='MainMenu'>
            <menu action='FileMenu'>
              <menuitem action='Open'/>
            </menu>
            <menu action='ViewMenu'>
              <menu action='FontSize'>
                {font_size}
              </menu>
              <menuitem action='WordWrap'/>
              {gtksourceview_ui_additions}
              <menuitem action='WhitePreviewBackground'/>
            </menu>
            <menu action='SettingsMenu'>
              <menu action='NewNodeContent'>
                {new_node_content}
              </menu>
              <menu action='CloseShortcut'>
                {close_shortcut} 
              </menu>
              <menuitem action='ConfirmClose'/>
            </menu>
          </menubar>
        </ui>
        """

    @staticmethod
    def set_monospace_font(text_view, font_size):
        """
        Set the font to monospace in the text view
        :param text_view: A GTK TextView
        :param font_size: The font size in the TextView in pt
        """
        try:
            from gi.repository import Pango  # pylint: disable=import-outside-toplevel
            font_desc = Pango.FontDescription(f'monospace {font_size}')
            if font_desc:
                text_view.modify_font(font_desc)
        except ImportError:
            pass

    @staticmethod
    def open_file_cb(_, text_buffer):
        """
        Present file chooser to select a source code file
        """
        chooser = Gtk.FileChooserDialog('Open file...', None,
                                        Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            if filename:
                TexTextGuiGTK.open_file(text_buffer, filename)
        chooser.destroy()

    @staticmethod
    def update_position_label(text_buffer, asktext, view):
        """
        Update the position label below the source code view
        :param (TexTextGuiGTK) asktext:
        :param text_buffer:
        :param view:
        """
        iterator = text_buffer.get_iter_at_mark(text_buffer.get_insert())
        nchars = iterator.get_offset()
        row = iterator.get_line() + 1
        start = iterator.copy()
        start.set_line_offset(0)
        col = 0

        if TOOLKIT == GTKSOURCEVIEW:
            tabwidth = view.get_tab_width()
            while start.compare(iterator) < 0:
                if start.get_char() == '\t':
                    col += tabwidth - col % tabwidth
                else:
                    col += 1
                start.forward_char()
            asktext.pos_label.set_text(f'char: {nchars}, line: {row}, column: {col + 1}')
        else:
            asktext.pos_label.set_text(f'char: {nchars}, line: {row}')

    @staticmethod
    def load_file(text_buffer, path):
        """
        Load text from a file into a text buffer
        :param text_buffer: the GTK text buffer
        :param path: where to load the file from
        :returns: True, if successful
        """

        try:
            with open(path, "r", encoding="utf-8") as file_handle:
                text = file_handle.read()
        except IOError:
            print(f"Couldn't load file: {path}")
            return False
        text_buffer.set_text(text)

        text_buffer.set_modified(True)
        text_buffer.place_cursor(text_buffer.get_start_iter())
        return True

    @staticmethod
    def open_file(text_buffer, filename):
        """
        Open a text file via its name
        :param text_buffer: Where to put the loaded text
        :param filename: File name
        """

        if os.path.isabs(filename):
            path = filename
        else:
            path = os.path.abspath(filename)

        TexTextGuiGTK.load_file(text_buffer, path)

    # Callback methods for the various menu items at the top of the window
    def numbers_toggled_cb(self, action, sourceview):
        sourceview.set_show_line_numbers(action.get_active())
        self._config["gui"]["line_numbers"] = action.get_active()

    def auto_indent_toggled_cb(self, action, sourceview):
        sourceview.set_auto_indent(action.get_active())
        self._config["gui"]["auto_indent"] = action.get_active()

    def insert_spaces_toggled_cb(self, action, sourceview):
        sourceview.set_insert_spaces_instead_of_tabs(action.get_active())
        self._config["gui"]["insert_spaces"] = action.get_active()

    def word_wrap_toggled_cb(self, action, sourceview):
        sourceview.set_wrap_mode(Gtk.WrapMode.WORD if action.get_active() else Gtk.WrapMode.NONE)
        self._config["gui"]["word_wrap"] = action.get_active()

    # noinspection PyUnusedLocal
    def on_preview_background_chagned(self, action, _):
        self._config["gui"]["white_preview_background"] = action.get_active()

    # noinspection PyUnusedLocal
    def tabs_toggled_cb(self, action, previous_value, sourceview):
        sourceview.set_tab_width(action.get_current_value())
        self._config["gui"]["tab_width"] = action.get_current_value()

    # noinspection PyUnusedLocal
    def new_node_content_cb(self, action, previous_value, sourceview):
        self._config["gui"]["new_node_content"] = self.NEW_NODE_CONTENT[action.get_current_value()]

    # noinspection PyUnusedLocal
    def font_size_cb(self, action, previous_value, sourceview):
        self._config["gui"]["font_size"] = self.FONT_SIZE[action.get_current_value()]
        self.set_monospace_font(sourceview, self._config["gui"]["font_size"])

    # noinspection PyUnusedLocal
    def close_shortcut_cb(self, action, previous_value, sourceview):
        self._config["gui"]["close_shortcut"] = self.CLOSE_SHORTCUT[action.get_current_value()]
        self._cancel_button.set_tooltip_text(
            f"Don't save changes ({self._close_shortcut_actions[action.get_current_value()][2]})".replace("_", ""))

    # noinspection PyUnusedLocal
    def confirm_close_toggled_cb(self, action, sourceview):
        self._config["gui"]["confirm_close"] = action.get_active()

    # noinspection PyUnusedLocal
    def cb_key_press(self, widget, event, data=None):
        """
        Handle keyboard shortcuts
        :param widget:
        :param event:
        :param data:
        :return: True, if a shortcut was recognized and handled
        """

        ctrl_is_pressed = Gdk.ModifierType.CONTROL_MASK & event.state
        if Gdk.keyval_name(event.keyval) == 'Return' and ctrl_is_pressed:
            self._ok_button.clicked()
            return True

        # Show/ update Preview shortcut (CTRL+P)
        if Gdk.keyval_name(event.keyval) == 'p' and ctrl_is_pressed:
            self._preview_button.clicked()
            return True

        # Cancel dialog via shortcut if set by the user
        close_shortcut_value = self._config["gui"].get("close_shortcut", self.DEFAULT_CLOSE_SHORTCUT)
        if (close_shortcut_value == 'Escape' and Gdk.keyval_name(event.keyval) == 'Escape') or \
           (close_shortcut_value == 'CtrlQ' and Gdk.keyval_name(event.keyval) == 'q' and
           ctrl_is_pressed):
            self._cancel_button.clicked()
            return True

        return False

    def cb_ok(self, widget=None, data=None):
        text_buffer = self._source_buffer
        self.text = text_buffer.get_text(text_buffer.get_start_iter(),
                                         text_buffer.get_end_iter(), True)

        if isinstance(self._preamble_widget, Gtk.FileChooser):
            self.preamble_file = self._preamble_widget.get_filename()
            if not self.preamble_file:
                self.preamble_file = ""
        else:
            self.preamble_file = self._preamble_widget.get_text()

        self.global_scale_factor = self._scale_adj.get_value()

        self.current_convert_strokes_to_path = self._conv_stroke2path.get_active()

        try:
            node_meta_data = TexTextEleMetaData()
            node_meta_data.textext_version = self.textext_version
            node_meta_data.text = self.text
            node_meta_data.preamble = self.preamble_file
            node_meta_data.scale_factor = self.global_scale_factor
            node_meta_data.tex_command = self.TEX_COMMANDS[self._texcmd_cbox.get_active()].lower()
            node_meta_data.alignment = self.ALIGNMENT_LABELS[self._alignment_combobox.get_active()]
            node_meta_data.stroke_to_path = self.current_convert_strokes_to_path
            self._convert_callback(node_meta_data)
        except Exception as error:
            self.show_error_dialog("TexText Error",
                                   "Error occurred while converting text from Latex to SVG:",
                                   error)
            return False

        Gtk.main_quit()
        return False

    def cb_cancel(self, widget=None, data=None):
        """Callback for Cancel button"""
        self.window_deleted_cb(widget, None, None)

    # noinspection PyUnusedLocal
    def move_cursor_cb(self, text_buffer, cursoriter, mark, view):
        self.update_position_label(text_buffer, self, view)

    # noinspection PyUnusedLocal
    def window_deleted_cb(self, widget, event, view):
        if (self._config["gui"].get("confirm_close", self.DEFAULT_CONFIRM_CLOSE)
                and self._source_buffer.get_text(self._source_buffer.get_start_iter(),
                                                 self._source_buffer.get_end_iter(), True) != self.text):
            dlg = Gtk.MessageDialog(self._window, Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE)
            dlg.set_markup(
                "<b>Do you want to close TexText without save?</b>\n\n"
                "Your changes will be lost if you don't save them."
            )
            dlg.add_button("Continue editing", Gtk.ResponseType.CLOSE) \
                .set_image(Gtk.Image.new_from_stock(Gtk.STOCK_GO_BACK, Gtk.IconSize.BUTTON))
            dlg.add_button("Close without save", Gtk.ResponseType.YES) \
                .set_image(Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.BUTTON))

            dlg.set_title("Close without save?")
            res = dlg.run()
            dlg.destroy()
            if res in (Gtk.ResponseType.CLOSE, Gtk.ResponseType.DELETE_EVENT):
                return True

        Gtk.main_quit()
        return False

    # noinspection PyUnusedLocal
    def update_preview(self, _):
        """Update the preview image of the GUI using the callback it gave """
        if self._preview_callback:
            node_meta_data = TexTextEleMetaData()

            node_meta_data.text = self._source_buffer.get_text(self._source_buffer.get_start_iter(),
                                                self._source_buffer.get_end_iter(), True)

            if isinstance(self._preamble_widget, Gtk.FileChooser):
                node_meta_data.preamble = self._preamble_widget.get_filename()
                if not node_meta_data.preamble:
                    node_meta_data.preamble = ""
            else:
                node_meta_data.preamble = self._preamble_widget.get_text()

            node_meta_data.scale_factor = self.global_scale_factor
            node_meta_data.tex_command = self.TEX_COMMANDS[self._texcmd_cbox.get_active()].lower()
            node_meta_data.alignment = self.ALIGNMENT_LABELS[self._alignment_combobox.get_active()]
            node_meta_data.stroke_to_path = self.current_convert_strokes_to_path

            try:
                self._preview_callback(node_meta_data, self.set_preview_image_from_file,
                                       self._config["gui"].get("white_preview_background",
                                                               self.DEFAULT_PREVIEW_WHITE_BACKGROUND))
            except Exception as error:
                self.show_error_dialog("TexText Error",
                                       "Error occurred while generating preview:",
                                       error)
                return False

    def set_preview_image_from_file(self, path):
        """
        Set the preview image in the GUI, scaled to the text view's width
        :param path: the path of the image
        """

        self._pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        self._preview_scroll_window.set_has_tooltip(False)
        self.update_preview_representation()

    # noinspection PyUnusedLocal
    def switch_preview_representation(self, _=None, event=None):
        if event.button == 1:  # left click only
            if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:  # only double click
                if self.preview_representation == "SCALE":
                    if self._preview_scroll_window.get_has_tooltip():
                        self.preview_representation = "SCROLL"
                else:
                    if self._preview_scroll_window.get_has_tooltip():
                        self.preview_representation = "SCALE"
                self.update_preview_representation()

    def update_preview_representation(self):

        max_preview_height = 150

        textview_width = self._source_view.get_allocation().width
        image_width = self._pixbuf.get_width()
        image_height = self._pixbuf.get_height()

        def set_scaled_preview():
            scale = 1
            if image_width > textview_width:
                scale = min(scale, (textview_width * 1.0 / image_width))

            if image_height > max_preview_height:
                scale = min(scale, (max_preview_height * 1.0 / image_height))

            pixbuf = self._pixbuf
            if scale != 1:
                pixbuf = self._pixbuf.scale_simple(int(image_width * scale), int(image_height * scale),
                                                   GdkPixbuf.InterpType.BILINEAR)
                self._preview_scroll_window.set_tooltip_text("Double click: scale to original size")

            self._preview.set_from_pixbuf(pixbuf)
            self._preview.set_size_request(pixbuf.get_width(), pixbuf.get_height())

            return image_height

        def set_scroll_preview():

            self._preview.set_size_request(image_width, image_height)

            scroll_bar_width = 30

            preview_area_height = image_height
            if image_width + scroll_bar_width >= textview_width:
                preview_area_height += scroll_bar_width

            if preview_area_height > max_preview_height or image_width > textview_width:
                self._preview_scroll_window.set_tooltip_text("Double click: scale to fit window")

            self._preview.set_from_pixbuf(self._pixbuf)
            self._preview.set_size_request(image_width, image_height)
            return preview_area_height

        if self.preview_representation == "SCROLL":
            desired_preview_area_height = set_scroll_preview()
        else:
            desired_preview_area_height = set_scaled_preview()

        self._preview_scroll_window.set_size_request(-1, min(desired_preview_area_height, max_preview_height))
        self._preview_scroll_window.show()

    # ---------- create view window
    def create_buttons(self):
        """Creates and connects the Save, Cancel and Preview buttons"""

        spacing = 0

        button_box = Gtk.HButtonBox()

        button_box.set_border_width(5)
        button_box.set_layout(Gtk.ButtonBoxStyle.EDGE)
        button_box.set_spacing(spacing)

        self._cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        self._cancel_button.set_tooltip_text("Don't save changes (ESC)")
        button_box.add(self._cancel_button)

        self._preview_button = Gtk.Button(label="Preview")
        self._preview_button.set_tooltip_text("Show/ update preview (CTRL+P)")
        button_box.add(self._preview_button)

        self._ok_button = Gtk.Button(stock=Gtk.STOCK_SAVE)
        self._ok_button.set_tooltip_text("Update or create new LaTeX output (CTRL+RETURN)")
        button_box.add(self._ok_button)

        self._cancel_button.connect("clicked", self.cb_cancel)
        self._ok_button.connect("clicked", self.cb_ok)
        self._preview_button.connect('clicked', self.update_preview)

        return button_box

    def clear_preamble(self, _=None):
        """
        Clear the preamble file setting
        """
        self.preamble_file = "default_packages.tex"
        self.set_preamble()

    def set_preamble(self):
        if hasattr(Gtk, 'FileChooserButton'):
            self._preamble_widget.set_filename(self.preamble_file)
        else:
            self._preamble_widget.set_text(self.preamble_file)

    def reset_scale_factor(self, _=None):
        self._scale_adj.set_value(self.current_scale_factor)

    def use_global_scale_factor(self, _=None):
        self._scale_adj.set_value(self.global_scale_factor)

    # ---------- Create main window
    def create_window(self):
        """
        Set up the window with all its widgets

        :return: the created window
        """
        window = Gtk.Window()
        window.type = Gtk.WindowType.TOPLEVEL
        window.set_border_width(2)
        window.set_title(f'Enter LaTeX Formula - TexText {self.textext_version}')

        # File chooser and Scale Adjustment
        if hasattr(Gtk, 'FileChooserButton'):
            self._preamble_widget = Gtk.FileChooserButton("...")
            self._preamble_widget.set_action(Gtk.FileChooserAction.OPEN)
        else:
            self._preamble_widget = Gtk.Entry()

        self.set_preamble()

        # --- Preamble file ---
        preamble_delete = Gtk.Button(label="Clear")
        preamble_delete.connect('clicked', self.clear_preamble)
        preamble_delete.set_tooltip_text("Clear the preamble file setting")

        preamble_frame = Gtk.Frame()
        preamble_frame.set_label("Preamble File")
        preamble_box = Gtk.HBox(homogeneous=False, spacing=0)
        preamble_frame.add(preamble_box)
        preamble_box.pack_start(self._preamble_widget, True, True, 5)
        preamble_box.pack_start(preamble_delete, False, False, 5)
        preamble_box.set_border_width(3)

        # --- Tex command ---
        texcmd_frame = Gtk.Frame()
        texcmd_frame.set_label("TeX command")
        texcmd_box = Gtk.HBox(homogeneous=False, spacing=0)
        texcmd_frame.add(texcmd_box)
        texcmd_box.set_border_width(3)

        tex_command_store = Gtk.ListStore(str)
        for tex_command in self.TEX_COMMANDS:
            tex_command_store.append([tex_command])

        self._texcmd_cbox = Gtk.ComboBox.new_with_model(tex_command_store)
        renderer_text = Gtk.CellRendererText()
        self._texcmd_cbox.pack_start(renderer_text, True)
        self._texcmd_cbox.add_attribute(renderer_text, "text", 0)

        self._texcmd_cbox.set_active(self.TEX_COMMANDS.index(self.current_texcmd))
        self._texcmd_cbox.set_tooltip_text("TeX command used for compiling.")
        texcmd_box.pack_start(self._texcmd_cbox, True, True, 5)

        # --- Scaling ---
        scale_frame = Gtk.Frame()
        scale_frame.set_label("Scale Factor")
        scale_box = Gtk.HBox(homogeneous=False, spacing=0)
        scale_box.set_border_width(3)
        scale_frame.add(scale_box)
        self._scale_adj = Gtk.Adjustment(lower=0.001, upper=180, step_incr=0.001, page_incr=1)
        self._scale = Gtk.SpinButton()
        self._scale.set_adjustment(self._scale_adj)
        self._scale.set_digits(3)
        self._scale_adj.set_value(self.current_scale_factor)
        self._scale.set_tooltip_text("Change the scale of the LaTeX output")

        # We need buttons with custom labels and stock icons, so we make some
        reset_scale = self.current_scale_factor if self.current_scale_factor else self.global_scale_factor
        scale_reset_button = Gtk.Button.new_from_icon_name('edit-undo', Gtk.IconSize.BUTTON)
        scale_reset_button.set_label(f'Reset ({reset_scale:.3f})')
        scale_reset_button.set_always_show_image(True)
        scale_reset_button.set_tooltip_text(
            f"Set scale factor to the value this node has been created with ({reset_scale:.3f})")
        scale_reset_button.connect('clicked', self.reset_scale_factor)
        if self.text == "":
            scale_reset_button.set_sensitive(False)

        scale_global_button = Gtk.Button.new_from_icon_name('edit-copy', Gtk.IconSize.BUTTON)
        scale_global_button.set_label(f'As previous ({self.global_scale_factor:.3f})')
        scale_global_button.set_always_show_image(True)
        scale_global_button.set_tooltip_text(
            f"Set scale factor to the value of the previously edited node in Inkscape ({self.global_scale_factor:.3f})")
        scale_global_button.connect('clicked', self.use_global_scale_factor)

        scale_box.pack_start(self._scale, True, True, 2)
        scale_box.pack_start(scale_reset_button, False, False, 2)
        scale_box.pack_start(scale_global_button, False, False, 2)

        # --- Alignment box ---
        alignment_frame = Gtk.Frame()
        alignment_frame.set_label("Alignment")
        alignment_box = Gtk.HBox(homogeneous=False, spacing=0)
        alignment_box.set_border_width(3)
        alignment_frame.add(alignment_box)

        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf)
        for algn in self.ALIGNMENT_LABELS:
            vals = tuple(algn.split(" "))
            path = os.path.join(os.path.dirname(__file__), "icons", f"alignment-{vals[0]}-{vals[1]}.svg.png")
            assert os.path.exists(path)
            liststore.append([GdkPixbuf.Pixbuf.new_from_file(path)])

        self._alignment_combobox = Gtk.ComboBox()

        cell = Gtk.CellRendererPixbuf()
        self._alignment_combobox.pack_start(cell, True)
        self._alignment_combobox.add_attribute(cell, 'pixbuf', 0)
        self._alignment_combobox.set_model(liststore)
        self._alignment_combobox.set_wrap_width(3)
        self._alignment_combobox.set_active(self.ALIGNMENT_LABELS.index(self.current_alignment))
        self._alignment_combobox.set_tooltip_text("Set alignment anchor position")
        if self.text == "":
            self._alignment_combobox.set_sensitive(False)

        alignment_box.pack_start(self._alignment_combobox, True, True, 2)

        # Advanced settings
        adv_settings_frame = Gtk.Frame()
        adv_settings_frame.set_label("SVG output")
        self._conv_stroke2path = Gtk.CheckButton(label="No strokes")
        self._conv_stroke2path.set_tooltip_text("Ensures that strokes (lines, e.g. in \\sqrt, \\frac) "
                                                "can be easily \ncolored in Inkscape "
                                                "(Time consuming compilation!)")
        self._conv_stroke2path.set_active(self.current_convert_strokes_to_path)
        adv_settings_frame.add(self._conv_stroke2path)

        # --- Scale, alignment and advanced settings together in one "line"
        scale_align_hbox = Gtk.HBox(homogeneous=False, spacing=0)
        scale_align_hbox.pack_start(scale_frame, False, False, 5)
        scale_align_hbox.pack_start(alignment_frame, True, True, 5)
        scale_align_hbox.pack_start(adv_settings_frame, True, True, 5)

        # --- TeX code window ---
        # Scrolling Window with Source View inside
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_shadow_type(Gtk.ShadowType.IN)

        if TOOLKIT == GTKSOURCEVIEW:
            # Source code view
            text_buffer = GtkSource.Buffer()

            # set LaTeX as highlighting language, so that pasted text is also highlighted as such
            lang_manager = GtkSource.LanguageManager()
            latex_language = lang_manager.get_language("latex")
            text_buffer.set_language(latex_language)

            source_view = GtkSource.View.new_with_buffer(text_buffer)
        else:
            # normal text view
            text_buffer = Gtk.TextBuffer()
            source_view = Gtk.TextView()
            source_view.set_buffer(text_buffer)

        self._source_buffer = text_buffer
        self._source_view = source_view
        self._source_buffer.set_text(self.text)
        self._source_view.set_size_request(-1, 150)

        scroll_window.add(self._source_view)
        self.set_monospace_font(self._source_view, self.DEFAULT_FONTSIZE)

        # Action group and UI manager
        ui_manager = Gtk.UIManager()
        accel_group = ui_manager.get_accel_group()
        window.add_accel_group(accel_group)
        ui_manager.add_ui_from_string(self._view_ui_description)

        action_group = Gtk.ActionGroup('ViewActions')
        action_group.add_actions(self._view_actions, source_view)
        action_group.add_actions(self.buffer_actions, text_buffer)
        action_group.add_radio_actions(self._new_node_content_actions, -1, self.new_node_content_cb, source_view)
        action_group.add_radio_actions(self._close_shortcut_actions, -1, self.close_shortcut_cb, source_view)
        action_group.add_radio_actions(self._font_size_actions, -1, self.font_size_cb, source_view)
        action_group.add_toggle_actions(self._confirm_close_action, source_view)
        action_group.add_toggle_actions(self._word_wrap_action, source_view)
        action_group.add_toggle_actions(self._preview_white_background_action, source_view)
        if TOOLKIT == GTKSOURCEVIEW:
            action_group.add_toggle_actions(self._toggle_actions, source_view)
            action_group.add_radio_actions(self._radio_actions, -1, self.tabs_toggled_cb, source_view)
        ui_manager.insert_action_group(action_group, 0)

        # Menu
        menu = ui_manager.get_widget('/MainMenu')

        # Cursor position label
        self.pos_label = Gtk.Label()
        self.pos_label.set_text('Position')

        # latex preview
        self._preview = Gtk.Image()
        self._preview_scroll_window = Gtk.ScrolledWindow()
        self._preview_scroll_window.set_shadow_type(Gtk.ShadowType.NONE)
        self._preview_scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_viewport = Gtk.Viewport()
        preview_viewport.set_shadow_type(Gtk.ShadowType.NONE)
        preview_viewport.add(self._preview)
        self._preview_scroll_window.add(preview_viewport)

        preview_event_box = Gtk.EventBox()
        preview_event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        preview_event_box.connect('button-press-event', self.switch_preview_representation)
        preview_event_box.add(self._preview_scroll_window)

        # Vertical Layout
        vbox = Gtk.VBox(False, 4)
        window.add(vbox)

        vbox.pack_start(menu, False, False, 0)

        hbox_texcmd_preamble = Gtk.HBox(True, 0)

        hbox_texcmd_preamble.pack_start(texcmd_frame, True, True, 5)
        hbox_texcmd_preamble.pack_start(preamble_frame, True, True, 5)

        vbox.pack_start(hbox_texcmd_preamble, False, False, 0)
        vbox.pack_start(scale_align_hbox, False, False, 0)

        vbox.pack_start(scroll_window, True, True, 0)
        vbox.pack_start(self.pos_label, False, False, 0)
        vbox.pack_start(preview_event_box, False, False, 0)
        buttons_row = self.create_buttons()
        vbox.pack_start(buttons_row, False, False, 0)

        vbox.show_all()

        # ToDo: Currently this seems to do nothing?
        self._same_height_objects = [preamble_frame, texcmd_frame, scale_align_hbox]

        self._preview_scroll_window.hide()

        # preselect menu check items
        groups = ui_manager.get_action_groups()
        # retrieve the view action group at position 0 in the list
        action_group = groups[0]
        font_size_value = self._config["gui"].get("font_size", self.DEFAULT_FONTSIZE)
        action = action_group.get_action(f'FontSize{font_size_value}')
        action.set_active(True)
        action = action_group.get_action('WordWrap')
        action.set_active(self._config["gui"].get("word_wrap", self.DEFAULT_WORDWRAP))
        new_node_content_value = self._config["gui"].get("new_node_content", self.DEFAULT_NEW_NODE_CONTENT)
        action = action_group.get_action(f'NewNodeContent{new_node_content_value}')
        action.set_active(True)
        close_shortcut_value = self._config["gui"].get("close_shortcut", self.DEFAULT_CLOSE_SHORTCUT)
        action = action_group.get_action(f'CloseShortcut{close_shortcut_value}')
        action.set_active(True)
        action = action_group.get_action('ConfirmClose')
        action.set_active(self._config["gui"].get("confirm_close", self.DEFAULT_CONFIRM_CLOSE))
        action = action_group.get_action('WhitePreviewBackground')
        action.set_active(self._config["gui"].get("white_preview_background", self.DEFAULT_PREVIEW_WHITE_BACKGROUND))
        if TOOLKIT == GTKSOURCEVIEW:
            action = action_group.get_action('ShowNumbers')
            action.set_active(self._config["gui"].get("line_numbers", self.DEFAULT_SHOWLINENUMBERS))
            action = action_group.get_action('AutoIndent')
            action.set_active(self._config["gui"].get("auto_indent", self.DEFAULT_AUTOINDENT))
            action = action_group.get_action('InsertSpaces')
            action.set_active(self._config["gui"].get("insert_spaces", self.DEFAULT_INSERTSPACES))
            action = action_group.get_action(f"TabsWidth{self._config['gui'].get('tab_width', self.DEFAULT_TABWIDTH)}")
            action.set_active(True)
            self._source_view.set_tab_width(action.get_current_value())  # <- Why is this explicit call necessary ??

        if self.text == "":
            if new_node_content_value == 'InlineMath':
                self.text = "$$"
                self._source_buffer.set_text(self.text)
                sb_iter = self._source_buffer.get_iter_at_offset(1)
                self._source_buffer.place_cursor(sb_iter)
            if new_node_content_value == 'DisplayMath':
                self.text = "$$$$"
                self._source_buffer.set_text(self.text)
                sb_iter = self._source_buffer.get_iter_at_offset(2)
                self._source_buffer.place_cursor(sb_iter)

        # Connect event callbacks
        window.connect("key-press-event", self.cb_key_press)
        text_buffer.connect('changed', self.update_position_label, self, source_view)
        window.connect('delete-event', self.window_deleted_cb, source_view)
        text_buffer.connect('mark_set', self.move_cursor_cb, source_view)

        icon_sizes = [16, 32, 64, 128]
        icon_files = [os.path.join(
            os.path.dirname(__file__),
            "icons",
            f"logo-{size}x{size}.png")
            for size in icon_sizes]
        icons = [GdkPixbuf.Pixbuf.new_from_file(path) for path in icon_files if os.path.isfile(path)]
        window.set_icon_list(icons)

        return window

    def show(self, callback, preview_callback=None):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", module="asktext")
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            self._convert_callback = callback
            self._preview_callback = preview_callback

            # create first window
            with redirect_stderr(None):
                window = self.create_window()
            window.set_default_size(500, 525)
            # Until commit 802d295e46877fd58842b61dbea4276372a2505d we called own normalize_ui_row_heights here with
            # bad hide/show/hide hack, see issue #114
            window.show()
            self._window = window
            self._window.set_focus(self._source_view)

            # main loop
            Gtk.main()
            return self._config

    def show_error_dialog(self, title, message_text, exception):

        dialog = Gtk.Dialog(title, self._window)
        dialog.set_default_size(450, 300)
        button = dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.CLOSE)
        button.connect("clicked", lambda w, d=None: dialog.destroy())
        message_label = Gtk.Label()
        message_label.set_markup(f"<b>{message_text}</b>")
        message_label.set_justify(Gtk.Justification.LEFT)

        raw_output_box = Gtk.VBox()

        def add_section(header, text):

            text_view = Gtk.TextView()
            text_view.set_editable(False)
            text_view.set_left_margin(5)
            text_view.set_right_margin(5)
            text_view.set_wrap_mode(Gtk.WrapMode.WORD)
            text_view.get_buffer().set_text(text)
            text_view.show()

            scroll_window = Gtk.ScrolledWindow()
            scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
            scroll_window.set_shadow_type(Gtk.ShadowType.IN)
            scroll_window.set_min_content_height(150)
            scroll_window.add(text_view)
            scroll_window.show()

            if header is None:
                dialog.vbox.pack_start(scroll_window, expand=True, fill=True, padding=5)
                return

            expander = Gtk.Expander()

            # noinspection PyUnusedLocal
            def callback(_):
                if expander.get_expanded():
                    desired_height = 20
                else:
                    desired_height = 150
                expander.set_size_request(-1, desired_height)

            expander.connect('activate', callback)
            expander.add(scroll_window)
            expander.show()

            expander.set_label(header)
            expander.set_use_markup(True)

            expander.set_size_request(20, -1)
            scroll_window.hide()

            dialog.vbox.pack_start(expander, expand=True, fill=True, padding=5)

        dialog.vbox.pack_start(message_label, expand=False, fill=True, padding=5)
        add_section(None, str(exception))
        dialog.vbox.pack_start(raw_output_box, expand=False, fill=True, padding=5)

        if isinstance(exception, TexTextCommandFailed):
            if exception.stdout:
                add_section("Stdout: <small><i>(click to expand)</i></small>", exception.stdout.decode('utf-8'))
            if exception.stderr:
                add_section("Stderr: <small><i>(click to expand)</i></small>", exception.stderr.decode('utf-8'))
        dialog.show_all()
        dialog.run()


if TOOLKIT == TK:
    TexTextGui = TexTextGuiTK
elif TOOLKIT in (GTK, GTKSOURCEVIEW):
    TexTextGui = TexTextGuiGTK
