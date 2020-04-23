#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import tkinter
from typing import TYPE_CHECKING

from uci_cbp_demo.logging import logger

if TYPE_CHECKING:
    from uci_cbp_demo.ui.gui import GUIModel


class DACControlModel:
    @property
    def dac(self):
        return self._dac

    def __init__(self, name, model: "GUIModel"):
        self.name = f"DAC {name}"
        self._model_variable = f"dac{name}"
        self._dac = tkinter.IntVar()
        self.model = model
        self._dac.set(getattr(model, self._model_variable))

    def value_update(self):
        logger.info(f"{self._model_variable} = {self._dac.get()}")
        setattr(self.model, self._model_variable, self._dac.get())

    def incr(self):
        self._dac.set(min(self._dac.get() + 1, 0x7F))
        self.value_update()

    def decr(self):
        self._dac.set(max(self._dac.get() - 1, 0))
        self.value_update()


class DACControl(tkinter.Frame):
    def __init__(self, master, model: "GUIModel", label, name: str, state, *args, **kwargs):
        super(DACControl, self).__init__(master, *args, **kwargs)

        self.model = DACControlModel(name, model)
        self.label = tkinter.Label(master=self, text=f"DAC{label}", state=state)
        self.label.pack(side=tkinter.LEFT)
        self.dac_value = tkinter.Entry(master=self, width=10, textvariable=self.model.dac,
                                       state="readonly" if state != tkinter.DISABLED else state)
        self.dac_value.pack(side=tkinter.LEFT)
        self.incr = tkinter.Button(master=self, text="+", width=1, command=self.model.incr, state=state)
        self.incr.pack(side=tkinter.LEFT)
        self.decr = tkinter.Button(master=self, text="-", width=1, command=self.model.decr, state=state)
        self.decr.pack(side=tkinter.LEFT)
