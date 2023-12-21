__version__ = "2.0"
__pkgname__ = "textext"

import os
import warnings
warnings.filterwarnings("ignore")

import inkex
from inkex.gui import GtkApp, Window


class TextextGui(Window):

    name = "textext_gui"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_btn_preview_clicked(self, widget=None):
        print("Hallo")

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
        pass


class TexTextApp(GtkApp):

    glade_dir = os.path.join(os.path.dirname(__file__))
    app_name = "textext"
    windows = [TextextGui]


class TexText(inkex.EffectExtension):

    def effect(self):
        TexTextApp(start_loop=True)


if __name__ == "__main__":
    TexText().run()
