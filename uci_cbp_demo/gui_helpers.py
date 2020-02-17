# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
from matplotlib.backend_bases import key_press_handler


def on_key_press(event, canvas):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas)


def _quit(root):
    root.quit()  # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
