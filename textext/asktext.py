"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2021 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

This is the GUI part of TexText, handling several more or less
sophisticated dialog windows depending on the installed tools.

It is used uniformly from base.py via the ask method of the
AskText class depending on the available GUI framework
(TkInter or GTK3).
"""

DEBUG = False
debug_text = r"""$
\left(
   \begin{array}{ccc}
     a_{11} & \cdots & a_{1n} \\
     \vdots & \ddots & \vdots \\
     a_{m1} & \cdots & a_{mn}
   \end{array}
\right)
$"""

WINDOW_TITLE = "Enter LaTeX Formula - TexText"

GTKSOURCEVIEW = "GTK Source View"
GTK = "GTK"
TK = "TK"

TOOLKIT = None

import os
import sys
import warnings
from .errors import TexTextCommandFailed
from textext.utility import SuppressStream

# unfortunately, with Inkscape being 32bit on OSX, I couldn't get GTKSourceView to work, yet

# Try GTK first
#   If successful, try GTKSourceView (bonus points!)
#   If unsuccessful, try TK (first for Python 3, then for Python 2)
#   When not even TK could be imported, abort with error message
try:
    # Hotfix for Inkscape 1.0.1 on Windows: HarfBuzz-0.0.typelib is missing
    # in the Inkscape installation Python subsystem, hence we ship
    # it manually and set the search path accordingly here
    # ToDo: Remove this hotfix when Inkscape 1.0.2 is released and mark
    #       Inkscape 1.0.1 as incompatible with TexText
    if os.name == 'nt':
        os.environ['GI_TYPELIB_PATH'] = os.path.dirname(os.path.abspath(__file__))

    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    from gi.repository import Gdk, GdkPixbuf

    try:

        gi.require_version('GtkSource', '3.0')
        from gi.repository import GtkSource

        TOOLKIT = GTKSOURCEVIEW
    except (ImportError, TypeError, ValueError) as _:
        TOOLKIT = GTK

except (ImportError, TypeError, ValueError) as _:
    try:
        if sys.version_info[0] == 3: # TK for Python 3 (if this fails, try Python 2 below)
            import tkinter as Tk
            from tkinter import messagebox as TkMsgBoxes
            from tkinter import filedialog as TkFileDialogs
        else: # TK for Python 2
            import Tkinter as Tk
            import tkMessageBox as TkMsgBoxes
            import tkFileDialog as TkFileDialogs
        TOOLKIT = TK

    except ImportError:
        raise RuntimeError("\nNeither GTK nor TKinter is available!\nMake sure that at least one of these "
                           "bindings for the graphical user interface of TexText is installed! Refer to the "
                           "installation instructions on https://textext.github.io/textext/ !")


def set_monospace_font(text_view):
    """
    Set the font to monospace in the text view
    :param text_view: A GTK TextView
    """
    try:
        import pango

        font_desc = pango.FontDescription('monospace 11')
        if font_desc:
            text_view.modify_font(font_desc)
    except ImportError:
        pass


class AskText(object):
    """GUI for editing TexText objects"""

    ALIGNMENT_LABELS = ["top left", "top center", "top right",
                        "middle left", "middle center", "middle right",
                        "bottom left", "bottom center", "bottom right"]
    DEFAULT_WORDWRAP = False
    DEFAULT_SHOWLINENUMBERS = True
    DEFAULT_AUTOINDENT = True
    DEFAULT_INSERTSPACES = True
    DEFAULT_TABWIDTH = 4
    DEFAULT_NEW_NODE_CONTENT = "Empty"
    DEFAULT_CLOSE_SHORTCUT = "Escape"
    DEFAULT_CONFIRM_CLOSE = True
    DEFAULT_PREVIEW_WHITE_BACKGROUND = False
    NEW_NODE_CONTENT = ["Empty", "InlineMath", "DisplayMath"]
    CLOSE_SHORTCUT = ["Escape", "CtrlQ", "None"]

    def __init__(self, version_str, text, preamble_file, global_scale_factor, current_scale_factor, current_alignment,
                 current_texcmd, current_convert_strokes_to_path, tex_commands, gui_config):
        self.TEX_COMMANDS = tex_commands
        if len(text) > 0:
            self.text = text
        else:
            if DEBUG:
                self.text = debug_text
            else:
                self.text = ""

        self.textext_version = version_str
        self.callback = None
        self.global_scale_factor = global_scale_factor
        self.current_scale_factor = current_scale_factor
        self.current_alignment = current_alignment

        if current_texcmd in self.TEX_COMMANDS:
            self.current_texcmd = current_texcmd
        else:
            self.current_texcmd = self.TEX_COMMANDS[0]

        self.current_convert_strokes_to_path = current_convert_strokes_to_path

        self.preamble_file = preamble_file
        self._preamble_widget = None
        self._scale = None
        self._gui_config = gui_config
        self._source_buffer = None
        self._ok_button = None
        self._cancel_button = None
        self._window = None

    def ask(self, callback, preview_callback=None):
        """
        Present the GUI for entering LaTeX code and setting some options
        :param callback: A callback function (basically, what to do with the values from the GUI)
        :param preview_callback: A callback function to run to create a preview rendering
        """
        raise NotImplementedError()

    def show_error_dialog(self, title, message_text, exception):
        """
        Presents an error dialog

        :param parent: Parent window
        :param title: Error title text
        :param message_text: Message text to be displayed
        :param exception: Exception thrown
        """
        raise NotImplementedError()

    @staticmethod
    def cb_cancel(widget=None, data=None):
        """Callback for Cancel button"""
        raise NotImplementedError()

    def cb_ok(self, widget=None, data=None):
        """Callback for OK / Save button"""
        raise NotImplementedError()

    def scale_factor_after_loading(self):
        """
        The slider's initial scale factor:
         Either the previously saved value or the global scale factor or a default of 1.0 if the extension
         runs for the first time.

        :return: Initial scale factor for the slider
        """
        scale_factor = self.current_scale_factor
        if scale_factor is None:
            scale_factor = self.global_scale_factor
        if scale_factor is None:
            scale_factor = 1.0
        return scale_factor


class AskTextTK(AskText):
    """TK GUI for editing TexText objects"""

    def __init__(self, version_str, text, preamble_file, global_scale_factor, current_scale_factor, current_alignment,
                 current_texcmd, current_convert_strokes_to_path, tex_commands, gui_config):
        super(AskTextTK, self).__init__(version_str, text, preamble_file, global_scale_factor, current_scale_factor,
                                        current_alignment, current_texcmd, current_convert_strokes_to_path, tex_commands, gui_config)
        self._frame = None
        self._scale = None

    @staticmethod
    def cb_cancel(widget=None, data=None):
        """Callback for Cancel button"""
        raise SystemExit(1)

    @staticmethod
    def validate_spinbox_input(d, i, P, s, S, v, V, W):
        """ Ensure that only floating point numbers are accepted as input of a Tk widget
            Inspired from:
            https://stackoverflow.com/questions/4140437/interactively-validating-entry-widget-content-in-tkinter

            S -> string coming from user, s -> current string in the box, P -> resulting string in the box
            d -> Command (insert = 1, delete = 0), i -> Index position of cursor
            Note: Selecting an entry and copying something from the clipboard is rejected by this method. Reason:
            Without validation Tk appends the content of the clipboard at the end of the selection leading to
            invalid content. So with or without this validation method you need to delete the content of the
            box before inserting the new stuff.
        """
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

    def ask(self, callback, preview_callback=None):
        self.callback = callback

        self._root = Tk.Tk()
        self._root.title("TexText {0}".format(self.textext_version))

        self._frame = Tk.Frame(self._root)
        self._frame.pack()

        # Frame box for preamble file
        box = Tk.Frame(self._frame, relief="groove", borderwidth=2)
        label = Tk.Label(box, text="Preamble file:")
        label.pack(pady=2, padx=5, anchor="w")
        self._preamble = Tk.Entry(box)
        self._preamble.pack(expand=True, fill="x", ipady=4, pady=5, padx=5, side="left", anchor="e")
        self._preamble.insert(Tk.END, self.preamble_file)

        self._askfilename_button = Tk.Button(box, text="Select...",
                                       command=self.select_preamble_file)
        self._askfilename_button.pack(ipadx=10, ipady=4, pady=5, padx=5, side="left")

        box.pack(fill="x", pady=0, expand=True)

        # Frame holding the advanced settings and the tex command
        box2 = Tk.Frame(self._frame, relief="flat")
        box2.pack(fill="x", pady=5, expand=True)

        # Frame box for advanced settings
        self._convert_strokes_to_path = Tk.BooleanVar()
        self._convert_strokes_to_path.set(self.current_convert_strokes_to_path)
        box = Tk.Frame(box2, relief="groove", borderwidth=2)
        label = Tk.Label(box, text="SVG-output:")
        label.pack(pady=2, padx=5, anchor="w")
        Tk.Checkbutton(box, text="No strokes", variable=self._convert_strokes_to_path, onvalue=True, offvalue=False).pack(side="left", expand=False, anchor="w")
        box.pack(side=Tk.RIGHT, fill="x", pady=5, expand=True)

        # Frame box for tex command
        self._tex_command_tk_str = Tk.StringVar()
        self._tex_command_tk_str.set(self.current_texcmd)
        box = Tk.Frame(box2, relief="groove", borderwidth=2)
        label = Tk.Label(box, text="TeX command:")
        label.pack(pady=2, padx=5, anchor="w")
        for tex_command in self.TEX_COMMANDS:
            Tk.Radiobutton(box, text=tex_command, variable=self._tex_command_tk_str,
                           value=tex_command).pack(side="left", expand=False, anchor="w")
        box.pack(side=Tk.RIGHT, fill="x", pady=5, expand=True)


        # Frame box for scale factor and reset buttons
        box = Tk.Frame(self._frame, relief="groove", borderwidth=2)
        label = Tk.Label(box, text="Scale factor:")
        label.pack(pady=2, padx=5, anchor="w")

        validation_command = (self._root.register(self.validate_spinbox_input),
                              '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self._scale = Tk.Spinbox(box, from_=0.001, to=10, increment=0.001, validate="key",
                                 validatecommand=validation_command)
        self._scale.pack(expand=True, fill="x", ipady=4, pady=5, padx=5, side="left", anchor="e")
        self._scale.delete(0, "end")
        self._scale.insert(0, self.scale_factor_after_loading())

        reset_scale = self.current_scale_factor if self.current_scale_factor else self.global_scale_factor
        self._reset_button = Tk.Button(box, text="Reset ({0:.3f})".format(reset_scale),
                                       command=self.reset_scale_factor)
        self._reset_button.pack(ipadx=10, ipady=4, pady=5, padx=5, side="left")
        if self.text == "":
            self._reset_button.config(state=Tk.DISABLED)

        self._global_button = Tk.Button(box, text="As previous ({0:.3f})".format(self.global_scale_factor),
                                        command=self.use_global_scale_factor)
        self._global_button.pack(ipadx=10, ipady=4, pady=5, padx=5, side="left")

        box.pack(fill="x", pady=5, expand=True)

        # Alignment
        box = Tk.Frame(self._frame, relief="groove", borderwidth=2)
        label = Tk.Label(box, text="Alignment to existing node:")
        label.pack(pady=2, padx=5, anchor="w")

        self._alignment_tk_str = Tk.StringVar() # Does not work in ctor, and Tk.Tk() in front opens 2nd window
        self._alignment_tk_str.set(self.current_alignment) # Variable holding the radio button selection

        alignment_index_list = [0, 3, 6, 1, 4, 7, 2, 5, 8] # To pick labels columnwise: xxx-left, xxx-center, ...
        vbox = None
        tk_state = Tk.DISABLED if self.text == "" else Tk.NORMAL
        for i, ind in enumerate(alignment_index_list):
            if i % 3 == 0:
                vbox = Tk.Frame(box)
            Tk.Radiobutton(vbox, text=self.ALIGNMENT_LABELS[ind], variable=self._alignment_tk_str,
                           value=self.ALIGNMENT_LABELS[ind], state=tk_state).pack(expand=True, anchor="w")
            if (i + 1) % 3 == 0:
                vbox.pack(side="left", fill="x", expand=True)
        box.pack(fill="x")

        # Word wrap status
        self._word_wrap_tkval = Tk.BooleanVar()
        self._word_wrap_tkval.set(self._gui_config.get("word_wrap", self.DEFAULT_WORDWRAP))

        # Frame with text input field and word wrap checkbox
        box = Tk.Frame(self._frame, relief="groove", borderwidth=2)
        ibox = Tk.Frame(box)
        label = Tk.Label(ibox, text="LaTeX code:")
        self._word_wrap_checkbotton = Tk.Checkbutton(ibox, text="Word wrap", variable=self._word_wrap_tkval,
                                                     onvalue=True, offvalue=False, command=self.cb_word_wrap)
        label.pack(pady=0, padx=5, side = "left", anchor="w")
        self._word_wrap_checkbotton.pack(pady=0, padx=5, side = "right", anchor="w")
        ibox.pack(expand=True, fill="both", pady=0, padx=0)

        ibox = Tk.Frame(box)
        iibox = Tk.Frame(ibox)
        self._text_box = Tk.Text(iibox, width=70, height=12) # 70 chars, 12 lines
        hscrollbar = Tk.Scrollbar(iibox, orient=Tk.HORIZONTAL, command=self._text_box.xview)
        self._text_box["xscrollcommand"]=hscrollbar.set
        self._text_box.pack(expand=True, fill="both", pady=0, padx=1, anchor = "w")
        hscrollbar.pack(expand=True, fill="both", pady=2, padx=5)

        vscrollbar = Tk.Scrollbar(ibox, orient=Tk.VERTICAL, command=self._text_box.yview)
        self._text_box["yscrollcommand"]=vscrollbar.set
        iibox.pack(expand=True, fill="both", pady=0, padx=1, side="left", anchor="e")
        vscrollbar.pack(expand=True, fill="y", pady=2, padx=1, side = "left", anchor = "e")
        ibox.pack(expand=True, fill="both", pady=0, padx=5)

        self._text_box.insert(Tk.END, self.text)
        self._text_box.configure(wrap=Tk.WORD if self._word_wrap_tkval.get() else Tk.NONE)

        box.pack(fill="x", pady=2)

        # OK and Cancel button
        box = Tk.Frame(self._frame)
        self._ok_button = Tk.Button(box, text="OK", command=self.cb_ok)
        self._ok_button.pack(ipadx=10, ipady=4, pady=5, padx=5, side="left")
        self._cancel = Tk.Button(box, text="Cancel", command=self.cb_cancel)
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
        self._root.geometry('%dx%d+%d+%d' % (window_width, window_height, window_xpos, window_ypos))

        self._root.mainloop()
        return self._gui_config

    def cb_ok(self, widget=None, data=None):
        try:
            self.global_scale_factor = float(self._scale.get())
        except ValueError:
            TkMsgBoxes.showerror("Scale factor error",
                                 "Please enter a valid floating point number for the scale factor!")
            return
        self.text = self._text_box.get(1.0, Tk.END)
        self.preamble_file = self._preamble.get()
        self.current_convert_strokes_to_path = self._convert_strokes_to_path.get()

        try:
            self.callback(self.text, self.preamble_file, self.global_scale_factor, self._alignment_tk_str.get(),
                          self._tex_command_tk_str.get(), self.current_convert_strokes_to_path)
        except Exception as error:
            self.show_error_dialog("TexText Error",
                              "Error occurred while converting text from Latex to SVG:",
                              error)
            return False

        self._frame.quit()
        return False

    def cb_word_wrap(self, widget=None, data=None):
        self._text_box.configure(wrap=Tk.WORD if self._word_wrap_tkval.get() else Tk.NONE)
        self._gui_config["word_wrap"] = self._word_wrap_tkval.get()

    def reset_scale_factor(self, _=None):
        self._scale.delete(0, "end")
        self._scale.insert(0, self.current_scale_factor)

    def use_global_scale_factor(self, _=None):
        self._scale.delete(0, "end")
        self._scale.insert(0, self.global_scale_factor)

    def select_preamble_file(self):
        file_name = TkFileDialogs.askopenfilename(initialdir=os.path.dirname(self._preamble.get()),
                                                  title="Select preamble file",
                                                  filetypes=(("LaTeX files", "*.tex"), ("all files", "*.*")))
        if file_name is not None:
            self._preamble.delete(0, Tk.END)
            self._preamble.insert(Tk.END, file_name)

    def show_error_dialog(self, title, message_text, exception):

        # ToDo: Check Windows behavior!! --> -disable
        self._root.wm_attributes("-topmost", False)

        err_dialog = Tk.Toplevel(self._frame)
        err_dialog.minsize(300, 400)
        err_dialog.transient(self._frame)
        err_dialog.focus_force()
        err_dialog.grab_set()

        def add_textview(header, text):
            err_dialog_frame = Tk.Frame(err_dialog)
            err_dialog_label = Tk.Label(err_dialog_frame, text=header)
            err_dialog_label.pack(side='top', fill=Tk.X)
            err_dialog_text = Tk.Text(err_dialog_frame, height=10)
            err_dialog_text.insert(Tk.END, text)
            err_dialog_text.pack(side='left', fill=Tk.Y)
            err_dialog_scrollbar = Tk.Scrollbar(err_dialog_frame)
            err_dialog_scrollbar.pack(side='right', fill=Tk.Y)
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

        close_button = Tk.Button(err_dialog, text='OK', command=close_error_dialog)
        close_button.pack(side='top', fill='x', expand=True)


class AskTextGTKSource(AskText):
    """GTK + Source Highlighting for editing TexText objects"""

    def __init__(self, version_str, text, preamble_file, global_scale_factor, current_scale_factor, current_alignment,
                 current_texcmd, current_convert_strokes_to_path, tex_commands, gui_config):
        super(AskTextGTKSource, self).__init__(version_str, text, preamble_file, global_scale_factor, current_scale_factor,
                                               current_alignment, current_texcmd, current_convert_strokes_to_path,
                                               tex_commands, gui_config)
        self._preview = None  # type: Gtk.Image
        self._pixbuf = None  # type: GdkPixbuf
        self.preview_representation = "SCALE"  # type: str
        self._preview_scroll_window = None  # type: Gtk.ScrolledWindow
        self._scale_adj = None
        self._texcmd_cbox = None
        self._preview_callback = None
        self._source_view = None

        self.buffer_actions = [
            ('Open', Gtk.STOCK_OPEN, '_Open', '<control>O', 'Open a file', self.open_file_cb)
        ]

        if TOOLKIT == GTKSOURCEVIEW:
            self._view_actions = [
                ('FileMenu', None, '_File'),
                ('ViewMenu', None, '_View'),
                ('SettingsMenu', None, '_Settings'),
                ('NewNodeContent', None, '_New Node Content'),
                ('CloseShortcut', None, 'Close TexText _Shortcut'),
                ('TabsWidth', None, '_Tabs Width'),
            ]
        else:
            self._view_actions = [
                ('FileMenu', None, '_File'),
                ('ViewMenu', None, '_View'),
                ('SettingsMenu', None, '_Settings'),
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

        self._preview_white_background_action = [
            ('WhitePreviewBackground', None, 'White preview background', None,
             'Set preview background to white', self.on_preview_background_chagned)
        ]

        self._confirm_close_action = [
            ('ConfirmClose', None, '_Confirm Closing of Window', None,
             'Request confirmation for closing the window when text has been changed', self.confirm_close_toggled_cb)
        ]

        self._radio_actions = [
            ('TabsWidth%d' % num, None, '%d' % num, None, 'Set tabulation width to %d spaces' % num, num) for num in
            range(2, 13, 2)]

        gtksourceview_ui_additions = "" if TOOLKIT == GTK else """
          <menuitem action='ShowNumbers'/>
          <menuitem action='AutoIndent'/>
          <menuitem action='InsertSpaces'/>
          <menu action='TabsWidth'>
            %s
          </menu>
          """ % "\n".join(['<menuitem action=\'%s\'/>' % action for (action, _, _, _, _, _) in self._radio_actions])

        self._new_node_content_actions = [
            #     name of action ,   stock id,    label, accelerator,  tooltip, callback/value
            ('NewNodeContentEmpty', None, '_Empty', None, 'New node will be initialized with empty content', 0),
            ('NewNodeContentInlineMath', None, '_Inline math', None, 'New node will be initialized with $ $', 1),
            ('NewNodeContentDisplayMath', None, '_Display math', None, 'New node will be initialized with $$ $$', 2)
        ]
        new_node_content = "\n".join(
            ['<menuitem action=\'%s\'/>' % action for (action, _, _, _, _, _) in self._new_node_content_actions])

        self._close_shortcut_actions = [
            ('CloseShortcutEscape', None, '_ESC', None, 'TexText window closes when pressing ESC', 0),
            ('CloseShortcutCtrlQ', None, 'CTRL + _Q', None, 'TexText window closes when pressing CTRL + Q', 1),
            ('CloseShortcutNone', None, '_None', None, 'No shortcut for closing TexText window', 2)
        ]
        close_shortcut = "\n".join(
            ['<menuitem action=\'%s\'/>' % action for (action, _, _, _, _, _) in self._close_shortcut_actions])

        self._view_ui_description = """
        <ui>
          <menubar name='MainMenu'>
            <menu action='FileMenu'>
              <menuitem action='Open'/>
            </menu>
            <menu action='ViewMenu'>
              <menuitem action='WordWrap'/>
              {additions}
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
        """.format(additions=gtksourceview_ui_additions,
                   new_node_content=new_node_content, close_shortcut=close_shortcut)

    @staticmethod
    def open_file_cb(_, text_buffer):
        """
        Present file chooser to select a source code file
        :param text_buffer: The target text buffer to show the loaded text in
        """
        chooser = Gtk.FileChooserDialog('Open file...', None,
                                        Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            if filename:
                AskTextGTKSource.open_file(text_buffer, filename)
        chooser.destroy()

    @staticmethod
    def update_position_label(text_buffer, asktext, view):
        """
        Update the position label below the source code view
        :param (AskTextGTKSource) asktext:
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
            asktext.pos_label.set_text('char: %d, line: %d, column: %d' % (nchars, row, col + 1))
        else:
            asktext.pos_label.set_text('char: %d, line: %d' % (nchars, row))

    @staticmethod
    def load_file(text_buffer, path):
        """
        Load text from a file into a text buffer
        :param text_buffer: the GTK text buffer
        :param path: where to load the file from
        :returns: True, if successful
        """

        try:
            text = open(path).read()
        except IOError:
            print("Couldn't load file: %s", path)
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

        AskTextGTKSource.load_file(text_buffer, path)

    # Callback methods for the various menu items at the top of the window
    def numbers_toggled_cb(self, action, sourceview):
        sourceview.set_show_line_numbers(action.get_active())
        self._gui_config["line_numbers"] = action.get_active()

    def auto_indent_toggled_cb(self, action, sourceview):
        sourceview.set_auto_indent(action.get_active())
        self._gui_config["auto_indent"] = action.get_active()

    def insert_spaces_toggled_cb(self, action, sourceview):
        sourceview.set_insert_spaces_instead_of_tabs(action.get_active())
        self._gui_config["insert_spaces"] = action.get_active()

    def word_wrap_toggled_cb(self, action, sourceview):
        sourceview.set_wrap_mode(Gtk.WrapMode.WORD if action.get_active() else Gtk.WrapMode.NONE)
        self._gui_config["word_wrap"] = action.get_active()

    def on_preview_background_chagned(self, action, sourceview):
        self._gui_config["white_preview_background"] = action.get_active()

    def tabs_toggled_cb(self, action, previous_value, sourceview):
        sourceview.set_tab_width(action.get_current_value())
        self._gui_config["tab_width"] = action.get_current_value()

    def new_node_content_cb(self, action, previous_value, sourceview):
        self._gui_config["new_node_content"] = self.NEW_NODE_CONTENT[action.get_current_value()]

    def close_shortcut_cb(self, action, previous_value, sourceview):
        self._gui_config["close_shortcut"] = self.CLOSE_SHORTCUT[action.get_current_value()]
        self._cancel_button.set_tooltip_text(
            "Don't save changes ({})".format(self._close_shortcut_actions[action.get_current_value()][2]).replace(
                "_", ""))

    def confirm_close_toggled_cb(self, action, sourceview):
        self._gui_config["confirm_close"] = action.get_active()

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
        close_shortcut_value = self._gui_config.get("close_shortcut", self.DEFAULT_CLOSE_SHORTCUT)
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
            self.callback(self.text, self.preamble_file, self.global_scale_factor,
                          self.ALIGNMENT_LABELS[self._alignment_combobox.get_active()],
                          self.TEX_COMMANDS[self._texcmd_cbox.get_active()].lower(),
                          self.current_convert_strokes_to_path)
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

    def move_cursor_cb(self, text_buffer, cursoriter, mark, view):
        self.update_position_label(text_buffer, self, view)

    def window_deleted_cb(self, widget, event, view):
        if (self._gui_config.get("confirm_close", self.DEFAULT_CONFIRM_CLOSE)
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

    def update_preview(self, widget):
        """Update the preview image of the GUI using the callback it gave """
        if self._preview_callback:
            text = self._source_buffer.get_text(self._source_buffer.get_start_iter(),
                                                self._source_buffer.get_end_iter(), True)

            if isinstance(self._preamble_widget, Gtk.FileChooser):
                preamble = self._preamble_widget.get_filename()
                if not preamble:
                    preamble = ""
            else:
                preamble = self._preamble_widget.get_text()

            try:
                self._preview_callback(text, preamble, self.set_preview_image_from_file,
                                       self.TEX_COMMANDS[self._texcmd_cbox.get_active()].lower(),
                                       self._gui_config.get("white_preview_background", self.DEFAULT_PREVIEW_WHITE_BACKGROUND))
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

    def switch_preview_representation(self, widget=None, event=None):
        if event.button == 1: # left click only
            if event.type == Gdk.EventType._2BUTTON_PRESS:  # only double click
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

            desired_preview_area_height = image_height
            if image_width + scroll_bar_width >= textview_width:
                desired_preview_area_height += scroll_bar_width

            if desired_preview_area_height>max_preview_height or image_width > textview_width:
                self._preview_scroll_window.set_tooltip_text("Double click: scale to fit window")

            self._preview.set_from_pixbuf(self._pixbuf)
            self._preview.set_size_request(image_width, image_height)
            return desired_preview_area_height

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
        window.set_title('Enter LaTeX Formula - TexText {0}'.format(self.textext_version))

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
        self._scale_adj.set_value(self.scale_factor_after_loading())
        self._scale.set_tooltip_text("Change the scale of the LaTeX output")

        # We need buttons with custom labels and stock icons, so we make some
        reset_scale = self.current_scale_factor if self.current_scale_factor else self.global_scale_factor
        scale_reset_button = Gtk.Button.new_from_icon_name('edit-undo', Gtk.IconSize.BUTTON)
        scale_reset_button.set_label('Reset ({0:.3f})'.format(reset_scale))
        scale_reset_button.set_always_show_image(True)
        scale_reset_button.set_tooltip_text(
            "Set scale factor to the value this node has been created with ({0:.3f})".format(reset_scale))
        scale_reset_button.connect('clicked', self.reset_scale_factor)
        if self.text == "":
            scale_reset_button.set_sensitive(False)

        scale_global_button = Gtk.Button.new_from_icon_name('edit-copy', Gtk.IconSize.BUTTON)
        scale_global_button.set_label('As previous ({0:.3f})'.format(self.global_scale_factor))
        scale_global_button.set_always_show_image(True)
        scale_global_button.set_tooltip_text(
            "Set scale factor to the value of the previously edited node in Inkscape ({0:.3f})".format(
                self.global_scale_factor))
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
        for a in self.ALIGNMENT_LABELS:
            args = tuple(a.split(" "))
            path = os.path.join(os.path.dirname(__file__), "icons", "alignment-%s-%s.svg.png" % args)
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
        self._conv_stroke2path.set_tooltip_text("Ensures that strokes (lines, e.g. in \\sqrt, \\frac) can be easily \ncolored in Inkscape (Time consuming compilation!)")
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
        set_monospace_font(self._source_view)

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
        self._same_height_objects = [
            preamble_frame,
            texcmd_frame,
            scale_align_hbox
        ]

        self._preview_scroll_window.hide()

        # preselect menu check items
        groups = ui_manager.get_action_groups()
        # retrieve the view action group at position 0 in the list
        action_group = groups[0]
        action = action_group.get_action('WordWrap')
        action.set_active(self._gui_config.get("word_wrap", self.DEFAULT_WORDWRAP))
        new_node_content_value = self._gui_config.get("new_node_content", self.DEFAULT_NEW_NODE_CONTENT)
        action = action_group.get_action('NewNodeContent{}'.format(new_node_content_value))
        action.set_active(True)
        close_shortcut_value = self._gui_config.get("close_shortcut", self.DEFAULT_CLOSE_SHORTCUT)
        action = action_group.get_action('CloseShortcut{}'.format(close_shortcut_value))
        action.set_active(True)
        action = action_group.get_action('ConfirmClose')
        action.set_active(self._gui_config.get("confirm_close", self.DEFAULT_CONFIRM_CLOSE))
        action = action_group.get_action('WhitePreviewBackground')
        action.set_active(self._gui_config.get("white_preview_background", self.DEFAULT_PREVIEW_WHITE_BACKGROUND))
        if TOOLKIT == GTKSOURCEVIEW:
            action = action_group.get_action('ShowNumbers')
            action.set_active(self._gui_config.get("line_numbers", self.DEFAULT_SHOWLINENUMBERS))
            action = action_group.get_action('AutoIndent')
            action.set_active(self._gui_config.get("auto_indent", self.DEFAULT_AUTOINDENT))
            action = action_group.get_action('InsertSpaces')
            action.set_active(self._gui_config.get("insert_spaces", self.DEFAULT_INSERTSPACES))
            action = action_group.get_action('TabsWidth%d' % self._gui_config.get("tab_width", self.DEFAULT_TABWIDTH))
            action.set_active(True)
            self._source_view.set_tab_width(action.get_current_value())  # <- Why is this explicit call necessary ??

        if self.text=="":
            if new_node_content_value=='InlineMath':
                self.text="$$"
                self._source_buffer.set_text(self.text)
                iter = self._source_buffer.get_iter_at_offset(1)
                self._source_buffer.place_cursor(iter)
            if new_node_content_value=='DisplayMath':
                self.text = "$$$$"
                self._source_buffer.set_text(self.text)
                iter = self._source_buffer.get_iter_at_offset(2)
                self._source_buffer.place_cursor(iter)

        # Connect event callbacks
        window.connect("key-press-event", self.cb_key_press)
        text_buffer.connect('changed', self.update_position_label, self, source_view)
        window.connect('delete-event', self.window_deleted_cb, source_view)
        text_buffer.connect('mark_set', self.move_cursor_cb, source_view)

        icon_sizes = [16, 32, 64, 128]
        icon_files = [os.path.join(
            os.path.dirname(__file__),
            "icons",
            "logo-{size}x{size}.png".format(size=size))
            for size in icon_sizes]
        icons = [GdkPixbuf.Pixbuf.new_from_file(path) for path in icon_files if os.path.isfile(path)]
        window.set_icon_list(icons)

        return window

    def ask(self, callback, preview_callback=None):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", module="asktext")
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            self.callback = callback
            self._preview_callback = preview_callback

            # create first window
            with SuppressStream():  # suppress GTK Warings printed directly to stderr in C++
                window = self.create_window()
            window.set_default_size(500, 525)
            # Until commit 802d295e46877fd58842b61dbea4276372a2505d we called own normalize_ui_row_heights here with
            # bad hide/show/hide hack, see issue #114
            window.show()
            self._window = window
            self._window.set_focus(self._source_view)

            # main loop
            Gtk.main()
            return self._gui_config

    def show_error_dialog(self, title, message_text, exception):

        dialog = Gtk.Dialog(title, self._window)
        dialog.set_default_size(450, 300)
        button = dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.CLOSE)
        button.connect("clicked", lambda w, d=None: dialog.destroy())
        message_label = Gtk.Label()
        message_label.set_markup("<b>{message}</b>".format(message=message_text))
        message_label.set_justify(Gtk.Justification.LEFT )

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

            def callback(event):
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
    AskTextDefault = AskTextTK
elif TOOLKIT in (GTK, GTKSOURCEVIEW):
    AskTextDefault = AskTextGTKSource
