# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
import time
import tkinter
from multiprocessing import Pipe, Process, Queue
from queue import Empty
from tkinter import messagebox

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from scipy.interpolate import interp1d

from uci_cbp_demo.bluetooth.callbacks import CapData
from uci_cbp_demo.bluetooth.constants import TARGET_TS, DISPLAY_WINDOW, FS, FILTER_WINDOW
from uci_cbp_demo.bluetooth.sensorBoard import SensorBoard
from uci_cbp_demo.datastructures import CapIterableQueue, CapDisplayDataQueue

logger = logging.getLogger("bp_demo")


class StreamDataFilter:
    def __init__(self, history):
        self.history = history
        self.q = CapIterableQueue(history)

    @property
    def fs(self):
        return 1 / np.mean(self.q.time[1:] - self.q.time[:-1])

    def filter(self, value: "CapData"):
        self.q.put(value)

        try:
            f = interp1d(self.q.time, self.q.cap, kind="nearest")
            _t = np.arange(min(self.q.time), max(self.q.time), TARGET_TS)
            _cap = np.array([f(tt) for tt in _t])
            logger.info(f"fs: {self.fs:.3f}")
        except ValueError:
            return value

        # sos = cheby2(2, STOP_ATTEN, CUTOFF / (TARGET_FS / 2), output="sos")
        # cap_filtered = sosfiltfilt(sos, cap_interp)
        # value.cap = cap_filtered[-1]
        return value


class GUI:
    fig = None
    root = None
    canvas = None
    ax_cap1 = None
    ax_cap2 = None
    line_cap1 = None
    line_cap2 = None

    def ask_quit(self, pipe: "Pipe"):
        if messagebox.askokcancel("Quit", "You want to quit now? *sniff*"):
            pipe.send("stop")
            time.sleep(3)
            logger.info("destroying root")
            self.root.destroy()
            logger.info("finish destroying root")

    def __init__(self, datasource: "SensorBoard", a=1, b=0, ch1=True, ch2=True):
        self.a = a
        self.b = b
        self.datasource = datasource
        self.ch1 = ch1
        self.ch2 = ch2
        self.channel = int(ch1) + int(ch2)
        _display_queue_size = int(DISPLAY_WINDOW * FS / self.channel)
        self.display_queue = {"cap1": CapDisplayDataQueue(size=_display_queue_size),
                              "cap2": CapDisplayDataQueue(size=_display_queue_size)}
        _filter_queue_size = int(FILTER_WINDOW * FS / self.channel)
        self.filter = {"cap1": StreamDataFilter(history=_filter_queue_size),
                       "cap2": StreamDataFilter(history=_filter_queue_size)}

        self.init_gui()
        self.inter_process_queue = {"cap1": Queue(), "cap2": Queue()}

    def init_gui(self):
        self.root = tkinter.Tk()
        self.root.wm_title("Continuous Blood Pressure")

        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        dpi = 100
        from screeninfo import get_monitors
        logging.info(f"You have {len(get_monitors())} monitors")
        w, h = 0.9 / len(get_monitors()) * ws, 0.8 * hs
        x, y = 0, 0
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.fig = Figure(figsize=(w / dpi, (h - 20) / dpi), dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)  # A tk.DrawingArea.
        if self.channel == 2:
            self.ax_cap1 = plt.subplot2grid((2, 1), (0, 0), fig=self.fig)
            self.ax_cap2 = plt.subplot2grid((2, 1), (1, 0), fig=self.fig)
        elif self.ch1:
            self.ax_cap1 = plt.subplot2grid((1, 1), (0, 0), fig=self.fig)
        elif self.ch2:
            self.ax_cap2 = plt.subplot2grid((1, 1), (0, 0), fig=self.fig)
        t = np.linspace(0, DISPLAY_WINDOW)

        if self.ch1:
            self.line_cap1 = self.ax_cap1.plot(t, np.zeros_like(t))[0]  # type:Line2D
            self.fs_cap1 = self.ax_cap1.text(0.1, 1, f"--- Hz")
            self.ax_cap1.set_xlim(0, DISPLAY_WINDOW)
            self.ax_cap1.set_ylim(0, 8)
            self.ax_cap1.set_title("CAP CH1")
            self.ax_cap1.grid()
            self.ax_cap1.set_ylabel("Cap (pF)")
        if self.ch2:
            self.line_cap2 = self.ax_cap2.plot(t, np.zeros_like(t))[0]  # type:Line2D
            self.fs_cap2 = self.ax_cap2.text(0.1, 1, f"--- Hz")
            self.ax_cap2.set_xlim(0, DISPLAY_WINDOW)
            self.ax_cap2.set_ylim(0, 8)
            self.ax_cap2.set_title("CAP CH2")
            self.ax_cap2.grid()
            self.ax_cap2.set_ylabel("Cap (pF)")
            self.ax_cap2.set_xlabel("Time (s)")

    def _cap1_callback(self, data: "CapData", sender):
        self.inter_process_queue['cap1'].put(data)

    def _cap2_callback(self, data: "CapData", sender):
        self.inter_process_queue['cap2'].put(data)

    def _cap1_redraw(self):
        try:
            while True:
                d = self.inter_process_queue['cap1'].get(block=False)
                self.display_queue['cap1'].put(d)
        except Empty:
            pass
        time = self.display_queue['cap1'].time_plot
        cap = self.display_queue['cap1'].cap
        self.line_cap1.set_data(time, cap)

        if self.display_queue['cap1'].non_empty > 2:
            self.fs_cap1.set_text(f"{1 / np.mean(time[1:] - time[:-1]):.1f} Hz "
                                  f"({self.display_queue['cap1'].non_empty} samples)")
        try:
            self.ax_cap1.set_xlim(min(time), max(max(time), DISPLAY_WINDOW))
        except ValueError:
            pass

    def _cap2_redraw(self):
        try:
            while True:
                d = self.inter_process_queue['cap2'].get(block=False)
                self.display_queue['cap2'].put(d)
        except Empty:
            pass
        time = self.display_queue['cap2'].time_plot
        cap = self.display_queue['cap2'].cap
        self.line_cap2.set_data(time, cap)
        if self.display_queue['cap2'].non_empty > 2:
            self.fs_cap2.set_text(f"{1 / np.mean(time[1:] - time[:-1]):.1f} Hz "
                                  f"({self.display_queue['cap2'].non_empty} samples)")
        try:
            self.ax_cap2.set_xlim(min(time), max(max(time), DISPLAY_WINDOW))
        except ValueError:
            pass

    def redraw(self):
        if self.ch1:
            self._cap1_redraw()
        if self.ch2:
            self._cap2_redraw()
        self.fig.tight_layout()
        self.canvas.draw()

    def start_gui(self, pipe):
        self.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        button = tkinter.Button(master=self.root, text="Quit", command=lambda: self.ask_quit(pipe))
        button.pack(side=tkinter.BOTTOM)

        if self.channel == 2:
            self.datasource.cap1_callback = self._cap1_callback
            self.datasource.cap2_callback = self._cap2_callback
            p = Process(target=self.datasource.start_cap_notification)
        elif self.ch1:
            self.datasource.cap1_callback = self._cap1_callback
            p = Process(target=self.datasource.start_cap1_notification)
        elif self.ch2:
            self.datasource.cap2_callback = self._cap2_callback
            p = Process(target=self.datasource.start_cap2_notification)
        p.start()
        timer = self.fig.canvas.new_timer(interval=1)
        timer.add_callback(self.redraw)
        timer.start()
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.ask_quit(pipe))
        self.root.mainloop()
        logger.info("Stopping canvas update timer")
        timer.stop()
