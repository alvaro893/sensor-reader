from __future__ import unicode_literals
import sys

from matplotlib.backends import qt_compat

from DetectSerialPorts import serial_ports
from HighCamera import HighCamera

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




class ColorMplCanvas(MyMplCanvas):

    def __init__(self,port=None, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        self.camera = HighCamera(serial_ports()[0])
        arr = self.camera.frame_arr
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(500)

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


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self,):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.main_widget = QtGui.QWidget(self)

        l = self.plotLayout
        #sc = MyStaticMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        # dc = ColorMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        color = ColorMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        self.camera_canvas = []
        self.camera_canvas.append(color)
        #l.addWidget(sc)
        # l.addWidget(dc)
        l.addWidget(color)

        self.main_widget.setFocus()
        #self.setCentralWidget(self.main_widget)

        self.statusBar().showMessage("All hail matplotlib!", 2000)

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
