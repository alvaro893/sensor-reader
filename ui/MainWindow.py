from __future__ import unicode_literals

import datetime
import logging
import sys
from PyQt4 import QtGui, QtCore
from PyQt4.uic import loadUiType
from Queue import Queue

from matplotlib import animation
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from HighCamera import HighCamera
from Utils import serial_ports
from lowCamera import LowCamera

# Window file
Ui_MainWindow, QMainWindow = loadUiType('ui/Ui_MainWindow.ui')
Ui_PortDialog, QDialog = loadUiType('ui/Ui_PortDialog.ui')



class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, camera=None, port=None, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.figure = fig
        self.camera = camera
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
        while not self.camera.stopped:
            yield self.q.get(),

    def update_figure(self, new_arr):
        "must be implemented for children classes"
        pass

    def delete(self):
        self.camera.stop()
        self.deleteLater()


class MplCanvasHighCamera(MplCanvas):
    def __init__(self, port=None, *args, **kwargs):
        MplCanvas.__init__(self, camera=HighCamera(port), *args, **kwargs)
        self.figure.suptitle(port)
        arr = self.camera.last_frame

        # configure buttons for camera commands
        mainWindow = self.window()
        mainWindow.syncButton.clicked.connect(self.camera.sync)
        mainWindow.calibrateButton.clicked.connect(self.camera.calibrate)
        mainWindow.delayButton.clicked.connect(lambda: self.camera.delay(mainWindow.delayInput.text()))
        mainWindow.bitDepthButton.clicked.connect(lambda:
                                                  self.camera.bit_depth(int(mainWindow.bitDepthComboBox.currentText())))
        mainWindow.maxRawButton.clicked.connect(lambda: self.camera.max_raw(mainWindow.maxRawSpinBox.text()))
        mainWindow.minRawButton.clicked.connect(lambda: self.camera.min_raw(mainWindow.minRawSpinBox.text()))
        mainWindow.autoHighButton.clicked.connect(self.camera.auto_gain_hi)
        mainWindow.autoLowButton.clicked.connect(self.camera.auto_gain_low)

        # configure row and columns of plots
        self.image = self.axes.imshow(arr,
                                      interpolation="bilinear",
                                      clim=[arr.min(), arr.max()],
                                      cmap="CMRmap",
                                      origin='lower')

        self.figure.colorbar(self.image, ax=self.axes)


    def update_figure(self, new_arr):
        try:
            arr, = new_arr
            self.image.set_array(arr)
            self.image.set_clim([arr.min(), arr.max()])  # autoscale
        except AttributeError as er:
            logging.error(er.message)

        mainWindow = self.window()
        telemetry = self.camera.telemetry

        # show telemetry
        try:
            mainWindow.maxRawLabel.setText(str(telemetry['raw_max_set']))
            mainWindow.minRawLabel.setText(str(telemetry['raw_min_set']))
            mainWindow.bitDepthLabel.setText(str(telemetry['bit_depth']))
            mainWindow.delayLabel.setText(str(telemetry['frame_delay']))
            mainWindow.timeCounterLabel.setText(str(datetime.timedelta(seconds=telemetry['time_counter'] / 1000)))
            mainWindow.frameCounterLabel.setText(str(telemetry['frame_counter']))
            mainWindow.frameMeanLabel.setText(str(telemetry['frame_mean']))
            mainWindow.maxTempLabel.setText(str(telemetry['raw_max']))
            mainWindow.minTempLabel.setText(str(telemetry['raw_min']))
            mainWindow.discardPacketsLabel.setText(str(telemetry['discard_packets_count']))
            mainWindow.agcLabel.setText(str(telemetry['agc']))
            mainWindow.fpaTempLabel.setText("%.2f" % (telemetry['fpa_temp'] / 100.0 - 273.15))
        except KeyError as e:
            logging.error(e.message)

        return self.image,



class MplCanvasLowCamera(MplCanvas):
    def __init__(self, port=None, *args, **kwargs):
        MplCanvas.__init__(self, camera=LowCamera(port), *args, **kwargs)
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


class PortDialog(QDialog, Ui_PortDialog):
    def __init__(self, ):
        super(PortDialog, self).__init__()
        self.setupUi(self)
        ports = serial_ports()
        self.listWidget.addItems(ports)
        self.hNetItem = "High Camera From network (WebSocket)"
        self.listWidget.addItem(self.hNetItem)
        self.listWidget.setCurrentRow(0)
        self.was_accepted = False
        self.radioButtonHigh.setChecked(True)
        # self.setWindowModality(QtCore.Qt.WindowModal)

    def accept(self):
        self.was_accepted = True
        self.close()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.main_widget = QtGui.QWidget(self)

        self.l = self.plotLayout
        self.camera_canvas = []
        self.addCameraButton.clicked.connect(self.addCamera)
        self.deleteButton.clicked.connect(self.deleteCameras)

        # color = MplCanvasHighCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=serial_ports()[0])
        # self.camera_canvas.append(color)
        # l.addWidget(color)

        self.main_widget.setFocus()
        # self.setCentralWidget(self.main_widget)
        self.statusBar().showMessage("Alvaro", 2000)

    def deleteCameras(self):
        canvas = self.camera_canvas.pop()
        canvas.delete()
        # self.l.removeWidget(canvas)

    def addCamera(self):
        dialog = PortDialog()
        dialog.buttonBox.accepted.connect(dialog.accept)
        dialog.exec_()

        if dialog.was_accepted:
            port = str(dialog.listWidget.currentItem().text())
            self.current_port = port
            if port == dialog.hNetItem: port = None

            if dialog.radioButtonLow.isChecked():
                self.createCamera(port, style='low')
            if dialog.radioButtonHigh.isChecked():
                self.createCamera(port, style='hi')

    def createCamera(self, port, style='hi'):
        if(style == 'hi'):
            canvas = MplCanvasHighCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=port)
        else:
            print 'low'
            canvas = MplCanvasLowCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=port)
        self.camera_canvas.append(canvas)
        self.l.addWidget(canvas)
        self.camera_canvas.append(canvas)
        canvas.figure.suptitle(self.current_port)

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
    sys.exit(qApp.exec_())
    # qApp.exec_()
