__author__ = 'Alvaro'
from Tkinter import *
from tkMessageBox import *
from functools import partial
from HighCamera import HighCamera
from lowCamera import LowCamera

def start(port):
    tk = Tk()
    app = Gui(tk, port)
    tk.mainloop() # this blocks the main thread


class Gui:

    def __init__(self, master, port):

        self.createCams(port)
        self.port = port
        # window configuration
        self.frame = Frame(master)
        self.frame.grid()
        self.master = master
        master.title("sensor reader")
        master.geometry("300x500")
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_variables()

        # buttons
        #Button(self.frame, text="QUIT", fg="red", command=self.click_stop_button).grid(row=0, column=0, sticky=N)

        Button(self.frame, text="START", fg="blue", command=self.click_start_button).grid(row=0, column=1)

        Button(self.frame, text="sync", command=self.high_camera.sync).grid(row=1, sticky=W)

        Button(self.frame, text="calibrate", command=self.high_camera.calibrate).grid(row=2, sticky=W)

        Button(self.frame, text="Bit Depth", command=partial(self.high_camera.bit_depth, self.depth_val)).grid(row=3, sticky=W)
        drop = OptionMenu(self.frame,self.depth_val,'0','2','8')
        drop.grid(row=3, column=2)


        Button(self.frame, text="Frame Delay", command=partial(self.high_camera.delay, self.fdelay_text)).grid(row=4, sticky=W)
        Entry(self.frame, textvariable=self.fdelay_text).grid(row=4, column=2)

        Button(self.frame, text="Max Raw Value", command=partial(self.high_camera.max_raw, self.maxr_text)).grid(row=5, sticky=W)
        Entry(self.frame, textvariable=self.maxr_text).grid(row=5, column=2)

        Button(self.frame, text="Min Raw Value", command=partial(self.high_camera.min_raw, self.minr_text)).grid(row=6, sticky=W)
        Entry(self.frame, textvariable=self.minr_text).grid(row=6, column=2)

        Button(self.frame, text="Auto high values", command=self.high_camera.auto_gain_hi).grid(row=7, sticky=W)
        Button(self.frame, text="Auto low values", command=self.high_camera.auto_gain_low).grid(row=8, sticky=W)

        self.labelMin, self.textMin = self.set_label("Min temp")
        self.labelMax, self.textMax = self.set_label("Max temp")
        self.labelMean, self.textMean = self.set_label("Max temp")

    def create_variables(self):
        self.depth_val = StringVar(); self.depth_val.set('-')
        self.minr_text = StringVar(); self.minr_text.set('-')
        self.maxr_text = StringVar(); self.maxr_text.set('-')
        self.fdelay_text = StringVar(); self.fdelay_text.set("-")

    def createCams(self, port):
        try:
            self.low_camera.stop()
            self.high_camera.stop()
        except Exception as e:
            pass

        try:
            self.low_camera = LowCamera(port)
            self.high_camera = HighCamera(port)
        except Exception as msg:
            showerror("error", msg)


    def click_start_button(self):
        self.createCams(self.port)



    def on_closing(self):
        try:
            self.low_camera.stop()
            self.high_camera.stop()
        finally:
            self.master.destroy()



    def frame_callback(self, raw_frame):
        HighCamera.processData(raw_frame)

        amin, amax, amean = HighCamera.get_absolute_values()
        self.set_value(self.textMax, "Max temp", amax)
        self.set_value(self.textMin, "Min temp", amin)
        self.set_value(self.textMean, "mean temp", amean)


    def set_value(self, text_var, value_name, value):
        text_var.set(value_name + ":        " + "{0:.2f}".format(value))

    def set_label(self, text):
        var_text = StringVar()
        label = Label(self.frame, text=text+':-', bg="grey", textvar=var_text)
        label.grid()
        return label, var_text


