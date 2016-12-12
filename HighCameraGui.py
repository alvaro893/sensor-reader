__author__ = 'Alvaro'
from Tkinter import *
from tkMessageBox import *
from functools import partial
from SerialCommunication import SerialCommunication
import HighCamera

def start(port):
    tk = Tk()
    app = App(tk, port)

    tk.mainloop()
    tk.destroy() # optional; see description below



class App:

    def __init__(self, master, port):

        # Other threads
        self.createThreads(port)
        self.port = port

        # window configuration
        self.frame = Frame(master)
        self.frame.pack()
        master.title("sensor reader")
        master.geometry("300x200")

        # buttons
        self.button_stop = Button(self.frame, text="QUIT", fg="red", command=self.click_stop_button)
        self.button_start.pack(side=LEFT)

        self.button_start = Button(self.frame, text="START", fg="blue", command=self.click_start_button)
        self.button_start.pack(side=LEFT)

        self.button_sync = Button(self.frame, text="sync", command=self.click_sync_button)
        self.button_sync.pack(side=LEFT)

        self.button_calibrate = Button(self.frame, text="calibrate", command=self.click_calibrate_button)
        self.button_calibrate.pack(side=LEFT)

        # separator = Frame(height=2, bd=1, relief=SUNKEN)
        # separator.pack(fill=X, padx=5, pady=5)
        self.labelMin, self.textMin = self.set_label("Min temp")
        self.labelMax, self.textMax = self.set_label("Max temp")
        self.labelMean, self.textMean = self.set_label("Max temp")


    def createThreads(self, port):
        try:
            self.serial_thread = SerialCommunication(self.frame_callback, port)
        except Exception as msg:
            showerror("error", msg)

    def click_start_button(self):
        if not self.serial_thread.is_alive:
            self.serial_thread.start_reading()



    def click_stop_button(self):
        self.serial_thread.stop_reading()
        self.createThreads(self.port)
        #self.frame.quit()

    def click_sync_button(self):
        self.serial_thread.write_to_serial('S')

    def click_calibrate_button(self):
        self.serial_thread.write_to_serial('C')

    def click_max_raw(self):
        self.serial_thread.write_to_serial('H')

    def click_min_raw(self):
        self.serial_thread.write_to_serial('L')

    def click_auto_gain_hi(self):
        self.serial_thread.write_to_serial('A')

    def click_auto_gain_low(self):
        self.serial_thread.write_to_serial('a')

    def click_bit_depth(self):
        self.serial_thread.write_to_serial('B')

    def click_delay(self):
        self.serial_thread.write_to_serial('U')


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
        label.pack()
        return label, var_text


