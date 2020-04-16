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

import uci_cbp_demo
from uci_cbp_demo.bluetooth import SensorBoard
from uci_cbp_demo.bluetooth.constants import DISPLAY_WINDOW
from uci_cbp_demo.datastructures import CapDisplayDataQueue, IMUDisplayDataQueue

logger = logging.getLogger("bp_demo")


class PlotCanvas(FigureCanvasTkAgg):
    PIXELS_LEFT = 70
    PIXELS_DOWN = 50

    def __init__(self, parent, caller, queues, dpi=100, **kwargs):
        self.dpi = dpi
        self.parent = parent
        self.queues = queues
        self.caller = caller
        self.display_queue = {"cap1": CapDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "cap2": CapDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "acc": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "gyro": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              "mag": IMUDisplayDataQueue(window_size=DISPLAY_WINDOW),
                              }

        self.fig = Figure(dpi=dpi)
        FigureCanvasTkAgg.__init__(self, self.fig, master=parent)
        self.mpl_connect("resize_event", self.on_resize)
        self.timer = self.new_timer(interval=1)
        self.fs = {}
        self.ax = {}
        self.line = {}
        self.make_axes(self.caller.signals)
        self.autoscale = tkinter.IntVar()
        self.autoscale.set(1)
        self.timer.add_callback(self.redraw)
        self.redraw()

    def on_resize(self, event):
        logger.debug(f"resize_event: {event.width} {event.height}")
        self.redraw()

    def redraw(self):
        self._empty_queue()
        for s in self.caller.signals:
            self._redraw_signal(s)

        self.fig.tight_layout(pad=0, h_pad=None, w_pad=None, rect=None)
        width, height = self.get_width_height()
        self.fig.subplots_adjust(left=self.PIXELS_LEFT / width,
                                 bottom=self.PIXELS_DOWN / height,
                                 right=0.99, top=0.99, wspace=0.1, hspace=0.1)

        self.draw()

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
            if "cap" in signal:
                if self.autoscale.get() == 1:
                    self.fs[signal].set_y(min(value))
                    self.ax[signal].set_ylim(min(value), max(value))
                else:
                    self.fs[signal].set_y(0)
                    self.ax[signal].set_ylim(0, 8)

        except ValueError:
            logger.warning(f"{signal} time axis is empty?")

    def _empty_queue(self):
        for c in [1, 2]:
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
        y_lim = {"cap1": (0, 8), "cap2": (0, 8), "acc": (-2, 2), "gyro": (-1, 1), "mag": (-80, 80)}
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

        for s in set(signals) - {'mag'}:
            plt.setp(self.ax[s].get_xticklabels(), visible=False)

        self.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True, pady=0)


class DACControl(tkinter.Frame):
    def __init__(self, master, name, *args, **kwargs):
        super(DACControl, self).__init__(master, *args, **kwargs)
        self.label = tkinter.Label(master=self, text=name)
        self.label.pack(side=tkinter.LEFT)
        self._dac = tkinter.IntVar()
        self._dac.set(0)

        self.dac_value = tkinter.Entry(master=self, width=10, textvariable=self._dac, state="readonly")
        self.dac_value.pack(side=tkinter.LEFT)
        self.incr = tkinter.Button(master=self, text="+", width=1, command=self._incr)
        self.incr.pack(side=tkinter.LEFT)
        self.decr = tkinter.Button(master=self, text="-", width=1, command=self._decr)
        self.decr.pack(side=tkinter.LEFT)

    def _incr(self):
        self._dac.set(min(self._dac.get() + 1, 0x7F))

    def _decr(self):
        self._dac.set(max(self._dac.get() - 1, 0))


class GUI:
    fig = None
    root = None
    canvas = None
    ax_cap1 = None
    ax_cap2 = None
    line_cap1 = None
    line_cap2 = None

    def send_message(self, pipe: "Pipe", message):
        _msg = (message, None)
        logger.info(f"Sending {_msg}")
        pipe.send(_msg)

    def send_start(self, pipe: "Pipe"):
        self.send_message(pipe, "CONNECT")
        self.canvas.timer.start()
        self.button_connect.configure(state=DISABLED)
        self.button_start.configure(state=DISABLED)
        self.button_pause.configure(state=ACTIVE)

    def send_pause(self, pipe: "Pipe"):
        self.send_message(pipe, "PAUSE")
        self.canvas.timer.stop()
        self.button_pause.configure(state=DISABLED)
        self.button_start.configure(state=ACTIVE)

    def send_stop(self, pipe: "Pipe"):
        self.send_message(pipe, "STOP")
        self.canvas.timer.stop()
        self.button_pause.configure(state=DISABLED)
        self.button_start.configure(state=ACTIVE)

    def send_connect(self, pipe: "Pipe"):
        logger.info("Starting canvas update timer")
        self.canvas.timer.start()
        pipe.send(("MAC", self.mac_str_var.get()))
        self.send_start(pipe)
        self.button_connect.configure(state=DISABLED)
        self.button_pause.configure(state=ACTIVE)
        self.mac_entry.configure(state=DISABLED)

    def imu_toggle(self):
        _btn = getattr(self, f"button_imu")
        if len(self.caps) == 0:
            return
        if _btn.cget("relief") == "sunken":
            _btn.configure(relief="raised")
        else:
            _btn.configure(relief="sunken")
        setattr(self, f"imu", not getattr(self, f"imu"))
        self.canvas.make_axes(self.signals)
        self.canvas.redraw()

    def ch_toggle(self, channel, pipe: "Pipe"):
        _btn = getattr(self, f"button_ch{channel}")
        if _btn.cget("relief") == "sunken":
            if len(self.caps) == 1:  # do not allow disabling both channels
                return
            _btn.configure(relief="raised")
        else:  # attempt to disable a cap channel
            _btn.configure(relief="sunken")
        self.send_message(pipe, f"CH{channel}")
        setattr(self, f"ch{channel}", not getattr(self, f"ch{channel}"))
        self.canvas.make_axes(self.signals)
        self.canvas.redraw()

    def ask_quit(self, pipe: "Pipe"):
        if messagebox.askokcancel("Quit", "You want to quit now? *sniff*"):
            self.send_stop(pipe)
            time.sleep(3)
            logger.info("destroying root")
            self.root.destroy()
            logger.info("finish destroying root")

    @property
    def caps(self):
        _caps = []
        if self.ch1:
            _caps.append(1)
        if self.ch2:
            _caps.append(2)
        return _caps

    @property
    def signals(self):
        _signals = [f'cap{c}' for c in self.caps]
        if self.imu:
            _signals.extend(['acc', 'gyro', 'mag'])
        return _signals

    def __init__(self, datasource: "SensorBoard", queues, a=1, b=0, ch1=True, ch2=True, addr="DC:4E:6D:9F:E3:BA"):
        self.a = a
        self.b = b
        self.datasource = datasource
        self.ch1 = ch1
        self.ch2 = ch2
        self.imu = True
        self.channel = int(ch1) + int(ch2)

        self.root = tkinter.Tk()
        self.root.wm_title(f"Continuous Blood Pressure {uci_cbp_demo.__version__}")
        self.root.wm_minsize(640, 480)

        self.mac_str_var = tkinter.StringVar()
        self.mac_str_var.set(addr)
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        logger.info(f"Screen WXH  = {ws}X{hs}")
        n_monitors = 2 if ws / hs >= 2 else 1
        logger.info(f"I think you have {n_monitors} monitors")
        w, h = (ws * 0.9) / n_monitors, 0.8 * hs
        x, y = 10, 10
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.canvas = PlotCanvas(self.root, self, queues)

        # buttons
        self.button_quit = tkinter.Button(master=self.root, text="Quit", )
        self.button_quit.pack(side=tkinter.LEFT)

        self.button_ch1 = tkinter.Button(master=self.root, text="CH 1", state=ACTIVE, relief="sunken")
        self.button_ch1.pack(side=tkinter.LEFT)
        self.button_ch2 = tkinter.Button(master=self.root, text="CH 2", state=ACTIVE, relief="sunken")
        self.button_ch2.pack(side=tkinter.LEFT)

        self.button_imu = tkinter.Button(master=self.root, text="IMU", state=ACTIVE, relief="sunken")
        self.button_imu.pack(side=tkinter.LEFT)

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

        self.ckb_autocap = tkinter.Checkbutton(master=self.root, text="AutoScale Cap", variable=self.canvas.autoscale)
        self.ckb_autocap.pack(side=tkinter.LEFT)

        self.dac_a_control = DACControl(self.root, "DAC A", padx=5)
        self.dac_a_control.pack(side=tkinter.LEFT)
        self.dac_b_control = DACControl(self.root, "DAC B", padx=5)
        self.dac_b_control.pack(side=tkinter.LEFT)

    def start_gui(self, pipe):
        self.button_quit.configure(command=lambda: self.ask_quit(pipe))
        self.button_start.configure(command=lambda: self.send_start(pipe))
        self.button_pause.configure(command=lambda: self.send_pause(pipe))
        self.button_connect.configure(command=lambda: self.send_connect(pipe))

        self.button_ch1.configure(command=lambda: self.ch_toggle(1, pipe))
        self.button_ch2.configure(command=lambda: self.ch_toggle(2, pipe))
        self.button_imu.configure(command=lambda: self.imu_toggle())

        self.root.protocol("WM_DELETE_WINDOW", lambda: self.ask_quit(pipe))
        self.root.mainloop()
