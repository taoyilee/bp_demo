#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import tkinter


class DACControlModel:
    @property
    def dac(self):
        return self._dac

    def __init__(self, name, default_dac_value=0):
        self.name = name
        self._dac = tkinter.IntVar()
        self._dac.set(default_dac_value)

    def incr(self):
        self._dac.set(min(self._dac.get() + 1, 0x7F))

    def decr(self):
        self._dac.set(max(self._dac.get() - 1, 0))


class DACControl(tkinter.Frame):
    def __init__(self, master, model: "DACControlModel", state, *args, **kwargs):
        super(DACControl, self).__init__(master, *args, **kwargs)
        self.model = model
        self.label = tkinter.Label(master=self, text=model.name, state=state)
        self.label.pack(side=tkinter.LEFT)
        self.dac_value = tkinter.Entry(master=self, width=10, textvariable=self.model.dac,
                                       state="readonly" if state != tkinter.DISABLED else state)
        self.dac_value.pack(side=tkinter.LEFT)
        self.incr = tkinter.Button(master=self, text="+", width=1, command=self.model.incr, state=state)
        self.incr.pack(side=tkinter.LEFT)
        self.decr = tkinter.Button(master=self, text="-", width=1, command=self.model.decr, state=state)
        self.decr.pack(side=tkinter.LEFT)
