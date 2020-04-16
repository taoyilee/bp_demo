#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import time
import tkinter
from multiprocessing import Pipe, Process, Queue
from tkinter import messagebox, DISABLED, ACTIVE

import uci_cbp_demo
from uci_cbp_demo.logging import logger
from uci_cbp_demo.ui.widget_canvas import PlotCanvas, PlotCanvasModel
from uci_cbp_demo.ui.widget_dac_control import DACControl, DACControlModel


class GUIView(tkinter.Tk):
    TITLE = f"UCI Continuous Blood Pressure {uci_cbp_demo.__version__}"
    MIN_WIDTH = 640
    MIN_HEIGHT = 480

    def __init__(self):
        super(GUIView, self).__init__()
        self.model = None
        self.imu = True
        self.wm_title(self.TITLE)
        self.wm_minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.mac_str_var = tkinter.StringVar()
        self.mac_str_var.set("")
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        logger.info(f"Screen WXH  = {ws}X{hs}")
        n_monitors = 2 if ws / hs >= 2 else 1
        logger.info(f"I think you have {n_monitors} monitors")
        w, h = (ws * 0.9) / n_monitors, 0.8 * hs
        x, y = 10, 10
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))

        self.menubar = tkinter.Menu(master=self)
        self.filemenu = tkinter.Menu(master=self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save Waveform")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit")
        self.menubar.add_cascade(label="File", menu=self.filemenu, state=DISABLED)

        self.editmenu = tkinter.Menu(master=self.menubar, tearoff=0)
        self.editmenu.add_command(label="UI Preferences")
        self.menubar.add_cascade(label="Edit", menu=self.editmenu, state=DISABLED)

        self.aboutmenu = tkinter.Menu(master=self.menubar, tearoff=0)
        self.aboutmenu.add_command(label="About this software")
        self.menubar.add_cascade(label="About", menu=self.aboutmenu, state=DISABLED)
        self.config(menu=self.menubar)

        self.canvas = PlotCanvas(self)
        # buttons
        self.button_ch1 = tkinter.Button(master=self, text="CH 1", state=ACTIVE, relief="sunken")
        self.button_ch1.pack(side=tkinter.LEFT)
        self.button_ch2 = tkinter.Button(master=self, text="CH 2", state=ACTIVE, relief="sunken")
        self.button_ch2.pack(side=tkinter.LEFT)

        self.button_imu = tkinter.Button(master=self, text="IMU", state=ACTIVE, relief="sunken")
        self.button_imu.pack(side=tkinter.LEFT)

        self.button_start = tkinter.Button(master=self, text="Start", state=DISABLED)
        self.button_start.pack(side=tkinter.LEFT)
        self.button_pause = tkinter.Button(master=self, text="Pause", state=DISABLED)
        self.button_pause.pack(side=tkinter.LEFT)
        self.mac_entry = tkinter.Entry(master=self, textvariable=self.mac_str_var)
        self.mac_entry.pack(side=tkinter.LEFT)
        self.button_connect = tkinter.Button(master=self, text="Connect")
        self.button_connect.pack(side=tkinter.LEFT)
        self.button_scan = tkinter.Button(master=self, text="Scan")
        self.button_scan.pack(side=tkinter.LEFT)

        self.ckb_autocap = tkinter.Checkbutton(master=self, text="AutoScale Cap", variable=self.canvas.autoscale)
        self.ckb_autocap.pack(side=tkinter.LEFT)

        self.dac_model = {"A": DACControlModel("DAC A", 0), "B": DACControlModel("DAC B", 0)}
        self.dac_a_control = DACControl(self, self.dac_model["A"], padx=5, state=DISABLED)
        self.dac_a_control.pack(side=tkinter.LEFT)
        self.dac_b_control = DACControl(self, self.dac_model["B"], padx=5, state=DISABLED)
        self.dac_b_control.pack(side=tkinter.LEFT)

    def attach_model(self, model: "GUIModel"):
        self.model = model
        self.mac_str_var.set(model.mac_addr)
        self.canvas.attach_model(PlotCanvasModel(model))


class GUIModel:

    def notify(self, message):
        _msg = (message, None)
        logger.info(f"Sending {_msg}")
        self.pipe.send(_msg)

    def start(self):
        self.notify("CONNECT")

    def pause(self):
        self.notify("PAUSE")

    def toggle_channel(self, ch):
        self.notify(f"CH{ch}")
        setattr(self, f"ch{ch}", not getattr(self, f"ch{ch}"))

    def stop(self):
        self.notify("STOP")

    @property
    def mac_addr(self):
        return self._mac_addr

    @mac_addr.setter
    def mac_addr(self, value):
        self._mac_addr = value
        logger.info("Starting canvas update timer")
        self.pipe.send(("MAC", self.mac_addr))
        self.start()

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

    def __init__(self, queues, pipe, a=1, b=0, ch1=True, ch2=True, addr="DC:4E:6D:9F:E3:BA"):
        self.a = a
        self.b = b
        self._mac_addr = addr
        self.ch1 = ch1
        self.ch2 = ch2
        self.imu = True
        self.pipe = pipe
        self.queues = queues


class GUIController:

    def start(self):
        self.model.start()
        self._view.canvas.timer.start()
        self._view.button_connect.configure(state=DISABLED)
        self._view.button_start.configure(state=DISABLED)
        self._view.button_pause.configure(state=ACTIVE)

    def pause(self):
        self.model.pause()
        self._view.canvas.timer.stop()
        self._view.button_pause.configure(state=DISABLED)
        self._view.button_start.configure(state=ACTIVE)

    def stop(self):
        self.model.stop()
        self._view.canvas.timer.stop()
        self._view.button_pause.configure(state=DISABLED)
        self._view.button_start.configure(state=ACTIVE)

    def connect(self):
        self.model.mac_addr = self._view.mac_str_var.get()
        self._view.canvas.timer.start()
        self._view.button_connect.configure(state=DISABLED)
        self._view.button_pause.configure(state=ACTIVE)
        self._view.mac_entry.configure(state=DISABLED)

    def imu_toggle(self):
        _btn = getattr(self._view, f"button_imu")
        if len(self.model.caps) == 0:
            return
        if _btn.cget("relief") == "sunken":
            _btn.configure(relief="raised")
        else:
            _btn.configure(relief="sunken")
        setattr(self, f"imu", not getattr(self, f"imu"))
        self._view.canvas.make_axes(self.model.signals)
        self._view.redraw()

    def ch_toggle(self, channel):
        _btn = getattr(self._view, f"button_ch{channel}")
        if _btn.cget("relief") == "sunken":
            if len(self.model.caps) == 1:  # do not allow disabling both channels
                return
            _btn.configure(relief="raised")
        else:  # attempt to disable a cap channel
            _btn.configure(relief="sunken")
        self.model.toggle_channel(channel)
        setattr(self, f"ch{channel}", not getattr(self, f"ch{channel}"))
        self._view.canvas.make_axes(self.model.signals)
        self._view.canvas.tight_layout()

    def ask_quit(self):
        if messagebox.askokcancel("Quit", "You want to quit now? *sniff*"):
            self.model.stop()
            time.sleep(3)
            logger.info("destroying root")
            self._view.destroy()
            logger.info("finish destroying root")

    def __init__(self, model: "GUIModel"):
        self.model = model
        self._view = GUIView()
        self._view.attach_model(self.model)
        self._view.protocol("WM_DELETE_WINDOW", self.ask_quit)

        self._view.button_start.configure(command=self.start)
        self._view.button_pause.configure(command=self.pause)
        self._view.button_connect.configure(command=self.connect)

        self._view.button_ch1.configure(command=lambda: self.ch_toggle(1))
        self._view.button_ch2.configure(command=lambda: self.ch_toggle(2))
        self._view.button_imu.configure(command=self.imu_toggle)

    def start_gui(self):
        logger.info("Starting GUI")
        self._view.mainloop()


def main():
    from uci_cbp_demo.backend import SensorBoard
    pipe_1, pipe_2 = Pipe()
    q = {"cap1": Queue(), "cap2": Queue(), "acc": Queue(), "gyro": Queue(), "mag": Queue()}
    sensor = SensorBoard(addr="DC:4E:6D:9F:E3:BA", pipe=pipe_2)
    _gui = GUIController(GUIModel(q, pipe_1, a=1, b=0, ch1=True, ch2=True, addr="DC:4E:6D:9F:E3:BA"))
    p = Process(target=sensor.start_cap_notification, args=(q,))
    p.start()
    _gui.start_gui()
    p.terminate()
