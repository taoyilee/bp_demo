#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import tkinter


class AboutView(tkinter.Toplevel):
    TITLE = "About UCI cBP demo"
    MIN_WIDTH = 600
    MIN_HEIGHT = 400

    def close(self):
        AboutViewSingleton.window_close_callback()
        self.destroy()

    def __init__(self, parent: "tkinter.Tk" = None):
        super(AboutView, self).__init__()
        self.parent = parent
        self.wm_title(self.TITLE)
        self.resizable(False, False)
        self.wm_minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.geometry('%dx%d+%d+%d' % (self.MIN_WIDTH, self.MIN_HEIGHT,
                                       self.parent.winfo_rootx() + 10, self.parent.winfo_rooty() + 10))
        text1 = tkinter.Label(self, anchor=tkinter.W, justify="left", padx=20, pady=10,
                              text="Copyright (c) 2020 Michael Tao-Yi Lee\nDutt Research Group, UC Irvine")
        text2 = tkinter.Label(self, anchor=tkinter.W, padx=20, pady=10, text="""MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""", justify="left")
        text1.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        text2.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.protocol("WM_DELETE_WINDOW", self.close)


class AboutViewSingleton:
    instance = None

    @classmethod
    def window_close_callback(cls):
        cls.instance = None

    def __init__(self, parent):
        if not AboutViewSingleton.instance:
            AboutViewSingleton.instance = AboutView(parent)
