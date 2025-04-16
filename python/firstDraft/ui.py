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

import sympy as sp
import numpy as np

from ruledSurface import RuledSurface
from CADUtils import Offset


class FeatureTree:
    def __init__(self):
        self.sketchPlanes = []
        self.sketches = []
        self.surfaces = []


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

        # feature tree
        self.featureTree = FeatureTree()

        # temp sketch plane
        self.tempSketchPlane = None

        # state flags
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False

        # setup plot
        self.sc = MplCanvas()

        self.set_labels()
        self.set_limits()

        self.layout = self.HLayoutOuter
        self.mplContainer.addWidget(self.sc) 

        self.show()

        self.selectedSketchPlane = None

        # setup intellisense for ui objects from .ui file
        self.sketchPlaneButton: wdg.QPushButton
        self.sketchButton: wdg.QPushButton
        self.surfaceButton: wdg.QPushButton
        self.transformationButton: wdg.QPushButton

        # setup callback functions
        self.sketchPlaneButton.clicked.connect(self.sketch_plane_dialogue)
        self.sketchButton.clicked.connect(self.sketch_dialogue)


    def clear_option_layout(self):
        for i in reversed(range(self.optionLayout.count())): 
            self.optionLayout.itemAt(i).widget().setParent(None)


    def sketch_dialogue(self):
        if self.sketch_dialogue_displayed == True: 
            return
        
        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        self.clear_option_layout()

        sketchPlaneListLabel = wdg.QLabel("Select sketch plane")
        sketchPlaneList = wdg.QListWidget()

        names = [plane.name for plane in self.featureTree.sketchPlanes]

        sketchPlaneList.addItems(names)

        print(names)

        selectButton = wdg.QPushButton("Start Sketch")
        deleteButton = wdg.QPushButton("Delete Sketch")

        layout.addWidget(sketchPlaneListLabel, 0, 0)
        layout.addWidget(sketchPlaneList, 1, 0, 1, 2)
        layout.addWidget(deleteButton, 2, 0)
        layout.addWidget(selectButton, 2, 1)

        deleteButton.clicked.connect(lambda: self.deleteSketchPlane(sketchPlaneList, sketchPlaneList.selectedItems()))

        # end
        self.optionLayout.addWidget(self.sketchContainer)

        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = True


    def deleteSketchPlane(self, sketchPlaneList, items):
        names = [item.text() for item in items]

        updatedSketchPlanes = [sketchPlane for sketchPlane in self.featureTree.sketchPlanes if sketchPlane.name not in names]
        
        self.featureTree.sketchPlanes = updatedSketchPlanes

        for item in items:
            sketchPlaneList.takeItem(sketchPlaneList.row(item))

        self.drawFeatures()


    def sketch_plane_dialogue(self):
        if self.sketch_plane_dialogue_displayed == True: 
            return
        
        self.angle_widgets_displayed = False
        self.offset_widgets_displayed = False

        # labels and fields
        self.sketchPlaneContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchPlaneContainer)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        
        # plane selection
        xyButton = wdg.QPushButton("XY Plane")
        yzButton = wdg.QPushButton("YZ Plane")
        xzButton = wdg.QPushButton("XZ Plane")

        layout.addWidget(xyButton, 0, 0)
        layout.addWidget(yzButton, 0, 1)
        layout.addWidget(xzButton, 0, 2)

        xyButton.clicked.connect(lambda: self.xy_button_callback(layout))
        yzButton.clicked.connect(lambda: self.yz_button_callback(layout))
        xzButton.clicked.connect(lambda: self.xz_button_callback(layout))

        sketchPlaneEscapeButton = wdg.QPushButton("Cancel")
        sketchPlanePlotButton = wdg.QPushButton("Preview")
        sketchPlaneAcceptButton = wdg.QPushButton("Accept")
        
        layout.addWidget(sketchPlaneEscapeButton, 9, 0)
        layout.addWidget(sketchPlanePlotButton, 9, 1)
        layout.addWidget(sketchPlaneAcceptButton, 9, 2)

        # callbacks
        sketchPlaneEscapeButton.clicked.connect(self.escape_sketch_plane)
        sketchPlanePlotButton.clicked.connect(self.preview_sketch_plane)
        sketchPlaneAcceptButton.clicked.connect(self.accept_sketch_plane)
        
        self.clear_option_layout()

        self.optionLayout.addWidget(self.sketchPlaneContainer)

        self.sketch_plane_dialogue_displayed = True
        self.sketch_dialogue_displayed = False


    def escape_sketch_plane(self):
        self.sketchPlaneContainer.deleteLater()
        self.sketch_plane_dialogue_displayed = False

        # TODO: WIPE CANVAS AND REDRAW ACTUAL FEATURES ONLY
        self.sc.axes.cla()
        self.set_labels()
        self.set_limits()

        self.drawFeatures()


    def accept_sketch_plane(self):
        self.sketchPlaneContainer.deleteLater()
        self.sketch_plane_dialogue_displayed = False

        # TODO: WIPE CANVAS AND REDRAW ACTUAL FEATURES ONLY
        self.sc.axes.cla()
        self.set_labels()
        self.set_limits()

        self.featureTree.sketchPlanes.append(self.tempSketchPlane)
        self.tempSketchPlane = None

        self.drawFeatures()


    def preview_sketch_plane_initial(self):
        self.sc.axes.cla()
        match self.selectedSketchPlane:
            case 'xy':
                p0 = sp.Matrix([[0, 0, 0]])
                p1 = sp.Matrix([[0, 100, 0]])

                q0 = sp.Matrix([[100, 0, 0]])
                q1 = sp.Matrix([[100, 100, 0]])
            case 'yz':
                p0 = sp.Matrix([[0, 0, 0]])
                p1 = sp.Matrix([[0, 0, 100]])

                q0 = sp.Matrix([[0, 100, 0]])
                q1 = sp.Matrix([[0, 100, 100]])
            case 'xz':
                p0 = sp.Matrix([[0, 0, 0]])
                p1 = sp.Matrix([[0, 0, 100]])

                q0 = sp.Matrix([[100, 0, 0]])
                q1 = sp.Matrix([[100, 0, 100]])
            case _:
                return
        
        sketchPlane = RuledSurface(f"Plane{len(self.featureTree.sketchPlanes)}", 10, p0, p1, q0, q1)

        sketchPlaneTraces = sketchPlane.generate_traces()

        self.sc.axes.cla()
        for trace in sketchPlaneTraces:
            self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color='blue', alpha=0.3)

        self.set_labels()
        self.set_limits()
        self.sc.figure.canvas.draw()

        self.tempSketchPlane = sketchPlane


    def preview_sketch_plane(self):
        self.sc.axes.cla()
        match self.selectedSketchPlane:
            case 'xy':
                p0 = sp.Matrix([[0, 0, 0]])
                p1 = sp.Matrix([[0, 100, 0]])

                q0 = sp.Matrix([[100, 0, 0]])
                q1 = sp.Matrix([[100, 100, 0]])
            case 'yz':
                p0 = sp.Matrix([[0, 0, 0]])
                p1 = sp.Matrix([[0, 0, 100]])

                q0 = sp.Matrix([[0, 100, 0]])
                q1 = sp.Matrix([[0, 100, 100]])
            case 'xz':
                p0 = sp.Matrix([[0, 0, 0]])
                p1 = sp.Matrix([[0, 0, 100]])

                q0 = sp.Matrix([[100, 0, 0]])
                q1 = sp.Matrix([[100, 0, 100]])
            case _:
                return
        
        sketchPlane = RuledSurface(f"Plane{len(self.featureTree.sketchPlanes)}", 10, p0, p1, q0, q1)

        self.sanitizeSketchPlaneInput()

        offset = Offset(float(self.xOffsetField.text()), float(self.yOffsetField.text()), float(self.zOffsetField.text()))

        print(f"offset: {offset.x}, {offset.y}, {offset.z}")

        sketchPlane.translate(offset)

        sketchPlane.rotate(float(self.alphaField.text()), float(self.betaField.text()), float(self.gammaField.text()))

        sketchPlaneTraces = sketchPlane.generate_traces()

        self.sc.axes.cla()
        for trace in sketchPlaneTraces:
            self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color='blue', alpha=0.3)

        self.set_labels()
        self.set_limits()
        self.sc.figure.canvas.draw()

        self.tempSketchPlane = sketchPlane


    def xy_button_callback(self, layout:wdg.QGridLayout):
        self.selectedSketchPlane = 'xy'
        print('xy')
        self.add_angle_widgets(layout)
        self.add_offset_widgets(layout)
        self.preview_sketch_plane_initial()


    def yz_button_callback(self, layout:wdg.QGridLayout):
        self.selectedSketchPlane = 'yz'
        print('yz')
        self.add_angle_widgets(layout)
        self.add_offset_widgets(layout)
        self.preview_sketch_plane_initial()


    def xz_button_callback(self, layout:wdg.QGridLayout):
        self.selectedSketchPlane = 'xz'
        print('xz')
        self.add_angle_widgets(layout)
        self.add_offset_widgets(layout)
        self.preview_sketch_plane_initial()


    def add_angle_widgets(self, layout:wdg.QGridLayout):
        if self.angle_widgets_displayed == True:
            return
        alphaLabel = wdg.QLabel("alpha")
        betaLabel = wdg.QLabel("beta")
        gammaLabel = wdg.QLabel("gamma")

        self.alphaField = wdg.QLineEdit("0")
        self.betaField = wdg.QLineEdit("0")
        self.gammaField = wdg.QLineEdit("0")

        layout.addWidget(alphaLabel, 2, 0)
        layout.addWidget(betaLabel, 3, 0)
        layout.addWidget(gammaLabel, 4, 0)

        layout.addWidget(self.alphaField, 2, 1)
        layout.addWidget(self.betaField, 3, 1)
        layout.addWidget(self.gammaField, 4, 1)

        self.angle_widgets_displayed = True


    def add_offset_widgets(self, layout:wdg.QGridLayout):
        if self.offset_widgets_displayed == True:
            return
        xOffset = wdg.QLabel("X offset")
        yOffset = wdg.QLabel("Y offset")
        zOffset = wdg.QLabel("Z offset")

        self.xOffsetField = wdg.QLineEdit("0")
        self.yOffsetField = wdg.QLineEdit("0")
        self.zOffsetField = wdg.QLineEdit("0")

        layout.addWidget(xOffset, 5, 0)
        layout.addWidget(yOffset, 6, 0)
        layout.addWidget(zOffset, 7, 0)

        layout.addWidget(self.xOffsetField, 5, 1)
        layout.addWidget(self.yOffsetField, 6, 1)
        layout.addWidget(self.zOffsetField, 7, 1)

        self.offset_widgets_displayed = True


    def set_labels(self):
        self.sc.axes.set_xlabel("X")
        self.sc.axes.set_ylabel("Y")
        self.sc.axes.set_zlabel("Z")

    
    def set_limits(self):
        self.sc.axes.set_xlim((0, 100))
        self.sc.axes.set_ylim((0, 100))
        self.sc.axes.set_zlim((0, 100))
    

    def sanitizeSketchPlaneInput(self):
        return
    

    def drawFeatures(self):
        self.sc.axes.cla()
        for sketchPlane in self.featureTree.sketchPlanes:
            sketchPlaneTraces = sketchPlane.generate_traces()

            sp.pretty_print(sketchPlane.S_u_w)

            for trace in sketchPlaneTraces:
                self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color='blue', alpha=0.1)

        self.set_labels()
        self.set_limits()
        self.sc.figure.canvas.draw()


if __name__ == "__main__":
    app = wdg.QApplication(sys.argv)
    app.setStyle('windowsvista')
    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec())