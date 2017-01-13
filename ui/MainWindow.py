from __future__ import unicode_literals
import sys

from matplotlib.backends import qt_compat

from DetectSerialPorts import serial_ports
from HighCamera import HighCamera
from lowCamera import LowCamera

use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore
    from PyQt4.uic import loadUiType
    from matplotlib.figure import Figure

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# Window file
Ui_MainWindow, QMainWindow = loadUiType('ui/Ui_MainWindow.ui')
Ui_PortDialog, QDialog = loadUiType('ui/Ui_PortDialog.ui')



class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.figure = fig
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)


        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class LowResolutionCanvas(MyMplCanvas):
    pass
class HighResolutionCanvas(MyMplCanvas):
    pass




class MplCanvasHighCamera(MyMplCanvas):
    #TODO: port
    def __init__(self,port=None, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        #TODO: sub class for diferent cameras
        self.camera = HighCamera(port)
        arr = self.camera.last_frame
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)

        # configure row and columns of plots
        self.pcolorm = self.axes.pcolormesh(arr, cmap='rainbow')
        self.figure.colorbar(self.pcolorm, ax=self.axes)

    def update_figure(self):
        new_arr = self.camera.last_frame
        self.pcolorm.set_array(new_arr.ravel())
        self.pcolorm.set_clim([new_arr.min(), new_arr.max()])  # autoscale
        self.draw()

    def close_camera(self):
        self.camera.stop()

class MplCanvasLowCamera(MyMplCanvas):
    # TODO: port
    def __init__(self, port=None, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        self.camera = LowCamera(port)  #serial_ports()[0]
        arr = self.camera.last_frame
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)

        # configure row and columns of plots
        self.pcolorm = self.axes.pcolormesh(arr, cmap='rainbow')
        self.figure.colorbar(self.pcolorm, ax=self.axes)


    def update_figure(self):
        new_arr = self.camera.last_frame
        self.pcolorm.set_array(new_arr.ravel())
        self.pcolorm.set_clim([new_arr.min(), new_arr.max()]) #autoscale
        self.draw()

    def close_camera(self):
        self.camera.stop()

class PortDialog(QDialog, Ui_PortDialog):
    def __init__(self,):
        super(PortDialog, self).__init__()
        self.setupUi(self)
        ports = serial_ports()
        self.listWidget.addItems(ports)
        self.listWidget.setCurrentRow(0)
        self.was_accepted = False
        self.radioButtonHigh.setChecked(True)
        #self.setWindowModality(QtCore.Qt.WindowModal)

    def accept(self):
        self.was_accepted = True
        self.close()

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self,):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.main_widget = QtGui.QWidget(self)

        self.l = self.plotLayout
        self.camera_canvas = []
        self.addCameraButton.clicked.connect(self.addCamera)

        # color = MplCanvasHighCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=serial_ports()[0])
        # self.camera_canvas.append(color)
        # l.addWidget(color)

        self.main_widget.setFocus()
        #self.setCentralWidget(self.main_widget)
        self.statusBar().showMessage("Alvaro", 2000)

    def addCamera(self):
        dialog = PortDialog()
        dialog.buttonBox.accepted.connect(dialog.accept)
        dialog.exec_()

        if dialog.was_accepted:
            current_port = str(dialog.listWidget.currentItem().text())
            if dialog.radioButtonLow.isChecked():
                self.createCamera(current_port, style='low')
            if dialog.radioButtonHigh.isChecked():
                self.createCamera(current_port, style='hi')

    def createCamera(self, port, style='hi'):
        if(style == 'hi'):
            canvas = MplCanvasHighCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=port)
        else:
            print 'low'
            canvas = MplCanvasLowCamera(parent=self.main_widget, width=5, height=4, dpi=100, port=port)
        self.camera_canvas.append(canvas)
        self.l.addWidget(canvas)
        self.camera_canvas.append(canvas)

    def fileQuit(self):
        self.close()
        for canvas in self.camera_canvas:
            canvas.close_camera()

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
    #qApp.exec_()
