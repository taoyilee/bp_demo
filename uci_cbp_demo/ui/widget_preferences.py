#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import tkinter
from tkinter import ttk
from typing import TYPE_CHECKING

from uci_cbp_demo.config import config

if TYPE_CHECKING:
    from uci_cbp_demo.ui.gui import GUIView


class PreferencesView(tkinter.Toplevel):
    TITLE = "Preferences"
    MIN_WIDTH = 450
    MIN_HEIGHT = 400

    def show(self):
        self.update()
        self.deiconify()

    def hide(self):
        config.DEFAULT.data_dir = self.waveform_output_strvar.get()
        config.DEFAULT.log_dir = self.log_output_strvar.get()
        self.withdraw()

    def __init__(self, parent: "GUIView" = None):
        super(PreferencesView, self).__init__()
        self.parent = parent
        self.wm_title(self.TITLE)
        self.resizable(False, False)
        self.wm_minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.geometry('%dx%d+%d+%d' % (self.MIN_WIDTH, self.MIN_HEIGHT,
                                       self.parent.winfo_rootx() + 10, self.parent.winfo_rooty() + 10))
        tab_parent = ttk.Notebook(self)

        tab1 = ttk.Frame(tab_parent)
        tab_parent.add(tab1, text="Locations")
        tab_parent.pack(expand=1, fill='both')

        tkinter.Label(tab1, text="Waveform Output Directory", font=("Helvetica", 8),
                      justify=tkinter.LEFT).grid(row=0, sticky=tkinter.W)
        tkinter.Label(tab1, text="Log Output Directory", font=("Helvetica", 8),
                      justify=tkinter.LEFT).grid(row=1, sticky=tkinter.W)

        self.waveform_output_strvar = tkinter.StringVar()
        self.waveform_output_strvar.set(config.DEFAULT.data_dir)

        self.log_output_strvar = tkinter.StringVar()
        self.log_output_strvar.set(config.DEFAULT.log_dir)
        txtfld1 = tkinter.Entry(tab1, textvariable=self.waveform_output_strvar, bd=1, width=40)
        txtfld1.grid(row=0, column=1)

        txtfld2 = tkinter.Entry(tab1, textvariable=self.log_output_strvar, bd=1, width=40)
        txtfld2.grid(row=1, column=1)
        tab1.grid_rowconfigure("all", pad=10)

        self.protocol("WM_DELETE_WINDOW", self.hide)


class PreferencesViewSingleton:
    instance: "PreferencesView" = None

    def __init__(self, parent):
        if not PreferencesViewSingleton.instance:
            PreferencesViewSingleton.instance = PreferencesView(parent)
        else:
            PreferencesViewSingleton.instance.show()
