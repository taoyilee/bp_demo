#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import logging
import time
import tkinter
from multiprocessing import Pipe
from queue import Empty
from tkinter import messagebox, DISABLED, ACTIVE

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure

from uci_cbp_demo.bluetooth import SensorBoard
from uci_cbp_demo.bluetooth.constants import DISPLAY_WINDOW
from uci_cbp_demo.datastructures import CapDisplayDataQueue, IMUDisplayDataQueue

logger = logging.getLogger("bp_demo")


class GUI:
    fig = None
    root = None
    canvas = None
    ax_cap1 = None
    ax_cap2 = None
    line_cap1 = None
    line_cap2 = None

    def send_start(self, pipe: "Pipe"):
        logger.info("Starting canvas update timer")
        self.timer.start()
        pipe.send(("CONNECT", None))
        self.button_connect.configure(state=DISABLED)
        self.button_start.configure(state=DISABLED)
        self.button_pause.configure(state=ACTIVE)

    def send_pause(self, pipe: "Pipe"):
        logger.info("Stopping canvas update timer")
        self.timer.stop()
        pipe.send(("PAUSE", None))
        self.button_pause.configure(state=DISABLED)
        self.button_start.configure(state=ACTIVE)

    def send_stop(self, pipe: "Pipe"):
        logger.info("Stopping canvas update timer")
        self.timer.stop()
        pipe.send(("STOP", None))
        self.button_pause.configure(state=DISABLED)
        self.button_start.configure(state=ACTIVE)

    def send_connect(self, pipe: "Pipe"):
        logger.info("Starting canvas update timer")
        self.timer.start()
        pipe.send(("MAC", self.mac_str_var.get()))
        self.send_start(pipe)
        self.button_connect.configure(state=DISABLED)
        self.button_pause.configure(state=ACTIVE)
        self.mac_entry.configure(state=DISABLED)

    def ask_quit(self, pipe: "Pipe"):
        if messagebox.askokcancel("Quit", "You want to quit now? *sniff*"):
            self.send_stop(pipe)
            time.sleep(3)
            logger.info("destroying root")
            self.root.destroy()
            logger.info("finish destroying root")

    def __init__(self, datasource: "SensorBoard", queues, a=1, b=0, ch1=True, ch2=True, addr="DC:4E:6D:9F:E3:BA"):
        self.a = a
        self.b = b
        self.datasource = datasource
        self.ch1 = ch1
        self.ch2 = ch2
        self.channel = int(ch1) + int(ch2)

        self.display_queue = {"cap1": CapDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "cap2": CapDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "acc": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "gyro": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "mag": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              }
        self.queues = queues
        self.root = tkinter.Tk()
        self.root.wm_title("Continuous Blood Pressure")
        self.caps = []
        if self.ch1:
            self.caps.append(1)
        if self.ch2:
            self.caps.append(2)
        self.signals = [f'cap{c}' for c in self.caps]
        self.signals.extend(['acc', 'gyro', 'mag'])
        self.mac_str_var = tkinter.StringVar()
        self.mac_str_var.set(addr)
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        logger.info(f"Screen WXH  = {ws}X{hs}")
        n_monitors = 2 if ws / hs >= 2 else 1
        dpi = 100
        logger.info(f"I think you have {n_monitors} monitors")
        w, h = (ws * 0.9) / n_monitors, 0.8 * hs
        x, y = 10, 10
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.fig = Figure(figsize=(w / dpi, (h - 40) / dpi), dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)  # A tk.DrawingArea.

        self.fs = {}
        self.ax = {s: plt.subplot2grid((len(self.signals), 1), (i, 0), fig=self.fig)
                   for i, s in enumerate(self.signals)}
        t = np.linspace(0, DISPLAY_WINDOW)
        self.line = {f'cap{c}': self.ax[f'cap{c}'].plot(t, np.zeros_like(t))[0] for c in self.caps}
        self.line.update({f"{s}_{o}": self.ax[s].plot(t, np.zeros_like(t), label=o.upper())[0]
                          for s in set(self.signals) - {'cap1', 'cap2'}
                          for o in ['x', 'y', 'z']})
        y_label = {"cap1": f"Cap 1 (pF)", "cap2": f"Cap 2 (pF)", "acc": "Acc (G)", "gyro": "Gyro (dps X100)",
                   "mag": "Mag (uT)"}
        y_lim = {"cap1": (0, 8), "cap2": (0, 8), "acc": (-2, 2), "gyro": (-1, 1), "mag": (-80, 80)}
        for s in set(self.signals) - {'cap1', 'cap2'}:
            self.ax[s].legend(loc='upper right')
        for s in set(self.signals):
            self.ax[s].set_ylabel(y_label[s])
            self.ax[s].set_ylim(*y_lim[s])

            self.fs[s] = self.ax[s].text(0.1, y_lim[s][0], f"--- Hz")
            self.ax[s].set_xlim(0, DISPLAY_WINDOW)
            self.ax[s].grid()
            self.ax[s].set_title("")
            self.ax[s].set_xticks(range(0, 11))
        self.ax['mag'].set_xlabel("Time (s)")
        self.timer = self.fig.canvas.new_timer(interval=1)
        self.fig.subplots_adjust(hspace=0)

        for s in set(self.signals) - {'mag'}:
            plt.setp(self.ax[s].get_xticklabels(), visible=False)
        self.redraw()
        self.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        # buttons
        self.button_quit = tkinter.Button(master=self.root, text="Quit", )
        self.button_quit.pack(side=tkinter.LEFT)
        self.button_start = tkinter.Button(master=self.root, text="Start", state=DISABLED)
        self.button_start.pack(side=tkinter.LEFT)
        self.button_pause = tkinter.Button(master=self.root, text="Pause", state=DISABLED)
        self.button_pause.pack(side=tkinter.LEFT)
        self.mac_entry = tkinter.Entry(master=self.root, textvariable=self.mac_str_var)
        self.mac_entry.pack(side=tkinter.LEFT)
        self.button_connect = tkinter.Button(master=self.root, text="Connect")
        self.button_connect.pack(side=tkinter.LEFT)
        self.button_scan = tkinter.Button(master=self.root, text="Scan")
        self.button_scan.pack(side=tkinter.LEFT)

        self.timer.add_callback(self.redraw)

    def _redraw_signal(self, signal):
        _t = self.display_queue[signal].time

        if isinstance(self.display_queue[signal], IMUDisplayDataQueue):
            orientations = ['x', 'y', 'z']
            for o in orientations:
                value = getattr(self.display_queue[signal], o)
                self.line[f"{signal}_{o}"].set_data(_t, value)
        else:
            value = self.display_queue[signal].cap
            self.line[signal].set_data(_t, value)

        if self.display_queue[signal].non_empty > 10:
            self.fs[signal].set_text(f"{1 / np.mean(_t[1:] - _t[:-1]):.1f} Hz "
                                     f"({self.display_queue[signal].non_empty} samples)")

        try:
            _min_time = min(_t)
            _max_time = max(np.max(_t), DISPLAY_WINDOW)
            self.ax[signal].set_xticks(np.arange(_min_time, _max_time + 1).astype(int))
            self.ax[signal].set_xlim(_min_time, _max_time)
            self.fs[signal].set_x(_min_time)
        except ValueError:
            logger.warning(f"{signal} time axis is empty?")

    def _empty_queue(self):
        for c in self.caps:
            try:
                while True:
                    d = self.queues[f'cap{c}'].get(block=False)
                    self.display_queue[f'cap{c}'].put(d)
                    self.display_queue['acc'].put(d.acc)
                    d.gyro.x *= 100
                    d.gyro.y *= 100
                    d.gyro.z *= 100
                    self.display_queue['gyro'].put(d.gyro)
                    self.display_queue['mag'].put(d.mag)
            except Empty:
                pass

    def redraw(self):
        self._empty_queue()
        for s in self.signals:
            self._redraw_signal(s)

        self.fig.tight_layout(pad=0, h_pad=None, w_pad=None, rect=None)
        # self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        self.fig.subplots_adjust(hspace=0.1, right=0.99)
        self.canvas.draw()

    def start_gui(self, pipe):
        self.button_quit.configure(command=lambda: self.ask_quit(pipe))
        self.button_start.configure(command=lambda: self.send_start(pipe))
        self.button_pause.configure(command=lambda: self.send_pause(pipe))
        self.button_connect.configure(command=lambda: self.send_connect(pipe))
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.ask_quit(pipe))
        self.root.mainloop()
