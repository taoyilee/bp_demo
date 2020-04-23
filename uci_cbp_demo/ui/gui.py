#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import time
import tkinter
from multiprocessing import Pipe, Process, Queue
from queue import Empty
from tkinter import messagebox, DISABLED, ACTIVE
from typing import List

import uci_cbp_demo
from uci_cbp_demo.backend import FileExporter, FileExporterConf
from uci_cbp_demo.backend.bluetooth import CapData
from uci_cbp_demo.config import config
from uci_cbp_demo.logging import logger
from uci_cbp_demo.ui.widget_about import AboutViewSingleton
from uci_cbp_demo.ui.widget_canvas import PlotCanvas, PlotCanvasModel
from uci_cbp_demo.ui.widget_dac_control import DACControl
from uci_cbp_demo.ui.widget_preferences import PreferencesViewSingleton
from uci_cbp_demo.ui.widget_scan import ScanViewSingleton


class GUIView(tkinter.Tk):
    TITLE = f"UCI Continuous Blood Pressure {uci_cbp_demo.__version__}"
    MIN_WIDTH = 640
    MIN_HEIGHT = 480

    def __init__(self, model: "GUIModel"):
        super(GUIView, self).__init__()
        self.model: GUIModel = model
        self.model = model
        self.model.view = self

        self.imu = True
        self.wm_title(self.TITLE)
        self.wm_minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.mac_str_var = tkinter.StringVar()
        self.mac_str_var.set(config.board.mac)
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
        self.editmenu.add_command(label="UI Preferences", command=lambda: PreferencesViewSingleton(self))
        self.menubar.add_cascade(label="Edit", menu=self.editmenu, state=ACTIVE)

        self.aboutmenu = tkinter.Menu(master=self.menubar, tearoff=0)
        self.aboutmenu.add_command(label="About this software", command=lambda: AboutViewSingleton(self))
        self.menubar.add_cascade(label="About", menu=self.aboutmenu, state=ACTIVE)
        self.config(menu=self.menubar)

        self.canvas = PlotCanvas(self, PlotCanvasModel(model))
        self.canvas.make_axes(self.model.signals)
        # buttons
        self.button_ch1 = tkinter.Button(master=self, text="CH 1", state=ACTIVE,
                                         relief="sunken" if model.ch1 else "raised")
        self.button_ch1.pack(side=tkinter.LEFT)
        self.button_ch2 = tkinter.Button(master=self, text="CH 2", state=ACTIVE,
                                         relief="sunken" if model.ch2 else "raised")
        self.button_ch2.pack(side=tkinter.LEFT)

        self.button_imu = tkinter.Button(master=self, text="IMU", state=ACTIVE,
                                         relief="sunken" if model.imu else "raised")
        self.button_imu.pack(side=tkinter.LEFT)

        self.button_start = tkinter.Button(master=self, text="Start", state=DISABLED)
        self.button_start.pack(side=tkinter.LEFT)
        self.button_pause = tkinter.Button(master=self, text="Pause", state=DISABLED)
        self.button_pause.pack(side=tkinter.LEFT)
        self.mac_entry = tkinter.Entry(master=self, textvariable=self.mac_str_var)
        self.mac_entry.pack(side=tkinter.LEFT)
        self.button_connect = tkinter.Button(master=self, text="Connect")
        self.button_connect.pack(side=tkinter.LEFT)
        self.button_scan = tkinter.Button(master=self, text="Scan", command=lambda: ScanViewSingleton(self))
        self.button_scan.pack(side=tkinter.LEFT)

        self.ckb_autocap = tkinter.Checkbutton(master=self, text="AutoScale Cap", variable=self.canvas.autoscale)
        self.ckb_autocap.pack(side=tkinter.LEFT)

        self.dac_a_control = DACControl(self, self.model, "(+)", "1", padx=5, state=ACTIVE)
        self.dac_a_control.pack(side=tkinter.LEFT)
        self.dac_b_control = DACControl(self, self.model, "(-)", "2", padx=5, state=ACTIVE)
        self.dac_b_control.pack(side=tkinter.LEFT)


class GUIModel:

    @property
    def dac1(self):
        return config.board.dac1

    @property
    def dac2(self):
        return config.board.dac2

    @dac1.setter
    def dac1(self, value):
        self.notify("DAC1", value)
        config.board.dac1 = value

    @dac2.setter
    def dac2(self, value):
        self.notify("DAC2", value)
        config.board.dac2 = value

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, value):
        self._view = value

    def notify(self, message, payload=None):
        _msg = (message, payload)
        logger.info(f"Sending {_msg}")
        self.pipe.send(_msg)

    def start(self):
        self.notify("START")

    def connect(self):
        self.notify("CONNECT")

    def pause(self):
        self.notify("PAUSE")

    def set_ch_status(self, ch, status):
        self.notify(f"CH{ch}", status)
        setattr(self, f"ch{ch}", status)

    def stop(self):
        self.notify("STOP")
        self.remove_exporter()

    @property
    def mac_addr(self):
        return self._mac_addr

    @mac_addr.setter
    def mac_addr(self, value):
        self._mac_addr = value
        self.pipe.send(("MAC", self.mac_addr))
        if self.view is not None:
            self.view.mac_str_var.set(self.mac_addr)

    def init(self, mac_addr):
        self.mac_addr = mac_addr
        self.set_ch_status(1, self.ch1)
        self.set_ch_status(2, self.ch2)
        self.notify("DAC1", self.dac1)
        self.notify("DAC2", self.dac2)
        self.connect()

    @property
    def caps(self):
        _caps = []
        if self.ch1:
            _caps.append(1)
        if self.ch2:
            _caps.append(2)
        return _caps

    def pop_queue(self, c) -> CapData:
        try:
            d = self.queues[f'cap{c}'].get(block=False)  # type:CapData
            for orientation in ["x", "y", "z"]:
                setattr(d.gyro, orientation, 100 * getattr(d.gyro, orientation))
            return d
        except Empty:
            pass

    def get_sample(self) -> List[CapData]:
        _return = []
        for i in range(40):
            for ch in [1, 2]:
                new_data = self.pop_queue(ch)
                if new_data is not None:
                    self._exporter.put(new_data)
                    _return.append(new_data)
        return _return

    @property
    def signals(self):
        _signals = [f'cap{c}' for c in self.caps]
        if self.imu:
            _signals.extend(['acc', 'gyro', 'mag'])
        return _signals

    def __init__(self, queues, pipe, a=1, b=0, ch1=None, ch2=None, addr="DC:4E:6D:9F:E3:BA"):
        self.a = a
        self.b = b
        self._view = None
        self._exporter: FileExporter = None
        self._mac_addr = addr
        self.ch1 = config.plotting.ch1_en if ch1 is None else ch1
        self.ch2 = config.plotting.ch2_en if ch2 is None else ch2
        self.imu = config.plotting.imu_en
        self.pipe = pipe
        self.queues = queues

    def attach_exporter(self, exporter: "FileExporter"):
        self._exporter = exporter

    def remove_exporter(self):
        self._exporter = None


class GUIController:

    def start(self):
        self.model.start()
        self._view.canvas.timer.start()
        self._view.button_connect.configure(state=DISABLED)
        self._view.button_scan.configure(state=DISABLED)
        self._view.button_start.configure(state=DISABLED)
        self._view.button_pause.configure(state=ACTIVE)

    def pause(self):
        self.model.pause()
        self._view.canvas.timer.stop()
        self._view.button_pause.configure(state=DISABLED)
        self._view.button_start.configure(state=ACTIVE)
        self._view.mac_entry.configure(state=DISABLED)

    def stop(self):
        self.model.stop()
        self._view.canvas.timer.stop()
        self._view.button_pause.configure(state=DISABLED)
        self._view.button_start.configure(state=ACTIVE)

    def connect(self):
        config.board.mac = self._view.mac_str_var.get()
        self.exporter.new_session()
        self.model.attach_exporter(self.exporter)
        self.model.init(self._view.mac_str_var.get())
        self.model.pipe.poll(None)
        c = self.model.pipe.recv()
        if c[0] == "CONNECTED":
            logger.info("Bluetooth connected received by GUI")
            self.start()

    def imu_toggle(self):
        _btn = getattr(self._view, f"button_imu")
        if len(self.model.caps) == 0:
            return
        if _btn.cget("relief") == "sunken":
            self.model.imu = False
            config.plotting.imu_en = False
            _btn.configure(relief="raised")
        else:
            self.model.imu = True
            config.plotting.imu_en = True
            _btn.configure(relief="sunken")

        self._view.canvas.make_axes(self.model.signals)
        self._view.canvas.tight_layout()

    def autoscale_cap(self):
        config.plotting.autoscale_cap = self._view.canvas.autoscale.get()

    def ch_toggle(self, channel):
        _btn = getattr(self._view, f"button_ch{channel}")
        if _btn.cget("relief") == "sunken":  # attempt to disable a cap channel
            if len(self.model.caps) == 1:  # do not allow disabling both channels
                return
            self.model.set_ch_status(channel, False)
            setattr(config.plotting, f"ch{channel}_en", False)
            _btn.configure(relief="raised")
        else:  # attempt to enable a cap channel
            self.model.set_ch_status(channel, True)
            setattr(config.plotting, f"ch{channel}_en", True)
            _btn.configure(relief="sunken")
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

        model.mac_addr = config.board.mac
        model.ch1 = config.plotting.ch1_en
        model.ch2 = config.plotting.ch2_en
        model.imu = config.plotting.imu_en
        from appdirs import user_data_dir
        _fe_conf = FileExporterConf()
        _fe_conf.app_data_directory = user_data_dir(uci_cbp_demo.__appname__, uci_cbp_demo.__author__)
        self.exporter = FileExporter(_fe_conf)
        self.model = model
        self._view = GUIView(self.model)

        self._view.protocol("WM_DELETE_WINDOW", self.ask_quit)

        self._view.button_start.configure(command=self.start)
        self._view.button_pause.configure(command=self.pause)
        self._view.button_connect.configure(command=self.connect)

        self._view.button_ch1.configure(command=lambda: self.ch_toggle(1))
        self._view.button_ch2.configure(command=lambda: self.ch_toggle(2))
        self._view.button_imu.configure(command=self.imu_toggle)
        self._view.ckb_autocap.configure(command=self.autoscale_cap)

    def start_gui(self):
        logger.info("Starting GUI")
        self._view.mainloop()


def main():
    from uci_cbp_demo.backend import SensorBoard
    pipe_1, pipe_2 = Pipe()
    q = {"cap1": Queue(), "cap2": Queue(), "acc": Queue(), "gyro": Queue(), "mag": Queue()}
    sensor = SensorBoard(addr="DC:4E:6D:9F:E3:BA", pipe=pipe_2)
    _gui = GUIController(GUIModel(q, pipe_1, addr="DC:4E:6D:9F:E3:BA"))
    p = Process(target=sensor.start_session, args=(q,))
    p.start()
    _gui.start_gui()
    p.terminate()
