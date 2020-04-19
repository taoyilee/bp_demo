#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import tkinter
from typing import TYPE_CHECKING

from bleak.backends.device import BLEDevice

from uci_cbp_demo.backend.bluetooth import scan
from uci_cbp_demo.logging import logger

if TYPE_CHECKING:
    from uci_cbp_demo.ui.gui import GUIView


class ScanView(tkinter.Toplevel):
    TITLE = "Available Devices"
    MIN_WIDTH = 250
    MIN_HEIGHT = 400

    def update_parent_mac(self):
        selected_mac = self.available_devices[self.listbox.curselection()[0]]  # type:BLEDevice
        selected_mac = selected_mac.address
        logger.info(f"Selected MAC: {selected_mac}")
        self.parent.model.mac_addr = selected_mac
        self.close()

    def close(self):
        ScanViewSingleton.window_close_callback()
        self.destroy()

    def __init__(self, parent: "GUIView" = None):
        super(ScanView, self).__init__()
        self.parent = parent
        self.wm_title(self.TITLE)
        self.resizable(False, False)
        self.wm_minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.geometry('%dx%d+%d+%d' % (self.MIN_WIDTH, self.MIN_HEIGHT,
                                       self.parent.winfo_rootx() + 10, self.parent.winfo_rooty() + 10))
        text1 = tkinter.Label(self, anchor=tkinter.W, justify="left", padx=20, pady=10,
                              text="Available Devices:\nDouble click to select")
        self.listbox = tkinter.Listbox(self)
        text1.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.listbox.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        self.available_devices = []
        for d in scan():
            if d.name == "DRGcBP":
                self.available_devices.append(d)
                self.listbox.insert(tkinter.END, f"{d.address} ({d.name})")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.listbox.bind('<Double-Button-1>', lambda x: self.update_parent_mac())


class ScanViewSingleton:
    instance = None

    @classmethod
    def window_close_callback(cls):
        cls.instance = None

    def __init__(self, parent):
        if not ScanViewSingleton.instance:
            ScanViewSingleton.instance = ScanView(parent)
