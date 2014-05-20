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
try:
    import pygtk

    pygtk.require('2.0')

    import gtk

    TOOLKIT = GTK
except ImportError:
    pass

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
        self._button = None
        self._cancel = None
        self._frame = None

    def ask(self, callback):
        pass

    def cb_cancel(self):
        raise SystemExit(1)

    def cb_ok(self):
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
        self._button = Tk.Button(box, text="OK", command=self.cb_ok)
        self._button.pack(ipadx=30, ipady=4, pady=5, padx=5, side="left")

        self._cancel = Tk.Button(box, text="Cancel", command=self.cb_cancel)
        self._cancel.pack(ipadx=30, ipady=4, pady=5, padx=5, side="right")

        box.pack(expand=False)

        root.mainloop()

        self.callback(self.text, self.preamble_file, self.scale_factor)
        return self.text, self.preamble_file, self.scale_factor

    def cb_ok(self):
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
        self._okButton = None
        self._cancelButton = None
        self._window = None

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

        self._okButton = gtk.Button(stock=gtk.STOCK_OK)
        self._cancelButton = gtk.Button(stock=gtk.STOCK_CANCEL)

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
        hbox.add(self._okButton)
        hbox.add(self._cancelButton)
        hbox.set_layout(gtk.BUTTONBOX_SPREAD)

        vbox.pack_end(hbox, expand=False, fill=False)

        window.add(vbox)

        # signals
        window.connect("delete-event", self.cb_delete_event)
        window.connect("key-press-event", self.cb_key_press)
        self._okButton.connect("clicked", self.cb_ok)
        self._cancelButton.connect("clicked", self.cb_cancel)

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
            self._okButton.clicked()
            return True
        return False

    def cb_cancel(self, widget, data=None):
        super(AskTextGTK, self).cb_cancel()

    def cb_ok(self, widget, data=None):
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


class AskTextGTKSource(AskText):
    pass