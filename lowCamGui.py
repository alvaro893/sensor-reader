__author__ = 'Alvaro'
from Tkinter import *
from functools import partial
from threading import Thread
from SerialCommunication import SerialCommunication
import HttpConnection
import Analisys
import lowCamera

def start(ports):
    tk = Tk()
    app = App(tk)
    app.set_ports(ports)

    tk.mainloop()
    tk.destroy() # optional; see description below



def hello():
    print "hello!"
def change_port(v):
    print v

class App:

    def __init__(self, master):

        # Other threads
        self.createThreads()

        # window configuration
        self.frame = Frame(master)
        self.frame.pack()
        master.title("sensor reader")

        # create a pulldown menu, and add it to the menu bar
        self.menubar = Menu(master)
        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Open", command=hello)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=master.quit)
        self.menubar.add_cascade(label="File", menu=filemenu)
        helpmenu = Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label="About", command=hello)
        self.menubar.add_cascade(label="Help", menu=helpmenu)
        # display the menu
        master.config(menu=self.menubar)

        # buttons
        self.button_stop = Button(self.frame, text="QUIT", fg="red", command=self.click_stop_button)
        self.button_stop.pack(side=LEFT)

        self.button_start = Button(self.frame, text="START", fg="blue", command=self.click_start_button)
        self.button_start.pack(side=LEFT)

        # separator = Frame(height=2, bd=1, relief=SUNKEN)
        # separator.pack(fill=X, padx=5, pady=5)
        self.labelMin, self.textMin = self.set_label("Min temp")
        self.labelMax, self.textMax = self.set_label("Max temp")
        self.labelMean, self.textMean = self.set_label("Max temp")


    def createThreads(self):
        self.network_thread = HttpConnection.NetworkThread()
        self.analysis_thread = Analisys.AsyncAnalysis(lowCamera.frame_arr)
        self.serial_thread = SerialCommunication(self.frame_callback)

    def click_start_button(self):
        self.serial_thread.start_reading()
        self.network_thread.start()
        self.analysis_thread.start()
        #self.serial_thread.start_reading()

    def click_stop_button(self):
        self.network_thread.stop()
        self.analysis_thread.stop()
        self.serial_thread.stop_reading()
        self.createThreads()
        #self.frame.quit()

    def frame_callback(self, raw_frame):
        self.network_thread.add_to_buffer(raw_frame)
        processed_frame = lowCamera.process_frame(raw_frame)
        self.analysis_thread.put_arr_in_queue(processed_frame)

        self.set_value(self.textMax, "Max temp", lowCamera.raw_max)
        self.set_value(self.textMin, "Min temp", lowCamera.raw_min)
        self.set_value(self.textMean, "mean temp", lowCamera.raw_mean)


    def set_value(self, text_var, value_name, value):
        text_var.set(value_name + ": " + str(value))

    def set_label(self, text):
        var_text = StringVar()
        label = Label(self.frame, text=text+':-', bg="grey", textvar=var_text)
        label.pack()
        return label, var_text

    def set_ports(self, port_names):
        portmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Port", menu=portmenu)
        for port in port_names:
            portmenu.add_command(label=port, command=partial(change_port, port))
