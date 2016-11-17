import matplotlib.pyplot as plt
import numpy as np

__author__ = 'Alvaro'
plot_width = 15
plot_height = 12
img = None
fig = plt.figure()


def set_plot(data):
    global img
    img = plt.imshow(data)
    img.set_cmap('hot')
    plt.ion()
    plt.show()


def update_data(data):
    global img
    img = plt.imshow(data, interpolation='quadric')
    #fig.canvas.draw()
    plt.pause(0.05)
        # print(data)

