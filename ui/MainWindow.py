from __future__ import unicode_literals

import datetime
import logging
import sys
from time import sleep

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread
from PyQt4.QtGui import QCommandLinkButton
from PyQt4.QtGui import QPushButton
from PyQt4.uic import loadUiType
from Queue import Queue

from matplotlib import animation
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import HttpConnection
from HighCamera import HighCamera
from Utils import serial_ports
from lowCamera import LowCamera

# Window file
Ui_MainWindow, QMainWindow = loadUiType('ui/Ui_MainWindow.ui')
Ui_HiControl, QWidget = loadUiType('ui/Ui_HiControlWidget.ui')
Ui_LowControl, QWidget = loadUiType('ui/Ui_LowControlWidget.ui')



class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, camera=None, port=None, parent=None, width=5, height=4, dpi=100, **kwargs):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(111)
        self.axes.set_axis_off()
        self.figure = fig
        self.camera = camera
        self.title = kwargs['title'] or "From Network"
        self.controlWidget = None

        # We want the axes cleared every time plot() is called
        # self.axes.hold(False)

        FigureCanvas.__init__(self, fig)
        self.q = Queue(1)
        # self.worker = Worker(self)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        # this will update the canvas when a frame is available, from the ui thread using a signal
        self.camera.on_frame_ready(self.add_to_queue)
        # QObject.connect(self, self.signal, self.add_to_queue)

        # define animation object
        self.ani = animation.FuncAnimation(fig, self.update_figure, self.data_gen, blit=True, interval=10,
                                      repeat=False)


    def add_to_queue(self):
        self.q.put(self.camera.last_frame)

    def data_gen(self):
        """ It gets the data from the camera and send it to update_figure function
        using generator mechanism. "yield" sends a tuple but does not exit the function"""
        while not self.camera.stopped:
            if not self.q.empty():
                yield self.q.get(),
            else:
                yield

    def update_figure(self, new_arr):
        "must be implemented for children classes"
        pass

    def delete(self):
        self.camera.stop()
        self.deleteLater()


class MplCanvasHighCamera(MplCanvas):
    def __init__(self, port=None, *args, **kwargs):
        MplCanvas.__init__(self, title=port,camera=HighCamera(port), *args, **kwargs)
        self.figure.suptitle(port)
        arr = self.camera.last_frame


        # configure row and columns of plots
        self.image = self.axes.imshow(arr,
                                      interpolation="bilinear",
                                      clim=[arr.min(), arr.max()],
                                      cmap="CMRmap",
                                      origin='lower')


    def update_figure(self, new_arr):
        """" gets data from a generator (tuple) from data_get function and
        updates the animation. in order of no blocking the ui the image must be updated even though
        we did not get data"""
        if new_arr == None:
            sleep(0.01)  # this reduces cpu comsuption a lot
            return self.image,
        try:
            arr, = new_arr
            self.image.set_array(arr)
            self.image.set_clim([arr.min(), arr.max()])  # autoscale
        except AttributeError as er:
            logging.error(er.message)

        control = self.controlWidget
        telemetry = self.camera.telemetry

        # show telemetry
        try:
            control.maxRawLabel.setText(str(telemetry['raw_max_set']))
            control.minRawLabel.setText(str(telemetry['raw_min_set']))
            control.bitDepthLabel.setText(str(telemetry['bit_depth']))
            control.delayLabel.setText(str(telemetry['frame_delay']))
            control.timeCounterLabel.setText(str(datetime.timedelta(seconds=telemetry['time_counter'] / 1000)))
            control.frameCounterLabel.setText(str(telemetry['frame_counter']))
            control.frameMeanLabel.setText(str(telemetry['frame_mean']))
            control.maxTempLabel.setText(str(telemetry['raw_max']))
            control.minTempLabel.setText(str(telemetry['raw_min']))
            control.discardPacketsLabel.setText(str(telemetry['discard_packets_count']))
            control.fpaTempLabel.setText("%.2f" % (telemetry['fpa_temp'] / 100.0 - 273.15))
            control.timeCounterLabel2.setText(str(telemetry['time_counter2']))
            control.frameStateLabel.setText(str(telemetry['frame_state']))
            control.sensorVersionLabel.setText(str(telemetry['sensor_version']))

            maxled, minled = self.getLedStatus(int(telemetry['agc']))
            # control.maxLed.setValue(maxled)
            # control.minLed.setValue(minled)
            def is_manual(manual):
                if manual:
                    return "manual"
                else:
                    return "auto"
            control.maxLed.setFormat(is_manual(maxled))
            control.minLed.setFormat(is_manual(minled))

        except KeyError as e:
            logging.error(e.message)

        return self.image,

    def getLedStatus(self, agc_byte):
        """the bit in the left represents the minimum, the bit in the right the max"""
        minled_bit = agc_byte & 1 # 0b01 -> 1
        maxled_bit = agc_byte >> 1 # 0b01 -> 0
        return maxled_bit ^ 1, minled_bit ^ 1  # ^1 is like a bitwise not


class MplCanvasLowCamera(MplCanvas):
    def __init__(self, port=None, *args, **kwargs):
        MplCanvas.__init__(self, title=port, camera=LowCamera(port), *args, **kwargs)
        arr = self.camera.last_frame

        # configure row and columns of plots
        self.image = self.axes.imshow(arr,
                                      interpolation="bilinear",
                                      clim=[arr.min(), arr.max()],
                                      cmap="rainbow",
                                      origin='lower')

        self.figure.colorbar(self.image, ax=self.axes)
        self.axes.set_xlim((0, self.camera.x_lim))

    def update_figure(self, new_arr):
        try:
            self.image.set_array(new_arr)
            self.image.set_clim([new_arr.min(), new_arr.max()])  # autoscale
            self.draw()
            amin, amax, amean = ("%.2f" % i for i in self.camera.get_absolute_values())
            self.window().maxTempLabel.setText(str(amax))
            self.window().minTempLabel.setText(str(amin))
            self.window().meanTempLabel.setText(str(amean))
        except AttributeError as e:
            logging.error(e.message)



class HiControlWidget(QWidget, Ui_HiControl):
    def __init__(self, camera):
        super(HiControlWidget, self).__init__()
        self.setupUi(self)
        self.syncButton.clicked.connect(camera.sync)
        self.calibrateButton.clicked.connect(camera.calibrate)
        self.delayButton.clicked.connect(lambda: camera.delay(self.delayInput.text()))
        self.bitDepthButton.clicked.connect(lambda:
                                                  camera.bit_depth(int(self.bitDepthComboBox.currentText())))
        self.maxRawButton.clicked.connect(lambda: camera.max_raw(self.maxRawSpinBox.text()))
        self.minRawButton.clicked.connect(lambda: camera.min_raw(self.minRawSpinBox.text()))
        self.autoHighButton.clicked.connect(camera.auto_gain_hi)
        self.autoLowButton.clicked.connect(camera.auto_gain_low)
        # self.rebootButton.clicked.connect(camera.reboot_rpi)


class LowControlWidget(QWidget, Ui_LowControl):
    def __init__(self):
        super(LowControlWidget, self).__init__()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, window_number=0):

        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.main_widget = QtGui.QWidget(self)
        self.l = self.plotLayout

        self.sensorConnections = []
        self.current_sensor_index = 0

        if(window_number > 0):
            self.addCameraButton.clicked.connect(self.addCamera)
        else:
            self.addCameraButton.clicked.connect(self.addCamera2)

        self.deleteButton.clicked.connect(self.delete2Sensors)
        self.nextCameraButton.clicked.connect(self.nextCameraCallback(1))
        self.previousCameraButton.clicked.connect(self.nextCameraCallback(-1))

        # color = MplCanvasHighCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=serial_ports()[0])
        # self.camera_canvas.append(color)
        # l.addWidget(color)

        self.main_widget.setFocus()
        # self.setCentralWidget(self.main_widget)
        self.statusBar().showMessage("Alvaro", 2000)

    class SensorConnection:
        def __init__(self, canvas, control):
            self.title = canvas.title
            # ui objects
            self.canvas = canvas
            self.control = control
            self.canvas.controlWidget = control
            canvas.figure.suptitle(self.title)

        def destroy(self):
            self.canvas.delete()
            self.control.deleteLater()

    def nextCameraCallback(self, increment):
        def callback():
            new_index = self.current_sensor_index + increment
            if new_index in range(0, len(self.sensorConnections)):
                print "new_index:", new_index
                self.stackedWidget.setCurrentIndex(new_index)
                self.controlLabel.setText("%s" % (self.sensorConnections[new_index].title))
                self.current_sensor_index = new_index
        return callback

    def getCurrentSensor(self):
        return


    def deleteSensor(self):
        if len(self.sensorConnections) == 0:
            return
        sensor = self.sensorConnections.pop(self.current_sensor_index)
        sensor.destroy()
        self.stackedWidget.removeWidget(sensor.control)
        self.nextCameraCallback(-1)()

    def delete2Sensors(self):
        self.deleteSensor()
        self.deleteSensor()
        self.addCameraButton.setEnabled(True)


    def addCamera(self):
        self.createSensorConnection("network:LOBBY1", "hi")
        self.createSensorConnection("network:LOBBY2", "hi")
        self.addCameraButton.setEnabled(False)

    def addCamera2(self):
        self.createSensorConnection("network:RESTAURANT1", "hi")
        self.createSensorConnection("network:RESTAURANT2", "hi")

        self.addCameraButton.setEnabled(False)


    def createSensorConnection(self, port, style):
        if(style == 'hi'):
            canvas = MplCanvasHighCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=port)
            controlWidget = HiControlWidget(canvas.camera)
        else:
            print 'low'
            canvas = MplCanvasLowCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=port)
            controlWidget = LowControlWidget()

        self.l.addWidget(canvas)
        self.stackedWidget.addWidget(controlWidget)
        self.stackedWidget.setCurrentWidget(controlWidget)
        sensor = self.SensorConnection(canvas, controlWidget)
        self.sensorConnections.append(sensor)
        self.current_sensor_index = len(self.sensorConnections) - 1
        self.controlLabel.setText("%s" % (sensor.title))


    def fileQuit(self):
        self.close()
        for canvas in self.camera_canvas:
            canvas.delete()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtGui.QMessageBox.about(self, "About",
                                """embedding_in_qt4.py example""")


def run_ui():
    qApp = QtGui.QApplication(sys.argv)

    aw = MainWindow()
    aw.show()
    aw2 = MainWindow(1)
    aw2.show()
    sys.exit(qApp.exec_())
    # qApp.exec_()
