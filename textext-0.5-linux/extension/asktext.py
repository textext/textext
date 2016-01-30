"""
:Author: Pauli Virtanen <pav@iki.fi>
:Date: 2008-04-26
:Author: Pit Garbe <piiit@gmx.de>
:Date: 2014-02-03
:License: BSD

This is the GUI part of TexText, handling several more or less sophisticated dialog windows
 depending on the installed tools.

Its used uniformly from textext.py via the factory (AskerFactory) and only the "ask" method is called.
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

# unfortunately, with Inkscape being 32bit on OSX, I couldn't get GTKSourceView to work, yet

# Try GTK first
#   If successful, try GTKSourceView (bonus points!)
#   If unsuccessful, try TK
#   When not even TK could be imported, abort with error message
try:
    import pygtk

    pygtk.require('2.0')
    import gtk

    try:
        import gtksourceview2

        TOOLKIT = GTKSOURCEVIEW
    except ImportError:
        TOOLKIT = GTK

except ImportError:
    try:
        import Tkinter as Tk

        TOOLKIT = TK
    except ImportError:
        raise RuntimeError("Neither pygtk nor Tkinter is available!")


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


def error_dialog(parent, title, message, detailed_message=None):
    """
    Present an error dialog

    :param title: Error title text
    :param message: Message text
    :param parent: The parent window
    :param detailed_message: Detailed message text, can have HTML
    """

    dialog = gtk.Dialog(title, parent, gtk.DIALOG_MODAL)
    dialog.set_default_size(400, 300)
    button = dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)
    button.connect("clicked", lambda w, d=None: dialog.destroy())
    message_label = gtk.Label()
    message_label.set_markup("<b>{message}</b>".format(message=message))
    message_label.set_justify(gtk.JUSTIFY_LEFT)

    if not detailed_message:
        detailed_message = "For details, please refer to the Inkscape error message that appears when you " \
                           "close the TexText window."

    scroll_window = gtk.ScrolledWindow()
    scroll_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
    scroll_window.set_shadow_type(gtk.SHADOW_IN)
    text_view = gtk.TextView()
    text_view.set_editable(False)
    text_view.set_left_margin(5)
    text_view.set_right_margin(5)
    text_view.set_wrap_mode(gtk.WRAP_WORD)
    text_view.get_buffer().set_text(detailed_message)
    scroll_window.add(text_view)

    dialog.vbox.pack_start(message_label, expand=False, fill=True, padding=5)
    dialog.vbox.pack_start(scroll_window, expand=True, fill=True, padding=5)
    dialog.show_all()
    dialog.run()


class AskerFactory(object):
    def asker(self, text, preamble_file, scale_factor):
        """
        Return the best possible GUI variant depending on the installed components
        :param text: Prefilled text
        :param preamble_file: Preamble file path
        :param scale_factor: A scale factor (0.1 to 10)
        :return: an instance of AskText
        """
        if TOOLKIT == TK:
            return AskTextTK(text, preamble_file, scale_factor)
        elif TOOLKIT in (GTK, GTKSOURCEVIEW):
            return AskTextGTKSource(text, preamble_file, scale_factor)


class AskText(object):
    """GUI for editing TexText objects"""

    def __init__(self, text, preamble_file, scale_factor):
        if len(text) > 0:
            self.text = text
        else:
            if DEBUG:
                self.text = debug_text
            else:
                self.text = ""

        self.callback = None
        self.scale_factor = scale_factor
        self.preamble_file = preamble_file
        self._preamble_widget = None
        self._scale = None
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
        pass

    def cb_cancel(self, widget=None, data=None):
        """Callback for Cancel button"""
        raise SystemExit(1)

    def cb_ok(self, widget=None, data=None):
        """Callback for OK / Save button"""
        pass


if TOOLKIT == TK:
    class AskTextTK(AskText):
        """TK GUI for editing TexText objects"""

        def __init__(self, text, preamble_file, scale_factor):
            super(AskTextTK, self).__init__(text, preamble_file, scale_factor)
            self._frame = None

        def ask(self, callback, preview_callback=None):
            self.callback = callback

            root = Tk.Tk()

            self._frame = Tk.Frame(root)
            self._frame.pack()

            box = Tk.Frame(self._frame)
            label = Tk.Label(box, text="Preamble file:")
            label.pack(pady=2, padx=5, side="left", anchor="w")
            self._preamble = Tk.Entry(box)
            self._preamble.pack(expand=True, fill="x", pady=5, padx=5, side="right")
            self._preamble.insert(Tk.END, self.preamble_file)
            box.pack(fill="x", expand=True)

            box = Tk.Frame(self._frame)
            label = Tk.Label(box, text="Scale factor:")
            label.pack(pady=2, padx=5, side="left", anchor="w")
            self._scale = Tk.Scale(box, orient="horizontal", from_=0.1, to=10, resolution=0.1)
            self._scale.pack(expand=True, fill="x", pady=5, padx=5, anchor="e")
            if self.scale_factor is not None:
                self._scale.set(self.scale_factor)
            else:
                self._scale.set(1.0)
            box.pack(fill="x", expand=True)

            label = Tk.Label(self._frame, text="Text:")
            label.pack(pady=2, padx=5, anchor="w")

            self._text_box = Tk.Text(self._frame)
            self._text_box.pack(expand=True, fill="both", pady=5, padx=5)
            self._text_box.insert(Tk.END, self.text)

            box = Tk.Frame(self._frame)
            self._ok_button = Tk.Button(box, text="OK", command=self.cb_ok)
            self._ok_button.pack(ipadx=30, ipady=4, pady=5, padx=5, side="left")

            self._cancel = Tk.Button(box, text="Cancel", command=self.cb_cancel)
            self._cancel.pack(ipadx=30, ipady=4, pady=5, padx=5, side="right")

            box.pack(expand=False)

            root.mainloop()

            self.callback(self.text, self.preamble_file, self.scale_factor)
            return self.text, self.preamble_file, self.scale_factor

        def cb_ok(self, widget=None, data=None):
            self.text = self._text_box.get(1.0, Tk.END)
            self.preamble_file = self._preamble.get()
            if self.scale_factor is not None:
                self.scale_factor = self._scale.get()
            self._frame.quit()

if TOOLKIT in (GTK, GTKSOURCEVIEW):
    class AskTextGTKSource(AskText):
        """GTK + Source Highlighting for editing TexText objects"""

        def __init__(self, text, preamble_file, scale_factor):
            super(AskTextGTKSource, self).__init__(text, preamble_file, scale_factor)
            self._preview = None
            self._scale_adj = None
            self._preview_callback = None
            self._source_view = None

            self.buffer_actions = [
                ('Open', gtk.STOCK_OPEN, '_Open', '<control>O', 'Open a file', self.open_file_cb)
            ]

            if TOOLKIT == GTKSOURCEVIEW:
                self._view_actions = [
                    ('FileMenu', None, '_File'),
                    ('ViewMenu', None, '_View'),
                    ('TabsWidth', None, '_Tabs Width')
                ]
            else:
                self._view_actions = [
                    ('FileMenu', None, '_File'),
                ]

            self._toggle_actions = [
                (
                    'ShowNumbers', None, 'Show _Line Numbers', None,
                    'Toggle visibility of line numbers in the left margin', self.numbers_toggled_cb, False),
                ('AutoIndent', None, 'Enable _Auto Indent', None, 'Toggle automatic auto indentation of text',
                 self.auto_indent_toggled_cb, False),
                ('InsertSpaces', None, 'Insert _Spaces Instead of Tabs', None,
                 'Whether to insert space characters when inserting tabulations', self.insert_spaces_toggled_cb, False)
            ]

            self._radio_actions = [
                ('TabsWidth2', None, '2', None, 'Set tabulation width to 4 spaces', 2),
                ('TabsWidth4', None, '4', None, 'Set tabulation width to 4 spaces', 4),
                ('TabsWidth6', None, '6', None, 'Set tabulation width to 6 spaces', 6),
                ('TabsWidth8', None, '8', None, 'Set tabulation width to 8 spaces', 8),
                ('TabsWidth10', None, '10', None, 'Set tabulation width to 10 spaces', 10),
                ('TabsWidth12', None, '12', None, 'Set tabulation width to 12 spaces', 12)
            ]

            gtksourceview_ui_additions = "" if TOOLKIT == GTK else """
            <menu action='ViewMenu'>
              <menuitem action='ShowNumbers'/>
              <menuitem action='AutoIndent'/>
              <menuitem action='InsertSpaces'/>
              <menu action='TabsWidth'>
                <menuitem action='TabsWidth2'/>
                <menuitem action='TabsWidth4'/>
                <menuitem action='TabsWidth6'/>
                <menuitem action='TabsWidth8'/>
                <menuitem action='TabsWidth10'/>
                <menuitem action='TabsWidth12'/>
              </menu>
            </menu>
            """

            self._view_ui_description = """
            <ui>
              <menubar name='MainMenu'>
                <menu action='FileMenu'>
                  <menuitem action='Open'/>
                </menu>
                {additions}
              </menubar>
            </ui>
            """.format(additions=gtksourceview_ui_additions)

        @staticmethod
        def open_file_cb(unused, text_buffer):
            """
            Present file chooser to select a source code file
            :param unused: ignored parameter
            :param text_buffer: The target text buffer to show the loaded text in
            """
            chooser = gtk.FileChooserDialog('Open file...', None,
                                            gtk.FILE_CHOOSER_ACTION_OPEN,
                                            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                             gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            response = chooser.run()
            if response == gtk.RESPONSE_OK:
                filename = chooser.get_filename()
                if filename:
                    AskTextGTKSource.open_file(text_buffer, filename)
            chooser.destroy()

        @staticmethod
        def update_position_label(text_buffer, view):
            """
            Update the position label below the source code view
            :param text_buffer:
            :param view:
            """
            pos_label = view.get_data('pos_label')
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

            pos_label.set_text('char: %d, line: %d, column: %d' % (nchars, row, col + 1))

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

            if TOOLKIT == GTKSOURCEVIEW:
                # try to figure out the (code) language of the text in the file
                manager = text_buffer.get_data('languages-manager')
                language = manager.guess_language(filename)
                if language:
                    text_buffer.set_highlight_syntax(True)
                    text_buffer.set_language(language)
                else:
                    print("No language found for file \"%s\"" % filename)
                    text_buffer.set_highlight_syntax(False)

            AskTextGTKSource.load_file(text_buffer, path)

        # Callback methods for the various menu items at the top of the window
        @staticmethod
        def numbers_toggled_cb(action, sourceview):
            sourceview.set_show_line_numbers(action.get_active())

        @staticmethod
        def auto_indent_toggled_cb(action, sourceview):
            sourceview.set_auto_indent(action.get_active())

        @staticmethod
        def insert_spaces_toggled_cb(action, sourceview):
            sourceview.set_insert_spaces_instead_of_tabs(action.get_active())

        @staticmethod
        def tabs_toggled_cb(action, previous_value, sourceview):
            sourceview.set_tab_width(action.get_current_value())

        def cb_key_press(self, widget, event, data=None):
            """
            Handle keyboard shortcuts
            :param widget:
            :param event:
            :param data:
            :return: True, if a shortcut was recognized and handled
            """
            if gtk.gdk.keyval_name(event.keyval) == 'Return' and gtk.gdk.CONTROL_MASK & event.state:
                self._ok_button.clicked()
                return True

            # escape cancels the dialog
            if gtk.gdk.keyval_name(event.keyval) == 'Escape':
                self._cancel_button.clicked()
                return True

            return False

        def cb_ok(self, widget=None, data=None):
            text_buffer = self._source_buffer
            self.text = text_buffer.get_text(text_buffer.get_start_iter(),
                                             text_buffer.get_end_iter())

            if isinstance(self._preamble_widget, gtk.FileChooser):
                self.preamble_file = self._preamble_widget.get_filename()
                if not self.preamble_file:
                    self.preamble_file = ""
            else:
                self.preamble_file = self._preamble_widget.get_text()

            if self.scale_factor is not None:
                self.scale_factor = self._scale_adj.get_value()

            try:
                self.callback(self.text, self.preamble_file, self.scale_factor)
            except StandardError, error:
                import traceback

                error_dialog(self._window,
                             "TexText Error",
                             "<b>Error occurred while converting text from Latex to SVG:</b>",
                             str(error) + "\n" + traceback.format_exc())
                return False

            gtk.main_quit()
            return False

        def move_cursor_cb(self, text_buffer, cursoriter, mark, view):
            self.update_position_label(text_buffer, view)

        def window_deleted_cb(self, widget, event, view):
            gtk.main_quit()
            return True

        def update_preview(self, widget):
            """Update the preview image of the GUI using the callback it gave """
            if self._preview_callback:
                text = self._source_buffer.get_text(self._source_buffer.get_start_iter(),
                                                    self._source_buffer.get_end_iter())

                if isinstance(self._preamble_widget, gtk.FileChooser):
                    preamble = self._preamble_widget.get_filename()
                    if not preamble:
                        preamble = ""
                else:
                    preamble = self._preamble_widget.get_text()

                try:
                    self._preview_callback(text, preamble, self.set_preview_image_from_file)
                except StandardError, error:
                    error_dialog(self._window,
                                 "TexText Error",
                                 "<b>Error occurred while generating preview:</b>",
                                 str(error))
                    return False

        def set_preview_image_from_file(self, path):
            """
            Set the preview image in the GUI, scaled to the text view's width
            :param path: the path of the image
            """
            textview_width = self._source_view.get_allocation().width

            pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            image_width = pixbuf.get_width()
            image_height = pixbuf.get_height()

            if image_width > textview_width:
                ratio = float(image_height) / image_width
                pixbuf = pixbuf.scale_simple(textview_width, int(textview_width * ratio),
                                             gtk.gdk.INTERP_BILINEAR)

            self._preview.set_from_pixbuf(pixbuf)

        # ---------- create view window
        def create_buttons(self):
            """Creates and connects the Save, Cancel and Preview buttons"""
            layout = gtk.BUTTONBOX_EDGE
            spacing = 0

            button_box = gtk.HButtonBox()

            button_box.set_border_width(5)
            button_box.set_layout(layout)
            button_box.set_spacing(spacing)

            self._cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
            self._cancel_button.set_tooltip_text("Don't save changes")
            button_box.add(self._cancel_button)

            preview_button = gtk.Button(label="Preview")
            preview_button.set_tooltip_text("You need ImageMagick for previews to work")
            button_box.add(preview_button)

            self._ok_button = gtk.Button(stock=gtk.STOCK_SAVE)
            self._ok_button.set_tooltip_text("Update or create new LaTeX output")
            button_box.add(self._ok_button)

            self._cancel_button.connect("clicked", self.cb_cancel)
            self._ok_button.connect("clicked", self.cb_ok)
            preview_button.connect('clicked', self.update_preview)

            return button_box

        def clear_preamble(self, unused=None):
            """
            Clear the preamble file setting
            """
            self.preamble_file = "default_packages.tex"
            if hasattr(gtk, 'FileChooserButton'):
                self._preamble_widget.set_filename(self.preamble_file)
            else:
                self._preamble_widget.set_text(self.preamble_file)

        # ---------- Create main window
        def create_window(self):
            """
            Set up the window with all its widgets

            :return: the created window
            """
            window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            window.set_border_width(0)
            window.set_title('Enter LaTeX Formula - TexText')

            # File chooser and Scale Adjustment
            if hasattr(gtk, 'FileChooserButton'):
                self._preamble_widget = gtk.FileChooserButton("...")
                self._preamble_widget.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
            else:
                self._preamble_widget = gtk.Entry()

            self.clear_preamble()

            preamble_delete = gtk.Button(label="Clear")
            preamble_delete.connect('clicked', self.clear_preamble)
            preamble_delete.set_tooltip_text("Clear the preamble file setting")

            preamble_box = gtk.HBox(homogeneous=False, spacing=2)
            preamble_label = gtk.Label("Preamble File")
            preamble_box.pack_start(preamble_label, False, False, 2)
            preamble_box.pack_start(self._preamble_widget, True, True, 2)
            preamble_box.pack_start(preamble_delete, False, False, 2)

            scale_box = gtk.HBox(homogeneous=False, spacing=2)
            scale_label = gtk.Label("Scale Factor")
            scale_box.pack_start(scale_label, False, False, 2)
            self._scale_adj = gtk.Adjustment(lower=0.1, upper=10, step_incr=0.1, page_incr=1)
            self._scale = gtk.HScale(self._scale_adj)
            self._scale.set_digits(1)
            self._scale_adj.set_value(self.scale_factor if self.scale_factor else 1.0)
            self._scale.set_tooltip_text("Change the scale of the LaTeX output")
            scale_box.pack_start(self._scale, True, True, 2)

            # Scrolling Window with Source View inside
            scroll_window = gtk.ScrolledWindow()
            scroll_window.set_shadow_type(gtk.SHADOW_IN)

            if TOOLKIT == GTKSOURCEVIEW:
                # Source code view
                text_buffer = gtksourceview2.Buffer()

                # set LaTeX as highlighting language, so that pasted text is also highlighted as such
                lang_manager = gtksourceview2.LanguageManager()
                latex_language = lang_manager.get_language("latex")
                text_buffer.set_language(latex_language)

                text_buffer.set_data('languages-manager', lang_manager)
                source_view = gtksourceview2.View(text_buffer)
            else:
                # normal text view
                text_buffer = gtk.TextBuffer()
                source_view = gtk.TextView(text_buffer)

            self._source_buffer = text_buffer
            self._source_view = source_view

            self._source_buffer.set_text(self.text)

            scroll_window.add(self._source_view)
            set_monospace_font(self._source_view)

            # Action group and UI manager
            ui_manager = gtk.UIManager()
            accel_group = ui_manager.get_accel_group()
            window.add_accel_group(accel_group)
            ui_manager.add_ui_from_string(self._view_ui_description)

            action_group = gtk.ActionGroup('ViewActions')
            action_group.add_actions(self._view_actions, source_view)
            action_group.add_actions(self.buffer_actions, text_buffer)
            if TOOLKIT == GTKSOURCEVIEW:
                action_group.add_toggle_actions(self._toggle_actions, source_view)
                action_group.add_radio_actions(self._radio_actions, -1, AskTextGTKSource.tabs_toggled_cb, source_view)
            ui_manager.insert_action_group(action_group, 0)

            # Menu
            menu = ui_manager.get_widget('/MainMenu')

            # Cursor position label
            pos_label = gtk.Label('Position')
            source_view.set_data('pos_label', pos_label)

            # latex preview
            self._preview = gtk.Image()

            # Vertical Layout
            vbox = gtk.VBox(0, False)
            window.add(vbox)

            vbox.pack_start(menu, False, False, 0)
            vbox.pack_start(preamble_box, False, False, 0)
            if self.scale_factor:
                vbox.pack_start(scale_box, False, False, 0)
            vbox.pack_start(scroll_window, True, True, 0)
            vbox.pack_start(pos_label, False, False, 0)
            vbox.pack_start(self._preview, False, False, 0)
            vbox.pack_start(self.create_buttons(), False, False, 0)

            vbox.show_all()

            # preselect menu check items
            if TOOLKIT == GTKSOURCEVIEW:
                groups = ui_manager.get_action_groups()
                # retrieve the view action group at position 0 in the list
                action_group = groups[0]
                action = action_group.get_action('ShowNumbers')
                action.set_active(True)
                action = action_group.get_action('AutoIndent')
                action.set_active(True)
                action = action_group.get_action('InsertSpaces')
                action.set_active(True)
                action = action_group.get_action('TabsWidth4')
                action.set_active(True)

            # Connect event callbacks
            window.connect("key-press-event", self.cb_key_press)
            text_buffer.connect('changed', self.update_position_label, source_view)
            window.connect('delete-event', self.window_deleted_cb, source_view)
            text_buffer.connect('mark_set', self.move_cursor_cb, source_view)

            return window

        def ask(self, callback, preview_callback=None):
            self.callback = callback
            self._preview_callback = preview_callback

            # create first window
            window = self.create_window()
            window.set_default_size(500, 500)
            window.show()

            self._window = window
            self._window.set_focus(self._source_view)

            # main loop
            gtk.main()
            return self.text, self.preamble_file, self.scale_factor