debugValues = True
debugText = r"""
$$
F(x,y)=0 ~~\mbox{and}~~
\left| \begin{array}{ccc}
  F''_{xx} & F''_{xy} &  F'_x \\
  F''_{yx} & F''_{yy} &  F'_y \\
  F'_x     & F'_y     & 0
  \end{array}\right| = 0
$$
"""

WINDOW_TITLE = "Enter LaTeX Formula - TexText"

GTKSOURCEVIEW = "GTK Source View"
GTK = "GTK"
TK = "TK"

TOOLKIT = None

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
        pass


class AskerFactory(object):
    def asker(self, text, preamble_file, scale_factor):
        if TOOLKIT == GTK:
            return AskTextGTK(text, preamble_file, scale_factor)
        elif TOOLKIT == TK:
            return AskTextTK(text, preamble_file, scale_factor)
        elif TOOLKIT == GTKSOURCEVIEW:
            return AskTextGTKSource(text, preamble_file, scale_factor)
        else:
            raise RuntimeError("Neither pygtk nor Tkinter is available!")


class AskText(object):
    """GUI for editing TexText objects"""

    def __init__(self, text, preamble_file, scale_factor):
        self.text = debugText if debugValues else text
        self.callback = None
        self.scale_factor = scale_factor
        self.preamble_file = preamble_file
        self._preamble = None
        self._scale = None
        self._textBox = None
        self._ok_button = None
        self._cancel_button = None
        self._frame = None
        self._window = None

    def ask(self, callback):
        pass

    def cb_cancel(self, widget=None, data=None):
        raise SystemExit(1)

    def cb_ok(self, widget=None, data=None):
        pass


class AskTextTK(AskText):
    """GUI for editing TexText objects"""

    def ask(self, callback):
        self.callback = callback

        root = Tk.Tk()

        self._frame = Tk.Frame(root)
        self._frame.pack()

        box = Tk.Frame(self._frame)
        label = Tk.Label(box, text="Preamble file:")
        label.pack(pady=2, padx=5, side="left", anchor="w")
        self._preamble = Tk.Entry(box)
        self._preamble.pack(expand=True, fill="x", pady=2, padx=5, side="right")
        self._preamble.insert(Tk.END, self.preamble_file)
        box.pack(fill="x", expand=True)

        box = Tk.Frame(self._frame)
        label = Tk.Label(box, text="Scale factor:")
        label.pack(pady=2, padx=5, side="left", anchor="w")
        self._scale = Tk.Scale(box, orient="horizontal", from_=0.1, to=10, resolution=0.1)
        self._scale.pack(expand=True, fill="x", pady=2, padx=5, anchor="e")
        if self.scale_factor is not None:
            self._scale.set(self.scale_factor)
        else:
            self._scale.set(1.0)
        box.pack(fill="x", expand=True)

        label = Tk.Label(self._frame, text="Text:")
        label.pack(pady=2, padx=5, anchor="w")

        self._textBox = Tk.Text(self._frame)
        self._textBox.pack(expand=True, fill="both", pady=5, padx=5)
        self._textBox.insert(Tk.END, self.text)

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
        self.text = self._textBox.get(1.0, Tk.END)
        self.preamble_file = self._preamble.get()
        if self.scale_factor is not None:
            self.scale_factor = self._scale.get()
        self._frame.quit()


import os
import traceback


class AskTextGTK(AskText):
    """GUI for editing TexText objects"""

    def __init__(self, text, preamble_file, scale_factor):
        super(AskTextGTK, self).__init__(text, preamble_file, scale_factor)
        self._scale_adj = None
        self._scale = None

    def ask(self, callback):
        self.callback = callback

        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title(WINDOW_TITLE)
        window.set_default_size(600, 400)

        label1 = gtk.Label(u"Preamble file:")
        label2 = gtk.Label(u"Scale factor:")
        label3 = gtk.Label(u"Text:")

        if hasattr(gtk, 'FileChooserButton'):
            self._preamble = gtk.FileChooserButton("...")
            if os.path.exists(self.preamble_file):
                self._preamble.set_filename(self.preamble_file)
            self._preamble.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        else:
            self._preamble = gtk.Entry()
            self._preamble.set_text(self.preamble_file)

        self._scale_adj = gtk.Adjustment(lower=0.01, upper=100,
                                         step_incr=0.1, page_incr=1)
        self._scale = gtk.SpinButton(self._scale_adj, digits=2)

        if self.scale_factor is not None:
            self._scale_adj.set_value(self.scale_factor)
        else:
            self._scale_adj.set_value(1.0)
            self._scale.set_sensitive(False)

        self._textBox = gtk.TextView()
        self._textBox.get_buffer().set_text(self.text)

        scroll_window = gtk.ScrolledWindow()
        scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll_window.set_shadow_type(gtk.SHADOW_IN)
        scroll_window.add(self._textBox)

        self._ok_button = gtk.Button(stock=gtk.STOCK_SAVE)
        self._cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)

        # layout
        table = gtk.Table(3, 2, False)
        table.attach(label1, 0, 1, 0, 1, xoptions=0, yoptions=gtk.FILL)
        table.attach(self._preamble, 1, 2, 0, 1, yoptions=gtk.FILL)
        table.attach(label2, 0, 1, 1, 2, xoptions=0, yoptions=gtk.FILL)
        table.attach(self._scale, 1, 2, 1, 2, yoptions=gtk.FILL)
        table.attach(label3, 0, 1, 2, 3, xoptions=0, yoptions=gtk.FILL)
        table.attach(scroll_window, 1, 2, 2, 3)

        vbox = gtk.VBox(False, 5)
        vbox.pack_start(table)

        hbox = gtk.HButtonBox()
        hbox.add(self._ok_button)
        hbox.add(self._cancel_button)
        hbox.set_layout(gtk.BUTTONBOX_SPREAD)

        vbox.pack_end(hbox, expand=False, fill=False)

        window.add(vbox)

        # signals
        window.connect("delete-event", self.cb_delete_event)
        window.connect("key-press-event", self.cb_key_press)
        self._ok_button.connect("clicked", self.cb_ok)
        self._cancel_button.connect("clicked", self.cb_cancel)

        # show
        window.show_all()
        self._textBox.grab_focus()

        # run
        self._window = window
        gtk.main()

        return self.text, self.preamble_file, self.scale_factor

    def cb_delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def cb_key_press(self, widget, event, data=None):
        # ctrl+return clicks the ok button
        if gtk.gdk.keyval_name(event.keyval) == 'Return' and gtk.gdk.CONTROL_MASK & event.state:
            self._ok_button.clicked()
            return True
        return False

    def cb_ok(self, widget=None, data=None):
        buf = self._textBox.get_buffer()
        self.text = buf.get_text(buf.get_start_iter(),
                                 buf.get_end_iter())
        if isinstance(self._preamble, gtk.FileChooser):
            self.preamble_file = self._preamble.get_filename()
            if not self.preamble_file:
                self.preamble_file = ""
        else:
            self.preamble_file = self._preamble.get_text()

        if self.scale_factor is not None:
            self.scale_factor = self._scale_adj.get_value()

        try:
            self.callback(self.text, self.preamble_file, self.scale_factor)
        except StandardError, error:
            error_message = traceback.format_exc()
            dialog = gtk.Dialog("Textext Error", self._window,
                                gtk.DIALOG_MODAL)
            dialog.set_default_size(600, 400)
            button = dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)
            button.connect("clicked", lambda w, d=None: dialog.destroy())
            message = gtk.Label()
            message.set_markup("<b>Error occurred while converting text from Latex to SVG:</b>")

            scroll_window = gtk.ScrolledWindow()
            scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            scroll_window.set_shadow_type(gtk.SHADOW_IN)
            text_view = gtk.TextView()
            text_view.set_editable(False)
            text_view.get_buffer().set_text(error_message)
            scroll_window.add(text_view)

            dialog.vbox.pack_start(message, expand=False, fill=True)
            dialog.vbox.pack_start(scroll_window, expand=True, fill=True)
            dialog.show_all()
            dialog.run()
            return False

        gtk.main_quit()
        return False


import gtksourceview2
import pango


class AskTextGTKSource(AskText):
    def __init__(self, text, preamble_file, scale_factor):
        super(AskTextGTKSource, self).__init__(text, preamble_file, scale_factor)

    # ---------- Error dialog
    def error_dialog(self, parent, msg):
        dialog = gtk.MessageDialog(parent,
                                   gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,
                                   msg)
        dialog.run()
        dialog.destroy()

    # ---------- File loading
    def load_file(self, text_buffer, path):
        text_buffer.begin_not_undoable_action()
        try:
            text = open(path).read()
        except IOError:
            print("Couldn't load file: %s", path)
            return False
        text_buffer.set_text(text)
        text_buffer.set_data('filename', path)
        text_buffer.end_not_undoable_action()

        text_buffer.set_modified(False)
        text_buffer.place_cursor(text_buffer.get_start_iter())
        return True

    # ---------- Buffer creation
    def open_file(self, text_buffer, filename):
        # get the new language for the file mimetype
        manager = text_buffer.get_data('languages-manager')

        if os.path.isabs(filename):
            path = filename
        else:
            path = os.path.abspath(filename)

        language = manager.guess_language(filename)
        if language:
            text_buffer.set_highlight_syntax(True)
            text_buffer.set_language(language)
        else:
            print 'No language found for file "%s"' % filename
            text_buffer.set_highlight_syntax(False)

            self.load_file(text_buffer, path)

    # ---------- Action callbacks
    def numbers_toggled_cb(self, action, sourceview=None):
        if sourceview:
            sourceview.set_show_line_numbers(action.get_active())

    def auto_indent_toggled_cb(self, action, sourceview=None):
        if sourceview:
            sourceview.set_auto_indent(action.get_active())

    def insert_spaces_toggled_cb(self, action, sourceview=None):
        if sourceview:
            sourceview.set_insert_spaces_instead_of_tabs(action.get_active())

    def tabs_toggled_cb(self, action, action2, sourceview=None):
        if sourceview:
            sourceview.set_tab_width(action.get_current_value())

    def cb_key_press(self, widget, event, data=None):
        # ctrl+return clicks the ok button
        if gtk.gdk.keyval_name(event.keyval) == 'Return' and gtk.gdk.CONTROL_MASK & event.state:
            self._ok_button.clicked()
            return True
        return False

    def cb_ok(self, widget=None, data=None):
        text_buffer = self._textBox
        self.text = text_buffer.get_text(text_buffer.get_start_iter(),
                                         text_buffer.get_end_iter())

        if isinstance(self._preamble, gtk.FileChooser):
            self.preamble_file = self._preamble.get_filename()
            if not self.preamble_file:
                self.preamble_file = ""
        else:
            self.preamble_file = self._preamble.get_text()

        if self.scale_factor is not None:
            self.scale_factor = self._scale_adj.get_value()

        try:
            self.callback(self.text, self.preamble_file, self.scale_factor)
        except StandardError, error:
            self.error_dialog(self._window,
                              "Textext Error. Error occurred while converting text from Latex to SVG. \n\n%s", error)
            return False

        gtk.main_quit()
        return False

    # ---------- Buffer action callbacks
    def open_file_cb(self, action, text_buffer):
        chooser = gtk.FileChooserDialog('Open file...', None,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            if filename:
                self.open_file(text_buffer, filename)
        chooser.destroy()

    def update_cursor_position(self, text_buffer, view):
        tabwidth = view.get_tab_width()
        pos_label = view.get_data('pos_label')
        iterator = text_buffer.get_iter_at_mark(text_buffer.get_insert())
        nchars = iterator.get_offset()
        row = iterator.get_line() + 1
        start = iterator.copy()
        start.set_line_offset(0)
        col = 0
        while start.compare(iterator) < 0:
            if start.get_char() == '\t':
                col += tabwidth - col % tabwidth
            else:
                col += 1
            start.forward_char()
        pos_label.set_text('char: %d, line: %d, column: %d' % (nchars, row, col + 1))

    def move_cursor_cb(self, text_buffer, cursoriter, mark, view):
        self.update_cursor_position(text_buffer, view)

    def window_deleted_cb(self, widget, event, view):
        gtk.main_quit()
        return True

    # ---------- Actions & UI definition
    buffer_actions = [
        ('Open', gtk.STOCK_OPEN, '_Open', '<control>O', 'Open a file', open_file_cb),
        ('Quit', gtk.STOCK_QUIT, '_Quit', '<control>Q', 'Exit the application', gtk.main_quit)
    ]

    view_actions = [
        ('FileMenu', None, '_File'),
        ('ViewMenu', None, '_View'),
        ('TabsWidth', None, '_Tabs Width')
    ]

    toggle_actions = [
        ('ShowNumbers', None, 'Show _Line Numbers', None, 'Toggle visibility of line numbers in the left margin',
         numbers_toggled_cb, False),
        ('AutoIndent', None, 'Enable _Auto Indent', None, 'Toggle automatic auto indentation of text',
         auto_indent_toggled_cb, False),
        ('InsertSpaces', None, 'Insert _Spaces Instead of Tabs', None,
         'Whether to insert space characters when inserting tabulations', insert_spaces_toggled_cb, False)
    ]

    radio_actions = [
        ('TabsWidth2', None, '2', None, 'Set tabulation width to 4 spaces', 2),
        ('TabsWidth4', None, '4', None, 'Set tabulation width to 4 spaces', 4),
        ('TabsWidth6', None, '6', None, 'Set tabulation width to 6 spaces', 6),
        ('TabsWidth8', None, '8', None, 'Set tabulation width to 8 spaces', 8),
        ('TabsWidth10', None, '10', None, 'Set tabulation width to 10 spaces', 10),
        ('TabsWidth12', None, '12', None, 'Set tabulation width to 12 spaces', 12)
    ]

    view_ui_description = """
    <ui>
      <menubar name='MainMenu'>
        <menu action='FileMenu'>
          <placeholder name="FileMenuAdditions"/>
          <separator/>
        </menu>
        <menu action='ViewMenu'>
          <separator/>
          <menuitem action='ShowNumbers'/>
          <separator/>
          <menuitem action='AutoIndent'/>
          <menuitem action='InsertSpaces'/>
          <separator/>
          <menu action='TabsWidth'>
            <menuitem action='TabsWidth4'/>
            <menuitem action='TabsWidth6'/>
            <menuitem action='TabsWidth8'/>
            <menuitem action='TabsWidth10'/>
            <menuitem action='TabsWidth12'/>
          </menu>
        </menu>
      </menubar>
    </ui>
    """

    buffer_ui_description = """
    <ui>
      <menubar name='MainMenu'>
        <menu action='FileMenu'>
          <placeholder name="FileMenuAdditions">
            <menuitem action='Open'/>
          </placeholder>
          <separator/>
          <menuitem action='Quit'/>
        </menu>
        <menu action='ViewMenu'>
        </menu>
      </menubar>
    </ui>
    """

    # ---------- create view window
    def create_buttons(self):
        layout = gtk.BUTTONBOX_EDGE
        spacing = 0

        button_box = gtk.HButtonBox()

        button_box.set_border_width(5)
        button_box.set_layout(layout)
        button_box.set_spacing(spacing)

        self._cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        button_box.add(self._cancel_button)

        self._ok_button = gtk.Button(stock=gtk.STOCK_SAVE)
        button_box.add(self._ok_button)

        self._cancel_button.connect("clicked", self.cb_cancel)
        self._ok_button.connect("clicked", self.cb_ok)

        return button_box

    def create_view_window(self, text_buffer, parent_view=None):
        # window
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_border_width(0)
        window.set_title('Enter LaTeX Formula - TexText')

        # view
        source_view = gtksourceview2.View(text_buffer)
        text_buffer.connect('changed', self.update_cursor_position, source_view)
        window.connect('delete-event', self.window_deleted_cb, source_view)

        # action group and UI manager
        action_group = gtk.ActionGroup('ViewActions')
        action_group.add_actions(self.view_actions, source_view)
        action_group.add_toggle_actions(self.toggle_actions, source_view)
        action_group.add_radio_actions(self.radio_actions, -1, self.tabs_toggled_cb, source_view)

        ui_manager = gtk.UIManager()
        ui_manager.insert_action_group(action_group, 0)
        # save a reference to the ui manager in the window for later use
        window.set_data('ui_manager', ui_manager)
        accel_group = ui_manager.get_accel_group()
        window.add_accel_group(accel_group)
        ui_manager.add_ui_from_string(self.view_ui_description)

        # misc widgets
        vbox = gtk.VBox(0, False)
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_IN)
        pos_label = gtk.Label('Position')
        source_view.set_data('pos_label', pos_label)
        menu = ui_manager.get_widget('/MainMenu')

        # layout widgets
        window.add(vbox)
        vbox.pack_start(menu, False, False, 0)

        if hasattr(gtk, 'FileChooserButton'):
            self._preamble = gtk.FileChooserButton("...")
            if os.path.exists(self.preamble_file):
                self._preamble.set_filename(self.preamble_file)
            self._preamble.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        else:
            self._preamble = gtk.Entry()
            self._preamble.set_text(self.preamble_file)

        preamble_box = gtk.HBox(homogeneous=False, spacing=2)
        preamble_label = gtk.Label("Preamble File")
        preamble_box.pack_start(preamble_label, False, False, 2)
        preamble_box.pack_start(self._preamble, True, True, 2)
        vbox.pack_start(preamble_box, False, False, 0)

        scale_box = gtk.HBox(homogeneous=False, spacing=2)
        scale_label = gtk.Label("Scale Factor")
        scale_box.pack_start(scale_label, False, False, 2)
        self._scale_adj = gtk.Adjustment(lower=0.01, upper=100,
                                         step_incr=0.1, page_incr=1)
        self._scale = gtk.HScale(self._scale_adj)
        self._scale.set_digits(2)
        scale_box.pack_start(self._scale, True, True, 2)
        vbox.pack_start(scale_box, False, False, 0)

        vbox.pack_start(sw, True, True, 0)
        sw.add(source_view)
        vbox.pack_start(pos_label, False, False, 0)
        vbox.pack_start(self.create_buttons(), False, False, 0)

        # set monospace font
        font_desc = pango.FontDescription('monospace 11')
        if font_desc:
            source_view.modify_font(font_desc)

        # change view attributes to match those of sourceview
        if parent_view:
            action = action_group.get_action('ShowNumbers')
            action.set_active(parent_view.get_show_line_numbers())
            action = action_group.get_action('AutoIndent')
            action.set_active(parent_view.get_auto_indent())
            action = action_group.get_action('InsertSpaces')
            action.set_active(parent_view.get_insert_spaces_instead_of_tabs())
            action = action_group.get_action('TabsWidth%d' % parent_view.get_tab_width())
            if action:
                action.set_active(True)

        vbox.show_all()

        return window

    # ---------- Create main window
    def create_main_window(self, text_buffer):
        window = self.create_view_window(text_buffer)
        ui_manager = window.get_data('ui_manager')

        # buffer action group
        action_group = gtk.ActionGroup('BufferActions')
        action_group.add_actions(self.buffer_actions, text_buffer)
        ui_manager.insert_action_group(action_group, 1)
        # merge buffer ui
        ui_manager.add_ui_from_string(self.buffer_ui_description)

        # preselect menu check items
        groups = ui_manager.get_action_groups()
        # retrieve the view action group at position 0 in the list
        action_group = groups[0]
        action = action_group.get_action('ShowNumbers')
        action.set_active(True)
        action = action_group.get_action('AutoIndent')
        action.set_active(True)
        action = action_group.get_action('InsertSpaces')
        action.set_active(True)
        action = action_group.get_action('TabsWidth8')
        action.set_active(True)

        window.connect("key-press-event", self.cb_key_press)

        return window

    def ask(self, callback):
        self.callback = callback

        lm = gtksourceview2.LanguageManager()
        text_buffer = gtksourceview2.Buffer()

        if debugValues:
            text_buffer.set_text(debugText)

        # set LaTeX as highlighting language, so that pasted text is also highlighted as such
        latex_language = lm.get_language("latex")
        text_buffer.set_language(latex_language)

        text_buffer.set_data('languages-manager', lm)

        # create first window
        window = self.create_main_window(text_buffer)
        window.set_default_size(500, 500)
        window.show()

        # main loop
        self._window = window
        self._textBox = text_buffer
        gtk.main()
        return self.text, self.preamble_file, self.scale_factor