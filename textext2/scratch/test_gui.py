import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class TextextGui:

    name = "textext_gui"

    def on_btn_preview_clicked(self, widget=None):
        self.print_something("JCW")

    def on_btn_execute_clicked(self, widget=None):
        pass

    def on_btn_cancel_clicked(self, widget=None):
        pass

    def on_btn_scalereset_clicked(self, widget=None):
        pass

    def on_btn_scale_previous_clicked(self, widget=None):
        pass

    def on_btn_preamble_open_clicked(self, widget=None):
        pass

    def on_btn_preamble_saveas_clicked(self, widget=None):
        pass

    def on_btn_preamble_save_clicked(self, widget=None):
        pass

    def on_win_main_destroy(self, widget=None):
        Gtk.main_quit()

    def print_something(self, text):
        print("Hallo Welt: {0}".format(text))


builder = Gtk.Builder()
builder.add_from_file("textext_gui.ui")
builder.connect_signals(TextextGui())

window = builder.get_object("textext_gui")
window.show_all()

Gtk.main()
