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

from sketchPlane import SketchPlane
from CADUtils import Offset


class FeatureTree:
    def __init__(self):
        self.sketchPlanes = []
        self.sketches = []
        self.surfaces = []


class MplCanvas3d(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(projection='3d')
        super().__init__(self.fig)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
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
        self.sketch_displayed = False
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False

        # setup plot
        # self.sc = MplCanvas3d()

        # self.set_labels()
        # self.set_limits()

        # self.mplContainer.addWidget(self.sc)
        self.setup_3d_plot()

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


    def setup_3d_plot(self):
        self.clear_mpl_container()
        self.sc = MplCanvas3d()
        
        self.set_labels_3d()
        self.set_limits_3d()

        self.drawFeatures()

        self.mplContainer.addWidget(self.sc)


    def setup_2d_plot(self, initial_orientation : str):
        self.clear_mpl_container()
        self.sc = MplCanvas()

        self.set_labels_2d(initial_orientation)
        self.set_limits_2d()

        self.mplContainer.addWidget(self.sc)


    def clear_option_layout(self):
        for i in reversed(range(self.optionLayout.count())): 
            self.optionLayout.itemAt(i).widget().setParent(None)


    def clear_mpl_container(self):
        for i in reversed(range(self.mplContainer.count())): 
            self.mplContainer.itemAt(i).widget().setParent(None)


    def sketch_dialogue(self):
        if self.sketch_dialogue_displayed == True: 
            return
        
        self.setup_3d_plot()
        
        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        self.clear_option_layout()

        # sketch plane list
        sketchPlaneListLabel = wdg.QLabel("Select sketch plane")
        sketchPlaneList = wdg.QListWidget()

        names = [plane.name for plane in self.featureTree.sketchPlanes]

        sketchPlaneList.addItems(names)

        sketchPlaneList.itemPressed.connect(lambda: self.sketch_plane_highlighted(sketchPlaneList.selectedItems()))

        # buttons
        selectButton = wdg.QPushButton("Start Sketch")
        deleteButton = wdg.QPushButton("Delete Sketch")

        layout.addWidget(sketchPlaneListLabel, 0, 0)
        layout.addWidget(sketchPlaneList, 1, 0, 1, 2)
        layout.addWidget(deleteButton, 2, 0)
        layout.addWidget(selectButton, 2, 1)

        # button callbacks
        deleteButton.clicked.connect(lambda: self.deleteSketchPlane(sketchPlaneList, sketchPlaneList.selectedItems()))
        selectButton.clicked.connect(lambda: self.start_sketch(sketchPlaneList.selectedItems()))

        # end
        self.optionLayout.addWidget(self.sketchContainer)

        self.sketch_displayed = False
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = True


    def sketch_plane_highlighted(self, selectedItem):
        if len(selectedItem) == 0:
            return
        
        for sketchPlane in self.featureTree.sketchPlanes:
            if sketchPlane.name == selectedItem[0].text():
                sketchPlane.color = 'orange'
            
            else: sketchPlane.color = 'blue'

        self.setup_3d_plot()


    def start_sketch(self, selectedItem):
        if len(selectedItem) == 0:
            return
        
        selectedSketchPlane = [sketchPlane for sketchPlane in self.featureTree.sketchPlanes if sketchPlane.name == selectedItem[0].text()][0]

        selectedSketchPlane : SketchPlane

        print(selectedSketchPlane.name)

        self.clear_option_layout()
        self.sketchContainer.deleteLater()

        self.setup_2d_plot(selectedSketchPlane.initial_orientation)

        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        straightLineButton = wdg.QPushButton("Straight Line")
        splineButton = wdg.QPushButton("Spline")
        bezierButton = wdg.QPushButton("Bezier Curve")

        layout.addWidget(straightLineButton, 0, 0)
        layout.addWidget(splineButton, 0, 1)
        layout.addWidget(bezierButton, 0, 2)

        # end
        self.optionLayout.addWidget(self.sketchContainer)

        # state flags
        self.sketch_displayed = True
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False


    def deleteSketchPlane(self, sketchPlaneList, items):
        names = [item.text() for item in items]

        updatedSketchPlanes = [sketchPlane for sketchPlane in self.featureTree.sketchPlanes if sketchPlane.name not in names]
        
        self.featureTree.sketchPlanes = updatedSketchPlanes

        for item in items:
            sketchPlaneList.takeItem(sketchPlaneList.row(item))

        self.drawFeatures()

        # ui flags
        self.sketch_displayed = True
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False


    def sketch_plane_dialogue(self):
        if self.sketch_plane_dialogue_displayed == True: 
            return
        
        self.setup_3d_plot()

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
        self.sketch_displayed = False


    def escape_sketch_plane(self):
        self.sketchPlaneContainer.deleteLater()
        self.sketch_plane_dialogue_displayed = False

        # wipe canvas
        self.sc.axes.cla()
        self.set_labels_3d()
        self.set_limits_3d()

        # draw features
        self.drawFeatures()


    def accept_sketch_plane(self):
        if self.tempSketchPlane is None:
            return
        
        self.sketchPlaneContainer.deleteLater()
        self.sketch_plane_dialogue_displayed = False

        # TODO: WIPE CANVAS AND REDRAW ACTUAL FEATURES ONLY
        self.sc.axes.cla()
        self.set_labels_3d()
        self.set_limits_3d()

        self.featureTree.sketchPlanes.append(self.tempSketchPlane)
        self.tempSketchPlane = None

        self.drawFeatures()


    def preview_sketch_plane_initial(self):
        self.sc.axes.cla()
        match self.selectedSketchPlane:
            case 'xy':
                initial_orientation = 'xy'
                color = 'blue'
                p0 = sp.Matrix([[-100, -100, 0]])
                p1 = sp.Matrix([[-100, 100, 0]])

                q0 = sp.Matrix([[100, -100, 0]])
                q1 = sp.Matrix([[100, 100, 0]])
            case 'yz':
                initial_orientation = 'yz'
                color = 'blue'
                p0 = sp.Matrix([[0, -100, -100]])
                p1 = sp.Matrix([[0, -100, 100]])

                q0 = sp.Matrix([[0, 100, -100]])
                q1 = sp.Matrix([[0, 100, 100]])
            case 'xz':
                initial_orientation = 'xz'
                color = 'blue'
                p0 = sp.Matrix([[-100, 0, -100]])
                p1 = sp.Matrix([[-100, 0, 100]])

                q0 = sp.Matrix([[100, 0, -100]])
                q1 = sp.Matrix([[100, 0, 100]])
            case _:
                return
        
        sketchPlane = SketchPlane(f"Plane{len(self.featureTree.sketchPlanes)}", initial_orientation, 10, p0, p1, q0, q1, color=color)

        sketchPlaneTraces = sketchPlane.generate_traces()

        self.sc.axes.cla()
        for trace in sketchPlaneTraces:
            self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=sketchPlane.color, alpha=0.3)

        self.set_labels_3d()
        self.set_limits_3d()
        self.sc.figure.canvas.draw()

        self.tempSketchPlane = sketchPlane


    def preview_sketch_plane(self):
        self.sc.axes.cla()
        match self.selectedSketchPlane:
            case 'xy':
                initial_orientation = 'xy'
                color='blue'
                p0 = sp.Matrix([[-100, -100, 0]])
                p1 = sp.Matrix([[-100, 100, 0]])

                q0 = sp.Matrix([[100, -100, 0]])
                q1 = sp.Matrix([[100, 100, 0]])
            case 'yz':
                initial_orientation = 'yz'
                color='blue'
                p0 = sp.Matrix([[0, -100, -100]])
                p1 = sp.Matrix([[0, -100, 100]])

                q0 = sp.Matrix([[0, 100, -100]])
                q1 = sp.Matrix([[0, 100, 100]])
            case 'xz':
                initial_orientation = 'xz'
                color='blue'
                p0 = sp.Matrix([[-100, 0, -100]])
                p1 = sp.Matrix([[-100, 0, 100]])

                q0 = sp.Matrix([[100, 0, -100]])
                q1 = sp.Matrix([[100, 0, 100]])
            case _:
                return
        
        sketchPlane = SketchPlane(f"Plane{len(self.featureTree.sketchPlanes)}", initial_orientation, 10, p0, p1, q0, q1, color=color)

        self.sanitizeSketchPlaneInput()

        offset = Offset(float(self.xOffsetField.text()), float(self.yOffsetField.text()), float(self.zOffsetField.text()))

        print(f"offset: {offset.x}, {offset.y}, {offset.z}")

        sketchPlane.translate(offset)

        sketchPlane.rotate(float(self.alphaField.text()), float(self.betaField.text()), float(self.gammaField.text()))

        sketchPlaneTraces = sketchPlane.generate_traces()

        self.sc.axes.cla()
        for trace in sketchPlaneTraces:
            self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=sketchPlane.color, alpha=0.3)

        self.set_labels_3d()
        self.set_limits_3d()
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


    def set_labels_3d(self):
        self.sc.axes.set_xlabel("X")
        self.sc.axes.set_ylabel("Y")
        self.sc.axes.set_zlabel("Z")

    
    def set_limits_3d(self):
        self.sc.axes.set_xlim((-100, 100))
        self.sc.axes.set_ylim((-100, 100))
        self.sc.axes.set_zlim((-100, 100))


    def set_labels_2d(self, initial_orientation : str):
        match initial_orientation:
            case 'xy':
                self.sc.axes.set_xlabel("X")
                self.sc.axes.set_ylabel("Y", rotation=0)
            case 'yz':
                self.sc.axes.set_xlabel("Y")
                self.sc.axes.set_ylabel("Z", rotation=0)
            case 'xz':
                self.sc.axes.set_xlabel("X")
                self.sc.axes.set_ylabel("Z", rotation=0)

    
    def set_limits_2d(self):
        self.sc.axes.set_xlim((-100, 100))
        self.sc.axes.set_ylim((-100, 100))
    

    def sanitizeSketchPlaneInput(self):
        return
    

    def drawFeatures(self):
        self.sc.axes.cla()

        print(self.featureTree.sketchPlanes)

        for sketchPlane in self.featureTree.sketchPlanes:
            sketchPlaneTraces = sketchPlane.generate_traces()

            sp.pretty_print(sketchPlane.S_u_w)

            for trace in sketchPlaneTraces:
                self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=sketchPlane.color, alpha=0.3)

        self.set_labels_3d()
        self.set_limits_3d()
        self.sc.figure.canvas.draw()


if __name__ == "__main__":
    app = wdg.QApplication(sys.argv)
    app.setStyle('windowsvista')
    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec())