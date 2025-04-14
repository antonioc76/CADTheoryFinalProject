import PyQt6 as qt
import PyQt6.QtWidgets as wdg
from PyQt6.uic import loadUi
import os
import sys

import matplotlib
matplotlib.use('qtagg')
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(projection='3d')
        super().__init__(self.fig)


class MainWindow(wdg.QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()

        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            self.this_exec_dir = os.path.dirname(sys._MEIPASS)
        else:
            self.this_exec_dir = os.path.dirname(os.path.abspath(__file__))

        # self.this_exec_dir = os.path.dirname(os.path.abspath(__file__))
        loadUi(self.this_exec_dir + "\\CADUI.ui", self)

        # state flags
        self.sketch_dialogue_displayed = False

        # setup plot
        self.sc = MplCanvas()
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 5, 3, 2]
        self.sc.axes.plot(x, y)
        self.layout = self.HLayoutOuter
        self.mplContainer.addWidget(self.sc) 

        self.show()

        # setup intellisense for ui objects from ui
        self.sketchPlaneButton: wdg.QPushButton
        self.sketchButton: wdg.QPushButton
        self.surfaceButton: wdg.QPushButton
        self.transformationButton: wdg.QPushButton

        # setup callback functions
        self.sketchPlaneButton.clicked.connect(self.sketch_dialogue)


    def sketch_dialogue(self):
        if self.sketch_dialogue_displayed == True: 
            return

        # labels and fields
        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)
        

        # plane selection
        xyButton = wdg.QPushButton("XY Plane")
        yzButton = wdg.QPushButton("YZ Plane")
        zxButton = wdg.QPushButton("ZX Plane")

        layout.addWidget(xyButton, 0, 0)
        layout.addWidget(yzButton, 0, 1)
        layout.addWidget(zxButton, 0, 2)

        
        sketchPlanePlotButton = wdg.QPushButton("Preview")
        sketchPlaneAcceptButton = wdg.QPushButton("Accept")
        layout.addWidget(sketchPlanePlotButton, 3, 1)
        layout.addWidget(sketchPlaneAcceptButton, 3, 2)
        sketchPlanePlotButton.clicked.connect(self.preview_sketch_plane)
        sketchPlaneAcceptButton.clicked.connect(self.accept_sketch_plane)
        
        self.optionLayout.addWidget(self.sketchContainer)
        self.sketch_dialogue_displayed = True


    def accept_sketch_plane(self):
        self.sketchContainer.deleteLater()
        self.sketch_dialogue_displayed = False

        # TODO: WIPE CANVAS AND REDRAW ACTUAL FEATURES ONLY
        self.sc.axes.cla()
        self.sc.draw()

    def preview_sketch_plane(self):
        x = [1, 2, 3, 4, 5]
        y = [1, 1, 1, 2, 1]

        self.sc.axes.plot(x, y)
        self.sc.figure.canvas.draw()


if __name__ == "__main__":
    app = wdg.QApplication(sys.argv)
    app.setStyle('windowsvista')
    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec())