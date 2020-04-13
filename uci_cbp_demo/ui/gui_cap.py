#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import logging
import time
import tkinter
from multiprocessing import Pipe
from queue import Empty
from tkinter import messagebox

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from scipy.interpolate import interp1d

from uci_cbp_demo.bluetooth import SensorBoard
from uci_cbp_demo.bluetooth.callbacks import CapData
from uci_cbp_demo.bluetooth.constants import TARGET_TS, DISPLAY_WINDOW, FS, FILTER_WINDOW, IMU_FS
from uci_cbp_demo.datastructures import CapIterableQueue, CapDisplayDataQueue, IMUDisplayDataQueue

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

    def send_start(self, pipe: "Pipe"):
        logger.info("Starting canvas update timer")
        self.timer.start()
        pipe.send(("CONNECT", None))

    def send_pause(self, pipe: "Pipe"):
        logger.info("Stopping canvas update timer")
        self.timer.stop()
        pipe.send(("PAUSE", None))

    def send_stop(self, pipe: "Pipe"):
        logger.info("Stopping canvas update timer")
        self.timer.stop()
        pipe.send(("STOP", None))

    def send_connect(self, pipe: "Pipe"):
        logger.info("Starting canvas update timer")
        self.timer.start()
        pipe.send(("MAC", self.mac_str_var.get()))
        self.send_start(pipe)

    def ask_quit(self, pipe: "Pipe"):
        if messagebox.askokcancel("Quit", "You want to quit now? *sniff*"):
            self.send_stop(pipe)
            time.sleep(3)
            logger.info("destroying root")
            self.root.destroy()
            logger.info("finish destroying root")

    def __init__(self, datasource: "SensorBoard", queues, a=1, b=0, ch1=True, ch2=True):
        self.a = a
        self.b = b
        self.datasource = datasource
        self.ch1 = ch1
        self.ch2 = ch2
        self.channel = int(ch1) + int(ch2)
        _display_queue_size = int(DISPLAY_WINDOW * FS / self.channel)
        _imu_queue_size = int(DISPLAY_WINDOW * IMU_FS / self.channel)

        self.display_queue = {"cap1": CapDisplayDataQueue(size=_display_queue_size),
                              "cap2": CapDisplayDataQueue(size=_display_queue_size),
                              "acc": IMUDisplayDataQueue(size=_imu_queue_size),
                              "gyro": IMUDisplayDataQueue(size=_imu_queue_size),
                              "mag": IMUDisplayDataQueue(size=_imu_queue_size)
                              }
        _filter_queue_size = int(FILTER_WINDOW * FS / self.channel)
        self.filter = {"cap1": StreamDataFilter(history=_filter_queue_size),
                       "cap2": StreamDataFilter(history=_filter_queue_size)}
        self.queues = queues
        self.init_gui()

    def init_gui(self, addr="DC:4E:6D:9F:E3:BA"):
        self.root = tkinter.Tk()
        self.root.wm_title("Continuous Blood Pressure")

        self.mac_str_var = tkinter.StringVar()
        self.mac_str_var.set(addr)
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        logger.info(f"Screen width  = {ws}")
        logger.info(f"Screen height = {hs}")
        n_monitors = 2 if ws / hs >= 2 else 1
        dpi = 100
        logger.info(f"I think you have {n_monitors} monitors")
        w, h = (ws * 0.9) / n_monitors, 0.8 * hs
        x, y = 10, 10
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.fig = Figure(figsize=(w / dpi, (h - 40) / dpi), dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)  # A tk.DrawingArea.
        if self.channel == 2:
            self.ax_cap1 = plt.subplot2grid((5, 1), (0, 0), fig=self.fig)
            self.ax_cap2 = plt.subplot2grid((5, 1), (1, 0), fig=self.fig)

            self.ax_acc = plt.subplot2grid((5, 1), (2, 0), fig=self.fig)
            self.ax_gyro = plt.subplot2grid((5, 1), (3, 0), fig=self.fig)
            self.ax_mag = plt.subplot2grid((5, 1), (4, 0), fig=self.fig)
        elif self.ch1:
            self.ax_cap1 = plt.subplot2grid((4, 1), (0, 0), fig=self.fig)

            self.ax_acc = plt.subplot2grid((4, 1), (1, 0), fig=self.fig)
            self.ax_gyro = plt.subplot2grid((4, 1), (2, 0), fig=self.fig)
            self.ax_mag = plt.subplot2grid((4, 1), (3, 0), fig=self.fig)
        elif self.ch2:
            self.ax_cap2 = plt.subplot2grid((4, 1), (0, 0), fig=self.fig)

            self.ax_acc = plt.subplot2grid((4, 1), (1, 0), fig=self.fig)
            self.ax_gyro = plt.subplot2grid((4, 1), (2, 0), fig=self.fig)
            self.ax_mag = plt.subplot2grid((4, 1), (3, 0), fig=self.fig)
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

        self.line_acc_x = self.ax_acc.plot(t, np.zeros_like(t), label="X")[0]  # type:Line2D
        self.line_acc_y = self.ax_acc.plot(t, np.zeros_like(t), label="Y")[0]  # type:Line2D
        self.line_acc_z = self.ax_acc.plot(t, np.zeros_like(t), label="Z")[0]  # type:Line2D
        self.ax_acc.legend()
        self.fs_acc = self.ax_acc.text(0.1, 1, f"--- Hz")
        self.ax_acc.set_xlim(0, DISPLAY_WINDOW)
        self.ax_acc.set_ylim(-2, 2)
        self.ax_acc.set_title("Accelerometer")
        self.ax_acc.grid()
        self.ax_acc.set_ylabel("G")

        self.line_gyro_x = self.ax_gyro.plot(t, np.zeros_like(t), label="X")[0]  # type:Line2D
        self.line_gyro_y = self.ax_gyro.plot(t, np.zeros_like(t), label="Y")[0]  # type:Line2D
        self.line_gyro_z = self.ax_gyro.plot(t, np.zeros_like(t), label="Z")[0]  # type:Line2D
        self.fs_gyro = self.ax_gyro.text(0.1, 1, f"--- Hz")
        self.ax_gyro.legend()
        self.ax_gyro.set_xlim(0, DISPLAY_WINDOW)
        self.ax_gyro.set_ylim(-10, 10)
        self.ax_gyro.set_title("Gyroscope")
        self.ax_gyro.grid()
        self.ax_gyro.set_ylabel("degree/s")

        self.line_mag_x = self.ax_mag.plot(t, np.zeros_like(t), label="X")[0]  # type:Line2D
        self.line_mag_y = self.ax_mag.plot(t, np.zeros_like(t), label="Y")[0]  # type:Line2D
        self.line_mag_z = self.ax_mag.plot(t, np.zeros_like(t), label="Z")[0]  # type:Line2D
        self.fs_mag = self.ax_mag.text(0.1, 1, f"--- Hz")
        self.ax_mag.legend()
        self.ax_mag.set_xlim(0, DISPLAY_WINDOW)
        self.ax_mag.set_ylim(-2, 2)
        self.ax_mag.set_title("Magnetometer")
        self.ax_mag.grid()
        self.ax_mag.set_ylabel("G")
        self.ax_mag.set_xlabel("Time (s)")

        self.timer = self.fig.canvas.new_timer(interval=1)

    def _acc_redraw(self):
        try:
            while True:
                d = self.queues['acc'].get(block=False)
                self.display_queue['acc'].put(d)
        except Empty:
            pass
        time = self.display_queue['acc'].time_plot
        x = self.display_queue['acc'].x
        self.line_acc_x.set_data(time, x)
        y = self.display_queue['acc'].y
        self.line_acc_y.set_data(time, y)
        z = self.display_queue['acc'].z
        self.line_acc_z.set_data(time, z)

        if self.display_queue['acc'].non_empty > 10:
            self.fs_acc.set_text(f"{1 / np.mean(time[1:] - time[:-1]):.1f} Hz "
                                 f"({self.display_queue['acc'].non_empty} samples)")
        try:
            self.ax_acc.set_xlim(min(time), max(max(time), DISPLAY_WINDOW))
        except ValueError:
            pass

    def _gyro_redraw(self):
        try:
            while True:
                d = self.queues['gyro'].get(block=False)
                self.display_queue['gyro'].put(d)
        except Empty:
            pass
        time = self.display_queue['gyro'].time_plot
        x = self.display_queue['gyro'].x
        self.line_gyro_x.set_data(time, x)
        y = self.display_queue['gyro'].y
        self.line_gyro_y.set_data(time, y)
        z = self.display_queue['gyro'].z
        self.line_gyro_z.set_data(time, z)

        if self.display_queue['gyro'].non_empty > 10:
            self.fs_gyro.set_text(f"{1 / np.mean(time[1:] - time[:-1]):.1f} Hz "
                                  f"({self.display_queue['gyro'].non_empty} samples)")
        try:
            self.ax_gyro.set_xlim(min(time), max(max(time), DISPLAY_WINDOW))
            self.ax_gyro.set_ylim(-1e-4, 1e-4)
        except ValueError:
            pass

    def _mag_redraw(self):
        try:
            while True:
                d = self.queues['mag'].get(block=False)
                self.display_queue['mag'].put(d)
        except Empty:
            pass
        time = self.display_queue['mag'].time_plot
        x = self.display_queue['mag'].x
        self.line_mag_x.set_data(time, x)
        y = self.display_queue['mag'].y
        self.line_mag_y.set_data(time, y)
        z = self.display_queue['mag'].z
        self.line_mag_z.set_data(time, z)

        if self.display_queue['mag'].non_empty > 10:
            self.fs_mag.set_text(f"{1 / np.mean(time[1:] - time[:-1]):.1f} Hz "
                                 f"({self.display_queue['mag'].non_empty} samples)")
        try:
            self.ax_mag.set_xlim(min(time), max(max(time), DISPLAY_WINDOW))
        except ValueError:
            pass

    def _cap1_redraw(self):
        try:
            while True:
                d = self.queues['cap1'].get(block=False)
                self.display_queue['cap1'].put(d)
        except Empty:
            pass
        time = self.display_queue['cap1'].time_plot
        cap = self.display_queue['cap1'].cap
        self.line_cap1.set_data(time, cap)

        if self.display_queue['cap1'].non_empty > 10:
            self.fs_cap1.set_text(f"{1 / np.mean(time[1:] - time[:-1]):.1f} Hz "
                                  f"({self.display_queue['cap1'].non_empty} samples)")
        try:
            self.ax_cap1.set_xlim(min(time), max(max(time), DISPLAY_WINDOW))
        except ValueError:
            pass

    def _cap2_redraw(self):
        try:
            while True:
                d = self.queues['cap2'].get(block=False)
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
        self._acc_redraw()
        self._gyro_redraw()
        self._mag_redraw()
        self.fig.tight_layout()
        self.canvas.draw()

    def start_gui(self, pipe):
        self.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        button = tkinter.Button(master=self.root, text="Quit", command=lambda: self.ask_quit(pipe))
        button.pack(side=tkinter.LEFT)

        button_start = tkinter.Button(master=self.root, text="Start", command=lambda: self.send_start(pipe))
        button_start.pack(side=tkinter.LEFT)

        button_pause = tkinter.Button(master=self.root, text="Pause", command=lambda: self.send_pause(pipe))
        button_pause.pack(side=tkinter.LEFT)

        mac_entry = tkinter.Entry(master=self.root, textvariable=self.mac_str_var)
        mac_entry.pack(side=tkinter.LEFT)

        button_connect = tkinter.Button(master=self.root, text="Connect", command=lambda: self.send_connect(pipe))
        button_connect.pack(side=tkinter.LEFT)
        self.timer.add_callback(self.redraw)
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.ask_quit(pipe))
        self.redraw()
        self.root.mainloop()