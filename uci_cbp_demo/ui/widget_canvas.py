#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import logging
import tkinter
from typing import TYPE_CHECKING

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from uci_cbp_demo.backend.bluetooth.constants import DISPLAY_WINDOW
from uci_cbp_demo.backend.datastructures import CapDisplayDataQueue, IMUDisplayDataQueue
from uci_cbp_demo.config import config

logger = logging.getLogger("bp_demo")

if TYPE_CHECKING:
    from uci_cbp_demo.ui.gui import GUIModel


class PlotCanvasModel:
    def __init__(self, model: "GUIModel"):
        self.model = model
        self.display_queue = {"cap1": CapDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "cap2": CapDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "acc": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "gyro": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "mag": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              }

    @property
    def signals(self):
        return self.model.signals

    def empty_queue(self):
        d = self.model.get_sample()
        for di in d:
            self.display_queue[f'cap{di.channel}'].put(di)
            self.display_queue['acc'].put(di.acc)
            self.display_queue['gyro'].put(di.gyro)
            self.display_queue['mag'].put(di.mag)


class PlotCanvas(FigureCanvasTkAgg):
    PIXELS_LEFT = 70
    PIXELS_DOWN = 50
    DPI = 100

    def __init__(self, parent, model: "PlotCanvasModel"):
        self.fig = Figure(dpi=self.DPI)
        FigureCanvasTkAgg.__init__(self, self.fig, master=parent)
        self.model = model
        self.parent = parent

        self.mpl_connect("resize_event", self.on_resize)
        self.timer = self.new_timer(interval=1)
        self.timer.add_callback(self.update_plot)
        self.fs = {}
        self.ax = {}
        self.line = {}
        self.make_axes(["cap1", "cap2", "acc", "gyro", "mag"])
        self.autoscale = tkinter.IntVar()
        self.autoscale.set(config.plotting.autoscale_cap)
        self.tight_layout()

    def on_resize(self, event):
        logger.debug(f"resize_event: {event.width} {event.height}")
        self.tight_layout()

    def update_plot(self):
        self.model.empty_queue()
        for s in self.model.signals:
            self._redraw_signal(s)
        self.tight_layout()

    def tight_layout(self):
        self.fig.tight_layout(pad=0, h_pad=None, w_pad=None, rect=None)
        width, height = self.get_width_height()
        self.fig.subplots_adjust(left=self.PIXELS_LEFT / width,
                                 bottom=self.PIXELS_DOWN / height,
                                 right=0.99, top=0.99, wspace=0.1, hspace=0.1)

        self.draw()

    def _redraw_signal(self, signal):
        _t = self.model.display_queue[signal].time

        if isinstance(self.model.display_queue[signal], IMUDisplayDataQueue):
            orientations = ['x', 'y', 'z']
            for o in orientations:
                value = getattr(self.model.display_queue[signal], o)
                self.line[f"{signal}_{o}"].set_data(_t, value)
        else:
            value = self.model.display_queue[signal].cap
            self.line[signal].set_data(_t, value)

        if self.model.display_queue[signal].non_empty > 10:
            self.fs[signal].set_text(f"{1 / np.mean(_t[1:] - _t[:-1]):.1f} Hz "
                                     f"({self.model.display_queue[signal].non_empty} samples)")

        try:
            _min_time = min(_t)
            _max_time = max(np.max(_t), DISPLAY_WINDOW)
            self.ax[signal].set_xticks(np.arange(_min_time, _max_time + 1).astype(int))
            self.ax[signal].set_xlim(_min_time, _max_time)
            self.fs[signal].set_x(_min_time)
            if "cap" in signal:
                if self.autoscale.get() == 1:
                    self.fs[signal].set_y(min(value))
                    self.ax[signal].set_ylim(min(value), max(value))
                else:
                    self.fs[signal].set_y(0)
                    self.ax[signal].set_ylim(0, 8)

        except ValueError:
            logger.debug(f"{signal} time axis is empty?")

    def make_axes(self, signals):
        self.ax = {s: plt.subplot2grid((len(signals), 1), (i, 0), fig=self.fig)
                   for i, s in enumerate(signals)}
        t = np.linspace(0, DISPLAY_WINDOW)
        caps = [s for s in signals if "cap" in s]
        self.line = {c: self.ax[c].plot(t, np.zeros_like(t))[0] for c in caps}
        self.line.update({f"{s}_{o}": self.ax[s].plot(t, np.zeros_like(t), label=o.upper())[0]
                          for s in set(signals) - {'cap1', 'cap2'}
                          for o in ['x', 'y', 'z']})
        y_label = {"cap1": f"Cap 1 (pF)", "cap2": f"Cap 2 (pF)", "acc": "Acc (G)", "gyro": "Gyro (dps X100)",
                   "mag": "Mag (uT)"}
        y_lim = {"cap1": (0, 8), "cap2": (0, 8), "acc": (-2, 2), "gyro": (-1, 1), "mag": (-10, 10)}
        for s in set(signals) - {'cap1', 'cap2'}:
            self.ax[s].legend(loc='upper right')
        for s in set(signals):
            self.ax[s].set_ylabel(y_label[s])
            self.ax[s].set_ylim(*y_lim[s])

            self.fs[s] = self.ax[s].text(0.1, y_lim[s][0], f"--- Hz")
            self.ax[s].set_xlim(0, DISPLAY_WINDOW)
            self.ax[s].grid()
            self.ax[s].set_title("")
            self.ax[s].set_xticks(range(0, 11))
        self.ax[signals[-1]].set_xlabel("Time (s)")

        self.fig.subplots_adjust(hspace=0)

        for s in set(signals) - {signals[-1]}:
            plt.setp(self.ax[s].get_xticklabels(), visible=False)

        self.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True, pady=0)
