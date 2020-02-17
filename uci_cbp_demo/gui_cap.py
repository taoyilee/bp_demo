# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import tkinter
from multiprocessing import Process, Queue
from queue import Empty

import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from scipy.interpolate import interp1d
from scipy.signal import cheby2, sosfiltfilt

from uci_cbp_demo.constants import MAX_DATA_QUEUE, WINDOW, TARGET_FS, CUTOFF, STOP_ATTEN
from uci_cbp_demo.datasources import RealDataSource_v2, MockDataSource
from uci_cbp_demo.gui_helpers import _quit

cap_data_queue = []


def update_plot(q, root, fig, line_cap, ax_cap, canvas, a, b):
    try:
        while True:
            if len(cap_data_queue) >= MAX_DATA_QUEUE:
                cap_data_queue.pop(0)
            new_data = q.get(block=False)
            cap_data_queue.append(new_data)
    except Empty:
        pass
    time = np.array([d["time"] for d in cap_data_queue])
    cap = np.array([d["cap"] for d in cap_data_queue])
    if len(time) > 20:
        try:
            fs = 1 / np.mean(time[1:] - time[:-1])
            print(f"{fs:.2f} Hz")
            time_min = WINDOW * (max(time) // WINDOW)
            smallest_index = max(-int(WINDOW * fs), -len(time))
            interpolating_time = time[smallest_index:]
            f = interp1d(interpolating_time, cap[smallest_index:], kind="cubic",
                         fill_value=(cap[smallest_index], cap[-1]), bounds_error=False)
            time_interp = np.arange(min(interpolating_time), max(time), 1 / TARGET_FS)
            cap_interp = np.array([f(tt) for tt in time_interp])
            sos = cheby2(2, STOP_ATTEN, CUTOFF / (TARGET_FS / 2), output="sos")
            cap_filtered = sosfiltfilt(sos, cap_interp)

            time_series = [(tt, s) for tt, s in zip(time_interp, cap_filtered) if tt >= time_min]
            time_plot = [tt for tt, _ in time_series]
            cap_plot = a * np.array([c for _, c in time_series]) + b

            line_cap.set_data(time_plot, cap_plot)
            ax_cap.set_ylim(max(0, min(cap_plot)), max(cap_plot))
            ax_cap.set_xlim(time_min, time_min + WINDOW)
        except Exception:
            pass
        fig.tight_layout()
        canvas.draw()
    root.after(10, update_plot, q, root, fig, line_cap, ax_cap, canvas, a, b)


def start_gui(a=1, b=0, mock=False, mac=None, uuid=None):
    root = tkinter.Tk()
    root.wm_title("Continuous Blood Pressure")
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    dpi = 100
    w, h = 0.48 * ws, 0.8 * hs
    x, y = 0, 0
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    fig = Figure(figsize=(w / dpi, (h - 20) / dpi), dpi=dpi)
    t = np.arange(0, 3, .01)
    ax_cap = fig.add_subplot(111)
    line_cap = ax_cap.plot(t, np.zeros_like(t))[0]  # type:Line2D
    ax_cap.set_ylim(0, 8)
    ax_cap.set_title("CAP CH1")
    ax_cap.grid()
    ax_cap.set_ylabel("Cap (pF)")
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    button = tkinter.Button(master=root, text="Quit", command=_quit)
    button.pack(side=tkinter.BOTTOM)

    q = Queue()
    if mock:
        print("Use mock data source")
        data_source = MockDataSource(q)
    else:
        data_source = RealDataSource_v2(q, mac, uuid)
    p = Process(target=data_source)
    p.start()
    update_plot(q, root, fig, line_cap, ax_cap, canvas, a, b)
    tkinter.mainloop()
    p.join()
