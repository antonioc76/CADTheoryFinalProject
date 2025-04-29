import PyQt6 as qt
from PyQt6.QtCore import Qt
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

from CADUtils import Offset
from sketchPlane import SketchPlane
from straightLine import StraightLine
from spline import Spline
from bezierCurve import BezierCurve
from closedUniformBSpline import ClosedUniformBSpline

from cylindricalSurface import CylindricalSurface
from ruledSurface import RuledSurface
from loftedSurface import LoftedSurface
from sweptSurface import SweptSurface

from intersectionCurve import IntersectionCurve


class FeatureTree:
    def __init__(self):
        self.sketchPlanesCount = 0
        self.sketchCount = 0
        self.curveCount = 0
        self.surfaceCount = 0

        self.sketchPlanes = []
        self.sketches = []
        self.curves = []
        self.surfaces = []

    
    def add_sketch_plane(self, sketchPlane:SketchPlane):
        self.sketchPlanes.append(sketchPlane)
        self.sketchPlanesCount += 1


    def add_curve(self, curve):
        self.curves.append(curve)
        self.curveCount += 1

    
    def add_surface(self, surface):
        self.surfaces.append(surface)
        self.surfaceCount += 1


class MplCanvas3d(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=4, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(projection='3d')
        super().__init__(self.fig)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=4, height=4, dpi=100):
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
        self.surface_dialogue_displayed = False
        self.intersection_dialogue_displayed = False

        # setup plot
        self.setup_3d_plot()

        self.show()

        self.selectedSketchPlane = None

        # setup intellisense for ui objects from .ui file
        self.sketchPlaneButton: wdg.QPushButton
        self.sketchButton: wdg.QPushButton
        self.surfaceButton: wdg.QPushButton
        self.surfaceIntersectionButton: wdg.QPushButton

        # setup callback functions
        self.sketchPlaneButton.clicked.connect(self.sketch_plane_dialogue)
        self.sketchButton.clicked.connect(self.sketch_dialogue)
        self.surfaceButton.clicked.connect(self.surface_dialogue)
        self.surfaceIntersectionButton.clicked.connect(self.intersection_dialogue)


    def setup_3d_plot(self):
        self.clear_mpl_container()
        self.sc = MplCanvas3d()
        
        self.set_labels_3d()
        self.set_limits_3d()

        self.draw_features()

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

        for i in reversed(range(self.mplContainer.count())): 
            self.mplContainer.itemAt(i).widget().setParent(None)        


    def intersection_dialogue(self):
        self.clear_option_layout()

        if self.intersection_dialogue_displayed == True:
            return
        
        self.color_all_sketchplanes_blue()

        self.color_all_curves_blue()

        self.color_all_surfaces_green()

        self.setup_3d_plot()

        self.angle_widgets_displayed = False
        self.offset_widgets_displayed = False

        self.intersectionContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.intersectionContainer)

        surfaceLabel1 = wdg.QLabel("select surface 1")
        surfaceList1 = wdg.QListWidget()

        surfaceLabel2 = wdg.QLabel("select surface 2")
        surfaceList2 = wdg.QListWidget()

        names = [curve.name for curve in self.featureTree.surfaces]

        surfaceList1.addItems(names)
        surfaceList2.addItems(names)

        layout.addWidget(surfaceLabel1, 1, 0, 1, 4)
        layout.addWidget(surfaceList1, 2, 0, 1, 4)
        layout.addWidget(surfaceLabel2, 3, 0, 1, 4)
        layout.addWidget(surfaceList2, 4, 0, 1, 4)

        intersectionEscapeButton = wdg.QPushButton("Cancel")
        intersectionPlotButton = wdg.QPushButton("Preview")
        intersectionAcceptButton = wdg.QPushButton("Accept")

        layout.addWidget(intersectionEscapeButton, 9, 0)
        layout.addWidget(intersectionPlotButton, 9, 1)
        layout.addWidget(intersectionAcceptButton, 9, 2)

        surfaceList1.itemClicked.connect(lambda: self.surface_highlighted(surfaceList1.selectedItems(), surfaceList2.selectedItems()))
        surfaceList2.itemClicked.connect(lambda: self.surface_highlighted(surfaceList1.selectedItems(), surfaceList2.selectedItems()))

        # bottom button callbacks
        intersectionEscapeButton.clicked.connect(lambda: self.escape_container(self.intersectionContainer))
        intersectionPlotButton.clicked.connect(lambda: self.preview_intersection(surfaceList1.selectedItems(), surfaceList2.selectedItems()))
        intersectionAcceptButton.clicked.connect(lambda: self.accept_intersection(surfaceList1.selectedItems(), surfaceList2.selectedItems()))

        # flags
        self.surface_dialogue_displayed = False
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False
        self.sketch_displayed = False
        self.intersection_dialogue_displayed = True

        self.optionLayout.addWidget(self.intersectionContainer)


    def surface_highlighted(self, selectedItems1, selectedItems2):
        orangeSurfaces = []
        purpleSurfaces = []
        if len(selectedItems1) != 0:
            for surface in self.featureTree.surfaces:
                if surface.name == selectedItems1[0].text():
                    orangeSurfaces.append(surface)

        if len(selectedItems2) != 0:
            for surface in self.featureTree.surfaces:
                if surface.name == selectedItems2[0].text():
                    purpleSurfaces.append(surface)

        greenSurfaces = list(set(self.featureTree.surfaces) - set(orangeSurfaces) - set(purpleSurfaces))

        for surface in orangeSurfaces:
            surface.color = 'orange'

        for surface in purpleSurfaces:
            surface.color = 'purple'

        for surface in greenSurfaces:
            surface.color = 'green'

        self.setup_3d_plot()


    def preview_intersection(self, selectedItems1, selectedItems2):
        p0 = sp.Matrix([[-100, -100, 0]])
        p1 = sp.Matrix([[-100, 100, 0]])

        q0 = sp.Matrix([[100, -100, 0]])
        q1 = sp.Matrix([[100, 100, 0]])

        sketchPlane = SketchPlane(f"Plane{self.featureTree.sketchPlanesCount}", 'xy', 10, p0, p1, q0, q1, color='blue')

        if len(selectedItems1) == 0:
            print('no selected first surface')
            return
        
        if len(selectedItems2) == 0:
            print('no selected second surface')
            return
        
        for surface in self.featureTree.surfaces:
            if surface.name == selectedItems1[0].text():
                selectedSurface1 = surface
            elif surface.name == selectedItems2[0].text():
                selectedSurface2 = surface

        if selectedSurface1 is None or selectedSurface1 is None:
            return
        
        intersectionCurve = IntersectionCurve(f"curve{self.featureTree.curveCount}", selectedSurface1, selectedSurface2, 100, 0.25, sketchPlane)
    
        intersectionCurveTrace = intersectionCurve.curve_itself.generate_trace()

        self.setup_3d_plot()

        self.sc.axes.plot(intersectionCurveTrace[:, 0], intersectionCurveTrace[:, 1], intersectionCurveTrace[:, 2])

        self.sc.figure.canvas.draw()


    def accept_intersection(self, selectedItems1, selectedItems2):
        p0 = sp.Matrix([[-100, -100, 0]])
        p1 = sp.Matrix([[-100, 100, 0]])

        q0 = sp.Matrix([[100, -100, 0]])
        q1 = sp.Matrix([[100, 100, 0]])

        sketchPlane = SketchPlane(f"Plane{self.featureTree.sketchPlanesCount}", 'xy', 10, p0, p1, q0, q1, color='blue')

        if len(selectedItems1) == 0:
            print('no selected first surface')
            return
        
        if len(selectedItems2) == 0:
            print('no selected second surface')
            return
        
        for surface in self.featureTree.surfaces:
            if surface.name == selectedItems1[0].text():
                selectedSurface1 = surface
            elif surface.name == selectedItems2[0].text():
                selectedSurface2 = surface

        if selectedSurface1 is None or selectedSurface1 is None:
            return
        
        intersectionCurve = IntersectionCurve(f"curve{self.featureTree.curveCount}", selectedSurface1, selectedSurface2, 100, 0.25, sketchPlane)
    
        self.featureTree.add_curve(intersectionCurve.curve_itself)

        self.draw_features()

        self.color_all_sketchplanes_blue()

        self.color_all_curves_blue()
        
        self.color_all_surfaces_green()

        self.setup_3d_plot()

        self.clear_option_layout()


    def surface_dialogue(self):
        self.clear_option_layout()

        self.surface_type = None

        if self.surface_dialogue_displayed == True: 
            return

        self.color_all_sketchplanes_blue()

        self.color_all_curves_blue()

        self.color_all_surfaces_green()
        
        self.setup_3d_plot()

        self.angle_widgets_displayed = False
        self.offset_widgets_displayed = False

        # labels and fields
        depthLabel = wdg.QLabel("Extrusion Depth: ")

        depthField = wdg.QLineEdit()

        self.surfaceContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.surfaceContainer)
        
        # surface selection
        cylindricalButton = wdg.QPushButton("Extruded Surface")
        ruledButton = wdg.QPushButton("Ruled Surface")
        loftButton = wdg.QPushButton("Loft Surface")
        sweptButton = wdg.QPushButton("Swept Surface")
        deleteCurvesButton = wdg.QPushButton("Delete Curves")

        layout.addWidget(cylindricalButton, 0, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ruledButton, 0, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(loftButton, 0, 2, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sweptButton, 1, 2, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(deleteCurvesButton, 1, 3, Qt.AlignmentFlag.AlignCenter)

        curveLabel1 = wdg.QLabel("Select Curve")
        curveList1 = wdg.QListWidget()

        curveLabel2 = wdg.QLabel("Select Curve")
        curveList2 = wdg.QListWidget()

        curveLabel3 = wdg.QLabel("Select Curve")
        curveList3 = wdg.QListWidget()

        curveLabel4 = wdg.QLabel("Select Curve")
        curveList4 = wdg.QListWidget()

        curveLabel5 = wdg.QLabel("Select Curve")
        curveList5 = wdg.QListWidget()

        curveList1.setSelectionMode(wdg.QAbstractItemView.SelectionMode.ExtendedSelection)
        curveList2.setSelectionMode(wdg.QAbstractItemView.SelectionMode.ExtendedSelection)

        cylindricalButton.clicked.connect(lambda: self.cylindricalCalled(layout, depthLabel, depthField, curveLabel1, curveList1))
        ruledButton.clicked.connect(lambda: self.ruledCalled(layout, curveLabel1, curveList1, curveLabel2, curveList2))
        loftButton.clicked.connect(lambda: self.loftCalled(curveLabel1, curveLabel2, curveLabel3, curveLabel4, curveLabel5, curveList1, curveList2, curveList3, curveList4, curveList5))
        sweptButton.clicked.connect(lambda: self.sweptCalled(layout, curveLabel1, curveList1, curveLabel2, curveList2))

        deleteCurvesButton.clicked.connect(lambda: self.deleteCurvesCalled(layout, curveLabel1, curveList1))

        surfaceEscapeButton = wdg.QPushButton("Cancel")
        surfacePlotButton = wdg.QPushButton("Preview")
        surfaceAcceptButton = wdg.QPushButton("Accept")

        layout.addWidget(surfaceEscapeButton, 9, 0)
        layout.addWidget(surfacePlotButton, 9, 1)
        layout.addWidget(surfaceAcceptButton, 9, 2)

        # callbacks
        surfaceEscapeButton.clicked.connect(lambda: self.escape_container(self.surfaceContainer))
        surfacePlotButton.clicked.connect(lambda: self.preview_surface(curveList1, curveList2, depthField.text(), self.surface_type))
        surfaceAcceptButton.clicked.connect(lambda: self.accept_surface(curveList1, curveList2, depthField.text(), self.surface_type))
        
        self.clear_option_layout()

        self.optionLayout.addWidget(self.surfaceContainer)

        # flags
        self.surface_dialogue_displayed = True
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False
        self.sketch_displayed = False
        self.intersection_dialogue_displayed = False


    def deleteCurvesCalled(self, layout, curveLabel1, curveList1):
        names = [curve.name for curve in self.featureTree.curves]

        curveLabel1.setText("select curve for deletion")
        curveList1.addItems(names)

        layout.addWidget(curveLabel1, 1, 0, 1, 4)
        layout.addWidget(curveList1, 2, 0, 1, 4)

        deleteButton = wdg.QPushButton("delete")

        layout.addWidget(deleteButton)

        # callbacks
        curveList1.itemPressed.connect(lambda: self.curve_highlighted(curveList1.selectedItems()))
        deleteButton.clicked.connect(lambda: self.deleteCurves(curveList1.selectedItems()))


    def deleteCurves(self, selectedItems):
        if len(selectedItems) == 0:
            return
        
        forDeletion = []
        for curve in self.featureTree.curves:
            for item in selectedItems:
                if curve.name == item.text():
                    forDeletion.append(curve)

        self.featureTree.curves = list(set(self.featureTree.curves) - set(forDeletion))

        self.clear_option_layout()

        self.setup_3d_plot()

        self.draw_features()


    def loftCalled(self, curveLabel1, curveLabel2, curveLabel3, curveLabel4, curveLabel5, curveList1, curveList2, curveList3, curveList4, curveList5):
        self.clear_option_layout()
        
        self.surfaceContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.surfaceContainer)

        numberOfCurvesLabel = wdg.QLabel("Select number of curves:")
        numberOfCurvesDropdown = wdg.QComboBox()
        numberOfCurvesDropdown.addItems(['2', '3', '4', '5'])
        acceptNumberOfCurvesButton = wdg.QPushButton("Accept")

        layout.addWidget(numberOfCurvesLabel, 1, 0, 1, 1)
        layout.addWidget(numberOfCurvesDropdown, 1, 1, 1, 1)
        layout.addWidget(acceptNumberOfCurvesButton, 1, 2, 1, 1)

        self.color_all_sketchplanes_blue()

        self.color_all_curves_blue()

        self.color_all_surfaces_green()

        self.setup_3d_plot()

        acceptNumberOfCurvesButton.clicked.connect(lambda: self.loftCurveNumberAccepted(numberOfCurvesDropdown, curveLabel1, curveLabel2, curveLabel3, curveLabel4, curveLabel5, curveList1, curveList2, curveList3, curveList4, curveList5))

        self.optionLayout.addWidget(self.surfaceContainer)

    
    def loftCurveNumberAccepted(self, numberOfCurvesDropdown, curveLabel1, curveLabel2, curveLabel3, curveLabel4, curveLabel5, curveList1, curveList2, curveList3, curveList4, curveList5):        
        numberOfCurves = int(numberOfCurvesDropdown.currentText())

        self.clear_option_layout()
        self.surfaceContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.surfaceContainer)

        match numberOfCurves:
            case 2:
                curveList1.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList2.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                layout.addWidget(curveLabel1, 0, 0, 1, 3)
                layout.addWidget(curveList1, 1, 0, 1, 3)
                layout.addWidget(curveLabel2, 2, 0, 1, 3)
                layout.addWidget(curveList2, 3, 0, 1, 3)
                
                names = [curve.name for curve in self.featureTree.curves]

                curveList1.addItems(names)
                curveList2.addItems(names)

            case 3:
                curveList1.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList2.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList3.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                layout.addWidget(curveLabel1, 0, 0, 1, 3)
                layout.addWidget(curveList1, 1, 0, 1, 3)
                layout.addWidget(curveLabel2, 2, 0, 1, 3)
                layout.addWidget(curveList2, 3, 0, 1, 3)
                layout.addWidget(curveLabel3, 4, 0, 1, 3)
                layout.addWidget(curveList3, 5, 0, 1, 3)

                names = [curve.name for curve in self.featureTree.curves]

                curveList1.addItems(names)
                curveList2.addItems(names)
                curveList3.addItems(names)

            case 4:
                curveList1.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList2.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList3.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList4.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                layout.addWidget(curveLabel1, 0, 0, 1, 3)
                layout.addWidget(curveList1, 1, 0, 1, 3)
                layout.addWidget(curveLabel2, 2, 0, 1, 3)
                layout.addWidget(curveList2, 3, 0, 1, 3)
                layout.addWidget(curveLabel3, 4, 0, 1, 3)
                layout.addWidget(curveList3, 5, 0, 1, 3)
                layout.addWidget(curveLabel4, 6, 0, 1, 3)
                layout.addWidget(curveList4, 7, 0, 1, 3)

                names = [curve.name for curve in self.featureTree.curves]

                curveList1.addItems(names)
                curveList2.addItems(names)
                curveList3.addItems(names)
                curveList4.addItems(names)

            case 5:
                curveList1.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList2.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList3.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList4.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                curveList5.setSelectionMode(wdg.QAbstractItemView.SelectionMode.SingleSelection)
                layout.addWidget(curveLabel1, 0, 0, 1, 3)
                layout.addWidget(curveList1, 1, 0, 1, 3)
                layout.addWidget(curveLabel2, 2, 0, 1, 3)
                layout.addWidget(curveList2, 3, 0, 1, 3)
                layout.addWidget(curveLabel3, 4, 0, 1, 3)
                layout.addWidget(curveList3, 5, 0, 1, 3)
                layout.addWidget(curveLabel4, 6, 0, 1, 3)
                layout.addWidget(curveList4, 7, 0, 1, 3)
                layout.addWidget(curveLabel5, 8, 0, 1, 3)
                layout.addWidget(curveList5, 9, 0, 1, 3)

                names = [curve.name for curve in self.featureTree.curves]

                curveList1.addItems(names)
                curveList2.addItems(names)
                curveList3.addItems(names)
                curveList4.addItems(names)
                curveList5.addItems(names)

        cancelButton = wdg.QPushButton("Cancel")
        previewButton = wdg.QPushButton("Preview")
        acceptButton = wdg.QPushButton("Accept")

        layout.addWidget(cancelButton, 10, 0, 1, 1)
        layout.addWidget(previewButton, 10, 1, 1, 1)
        layout.addWidget(acceptButton, 10, 2, 1, 1)

        # callbacks
        curveList1.itemPressed.connect(lambda: self.loft_curves_highlighted(numberOfCurves, curveList1.selectedItems(), curveList2.selectedItems(), curveList3.selectedItems(), curveList4.selectedItems(), curveList5.selectedItems()))
        curveList2.itemPressed.connect(lambda: self.loft_curves_highlighted(numberOfCurves, curveList1.selectedItems(), curveList2.selectedItems(), curveList3.selectedItems(), curveList4.selectedItems(), curveList5.selectedItems()))
        curveList3.itemPressed.connect(lambda: self.loft_curves_highlighted(numberOfCurves, curveList1.selectedItems(), curveList2.selectedItems(), curveList3.selectedItems(), curveList4.selectedItems(), curveList5.selectedItems()))
        curveList4.itemPressed.connect(lambda: self.loft_curves_highlighted(numberOfCurves, curveList1.selectedItems(), curveList2.selectedItems(), curveList3.selectedItems(), curveList4.selectedItems(), curveList5.selectedItems()))
        curveList5.itemPressed.connect(lambda: self.loft_curves_highlighted(numberOfCurves, curveList1.selectedItems(), curveList2.selectedItems(), curveList3.selectedItems(), curveList4.selectedItems(), curveList5.selectedItems()))

        cancelButton.clicked.connect(lambda: self.escape_container(self.surfaceContainer))
        previewButton.clicked.connect(lambda: self.preview_loft(numberOfCurves, curveLabel1, curveLabel2, curveLabel3, curveLabel4, curveLabel5, curveList1, curveList2, curveList3, curveList4, curveList5))
        acceptButton.clicked.connect(lambda: self.accept_loft(numberOfCurves, curveLabel1, curveLabel2, curveLabel3, curveLabel4, curveLabel5, curveList1, curveList2, curveList3, curveList4, curveList5))

        self.optionLayout.addWidget(self.surfaceContainer)


    def preview_loft(self, numberOfCurves, curveLabel1, curveLabel2, curveLabel3, curveLabel4, curveLabel5, curveList1, curveList2, curveList3, curveList4, curveList5):
        
        selectedCurves = []
        match numberOfCurves:
            case 2:
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                if len(curveList2.selectedItems()) == 0:
                    print('no curves')
                    return
                
                for curve in self.featureTree.curves:
                    if curve.name == curveList1.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList2.selectedItems()[0].text():
                        selectedCurves.append(curve)
            case 3:
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList2.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList3.selectedItems()) == 0:
                    print('no curves')
                    return
                
                for curve in self.featureTree.curves:
                    if curve.name == curveList1.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList2.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList3.selectedItems()[0].text():
                        selectedCurves.append(curve)

            case 4:
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList2.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList3.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList4.selectedItems()) == 0:
                    print('no curves')
                    return
                
                for curve in self.featureTree.curves:
                    if curve.name == curveList1.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList2.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList3.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList4.selectedItems()[0].text():
                        selectedCurves.append(curve)

            case 5:
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList2.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList3.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList4.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList5.selectedItems()) == 0:
                    print('no curves')
                    return
                
                for curve in self.featureTree.curves:
                    if curve.name == curveList1.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList2.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList3.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList4.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList5.selectedItems()[0].text():
                        selectedCurves.append(curve)

        loftedSurface = LoftedSurface(f"loft{self.featureTree.surfaceCount}", selectedCurves, 40)

        loftedSurfaceTraces = loftedSurface.generate_traces()

        self.setup_3d_plot()

        for trace in loftedSurfaceTraces:
            self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=loftedSurface.color)

        self.sc.figure.canvas.draw()
    

    def accept_loft(self, numberOfCurves, curveLabel1, curveLabel2, curveLabel3, curveLabel4, curveLabel5, curveList1, curveList2, curveList3, curveList4, curveList5):
        selectedCurves = []
        match numberOfCurves:
            case 2:
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                if len(curveList2.selectedItems()) == 0:
                    print('no curves')
                    return
                
                for curve in self.featureTree.curves:
                    if curve.name == curveList1.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList2.selectedItems()[0].text():
                        selectedCurves.append(curve)
            case 3:
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList2.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList3.selectedItems()) == 0:
                    print('no curves')
                    return
                
                for curve in self.featureTree.curves:
                    if curve.name == curveList1.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList2.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList3.selectedItems()[0].text():
                        selectedCurves.append(curve)

            case 4:
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList2.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList3.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList4.selectedItems()) == 0:
                    print('no curves')
                    return
                
                for curve in self.featureTree.curves:
                    if curve.name == curveList1.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList2.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList3.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList4.selectedItems()[0].text():
                        selectedCurves.append(curve)

            case 5:
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList2.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList3.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList4.selectedItems()) == 0:
                    print('no curves')
                    return
                
                if len(curveList5.selectedItems()) == 0:
                    print('no curves')
                    return
                
                for curve in self.featureTree.curves:
                    if curve.name == curveList1.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList2.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList3.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList4.selectedItems()[0].text():
                        selectedCurves.append(curve)

                for curve in self.featureTree.curves:
                    if curve.name == curveList5.selectedItems()[0].text():
                        selectedCurves.append(curve)

        loftedSurface = LoftedSurface(f"loft{self.featureTree.surfaceCount}", selectedCurves, 40)

        self.featureTree.add_surface(loftedSurface)

        self.clear_mpl_container()

        self.escape_container(self.surfaceContainer)


    def preview_surface(self, curveList1, curveList2, extrusion_depth, surface_type):
        print(curveList1.selectedItems())
        print(curveList2.selectedItems())

        match surface_type:
            case 'cylindrical':
                if len(curveList1.selectedItems()) == 0:
                    print('no curves')
                    return
                
                print(curveList1.selectedItems()[0].text())
            
                selectedCurves = []

                for curve in self.featureTree.curves:
                    for item in curveList1.selectedItems():
                        if curve.name == item.text():
                            selectedCurves.append(curve)

                if selectedCurves is None:
                    print('no selected curve')
                    return
                
                if extrusion_depth is None or extrusion_depth == '':
                    print('no extrusion depth')
                    return

                surfaces = []
                for curve in selectedCurves:
                    surface = CylindricalSurface(f"Surface{self.featureTree.surfaceCount}", curve, 10)
                    surface.scale_q(float(extrusion_depth))

                    surfaces.append(surface)

                print("inside preview surface")

                print(float(extrusion_depth))

                self.setup_3d_plot()

                surface_traces_list = []
                for surface in surfaces:
                    surface_traces = surface.generate_traces()
                    surface_traces_list.append(surface_traces)

                for surface_traces in surface_traces_list:
                    for trace in surface_traces:
                        self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=surface.color, alpha=0.4)

                self.sc.figure.canvas.draw()
            case 'ruled':
                selectedCurves1 = []
                selectedCurves2 = []
                if len(curveList1.selectedItems()) == 0:
                    print('no first curves')
                    return
                
                else:
                    print(curveList1.selectedItems()[0].text())
                
                if len(curveList2.selectedItems()) == 0:
                    print('no second curves')
                    return
                
                else:
                    print(curveList2.selectedItems()[0].text)
                
                for curve in self.featureTree.curves:
                    for item in curveList1.selectedItems():
                        if curve.name == item.text():
                            selectedCurves1.append(curve)

                    for item in curveList2.selectedItems():
                        if curve.name == item.text():
                            selectedCurves2.append(curve)

                if selectedCurves1 is None:
                    print('no selected first curve')
                    return
                
                if selectedCurves2 is None:
                    print('no selected second curve')
                    return

                if selectedCurves1 == selectedCurves2:
                    print('cannot select the same curve')
                    return
                
                if len(selectedCurves1) != len(selectedCurves2):
                    print("Same amount of curves not selected")
                    return
                
                surface_traces_list = []

                for i in range(len(selectedCurves1)):
                    mySurface = RuledSurface(f"Surface{self.featureTree.surfaceCount}", selectedCurves1[i], selectedCurves2[i], 10)
                    surface_traces = mySurface.generate_traces()
                    surface_traces_list.append(surface_traces)

                self.setup_3d_plot()

                for surf_traces in surface_traces_list:
                    for trace in surf_traces:
                        self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=mySurface.color)

                self.sc.figure.canvas.draw()

            case 'swept':
                selectedCurves1 = []
                selectedCurves2 = []
                if len(curveList1.selectedItems()) == 0:
                    print('no first curves')
                    return
                
                else:
                    print(curveList1.selectedItems()[0].text())
                
                if len(curveList2.selectedItems()) == 0:
                    print('no path curves')
                    return
                
                else:
                    print(curveList2.selectedItems()[0].text)
                
                for curve in self.featureTree.curves:
                    for item in curveList1.selectedItems():
                        if curve.name == item.text():
                            selectedCurves1.append(curve)

                    for item in curveList2.selectedItems():
                        if curve.name == item.text():
                            selectedPathCurve = curve

                if selectedCurves1 is None:
                    print('no selected first curve')
                    return
                
                if selectedPathCurve is None:
                    print('no selected path curve')
                    return
                
                surface_traces_list = []

                for i in range(len(selectedCurves1)):
                    mySurface = SweptSurface(f"Surface{self.featureTree.surfaceCount}", selectedCurves1[i], selectedPathCurve, self.sc.axes, False, 10)
                    surface_traces = mySurface.generate_traces()
                    surface_traces_list.append(surface_traces)

                self.setup_3d_plot()

                for surf_traces in surface_traces_list:
                    for trace in surf_traces:
                        self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=mySurface.color)

                self.sc.figure.canvas.draw()



    def accept_surface(self, curveList1, curveList2, extrusion_depth, surface_type):
        match surface_type:
            case 'cylindrical':
                if len(curveList1.selectedItems()) == 0:
                    return
                
                print(curveList1.selectedItems()[0].text())
            
                selectedCurves = []

                for curve in self.featureTree.curves:
                    for item in curveList1.selectedItems():
                        if curve.name == item.text():
                            selectedCurves.append(curve)

                if selectedCurves is None:
                    return
                
                if extrusion_depth is None or extrusion_depth == '':
                    return

                for curve in selectedCurves:
                    surface = CylindricalSurface(f"Surface{self.featureTree.surfaceCount}", curve, 10)
                    surface.scale_q(float(extrusion_depth))
                    self.featureTree.add_surface(surface)

                print(float(extrusion_depth))

                self.clear_mpl_container()

                self.escape_container(self.surfaceContainer)
            case 'ruled':
                selectedCurves1 = []
                selectedCurves2 = []
                if len(curveList1.selectedItems()) == 0:
                    print('no first curves')
                    return
                
                else:
                    print(curveList1.selectedItems()[0].text())
                
                if len(curveList2.selectedItems()) == 0:
                    print('no second curves')
                    return
                
                else:
                    print(curveList2.selectedItems()[0].text)
                
                for curve in self.featureTree.curves:
                    for item in curveList1.selectedItems():
                        if curve.name == item.text():
                            selectedCurves1.append(curve)

                    for item in curveList2.selectedItems():
                        if curve.name == item.text():
                            selectedCurves2.append(curve)

                if selectedCurves1 is None:
                    print('no selected first curve')
                    return
                
                if selectedCurves2 is None:
                    print('no selected second curve')
                    return

                if selectedCurves1 == selectedCurves2:
                    print('cannot select the same curve')
                    return
                
                if len(selectedCurves1) != len(selectedCurves2):
                    print("Same amount of curves not selected")
                    return

                for i in range(len(selectedCurves1)):
                    mySurface = RuledSurface(f"Surface{self.featureTree.surfaceCount}", selectedCurves1[i], selectedCurves2[i], 10)
                    self.featureTree.add_surface(mySurface)

                self.clear_mpl_container()

                self.escape_container(self.surfaceContainer)

            case 'swept':
                selectedCurves1 = []
                selectedCurves2 = []
                if len(curveList1.selectedItems()) == 0:
                    print('no first curves')
                    return
                
                else:
                    print(curveList1.selectedItems()[0].text())
                
                if len(curveList2.selectedItems()) == 0:
                    print('no path curves')
                    return
                
                else:
                    print(curveList2.selectedItems()[0].text)
                
                for curve in self.featureTree.curves:
                    for item in curveList1.selectedItems():
                        if curve.name == item.text():
                            selectedCurves1.append(curve)

                    for item in curveList2.selectedItems():
                        if curve.name == item.text():
                            selectedPathCurve = curve

                if selectedCurves1 is None:
                    print('no selected first curve')
                    return
                
                if selectedPathCurve is None:
                    print('no selected path curve')
                    return

                for i in range(len(selectedCurves1)):
                    mySurface = SweptSurface(f"Surface{self.featureTree.surfaceCount}", selectedCurves1[i], selectedPathCurve, self.sc.axes, False, 10)
                    self.featureTree.add_surface(mySurface)

                self.clear_mpl_container()

                self.escape_container(self.surfaceContainer)

    
    def cylindricalCalled(self, layout, depthLabel, depthField, curveLabel: wdg.QLabel, curveList):
        curveLabel.setText("Select Curves")

        layout.addWidget(depthLabel, 8, 1)
        layout.addWidget(depthField, 8, 2)

        self.color_all_sketchplanes_blue()

        self.color_all_curves_blue()

        self.color_all_surfaces_green()

        self.setup_3d_plot()

        names = [curve.name for curve in self.featureTree.curves]

        curveList.addItems(names)

        layout.addWidget(curveLabel, 1, 0, 1, 2)
        layout.addWidget(curveList, 2, 0, 1, 4)

        # callbacks
        curveList.itemPressed.connect(lambda: self.cylindrical_curves_highlighted(curveList.selectedItems()))

        self.surface_type = 'cylindrical'

    
    def cylindrical_curves_highlighted(self, selectedItems):
        if len(selectedItems) == 0:
            return
        
        orangeCurves = []
        for curve in self.featureTree.curves:
            for item in selectedItems:
                if curve.name == item.text():
                    orangeCurves.append(curve)

        blueCurves = list(set(self.featureTree.curves) - set(orangeCurves))
            
        for curve in orangeCurves:
            curve.color = 'orange'

        for curve in blueCurves:
            curve.color = 'blue'

        self.setup_3d_plot()


    def ruledCalled(self, layout, curveLabel1: wdg.QLabel, curveList1, curveLabel2: wdg.QLabel, curveList2):
        curveLabel1.setText("Select First Curve")

        curveLabel2.setText("Select Second Curve")

        names = [curve.name for curve in self.featureTree.curves]

        curveList1.addItems(names)
        curveList2.addItems(names)

        layout.addWidget(curveLabel1, 1, 0, 1, 4)
        layout.addWidget(curveList1, 2, 0, 1, 4)

        layout.addWidget(curveLabel2, 3, 0, 1, 4)
        layout.addWidget(curveList2, 4, 0, 1, 4)

        curveList1.itemPressed.connect(lambda: self.ruled_curves_highlighted(curveList1.selectedItems(), curveList2.selectedItems()))
        curveList2.itemPressed.connect(lambda: self.ruled_curves_highlighted(curveList1.selectedItems(), curveList2.selectedItems()))

        self.surface_type = 'ruled'


    def ruled_curves_highlighted(self, selectedItems1, selectedItems2):
        if len(selectedItems1) == 0 and len(selectedItems2):
            return
        
        orangeCurves = []
        for curve in self.featureTree.curves:
            for item in selectedItems1:
                if curve.name == item.text():
                    orangeCurves.append(curve)

        greenCurves = []
        for curve in self.featureTree.curves:
            for item in selectedItems2:
                if curve.name == item.text():
                    greenCurves.append(curve)

        blueCurves = list(set(self.featureTree.curves) - set(orangeCurves) - set(greenCurves))
            
        for curve in orangeCurves:
            curve.color = 'orange'

        for curve in greenCurves:
            curve.color = 'green'

        for curve in blueCurves:
            curve.color = 'blue'

        self.setup_3d_plot()

    
    def loft_curves_highlighted(self, numberOfCurves, selectedItems1, selectedItems2, selectedItems3, selectedItems4, selectedItems5):
        
        print(selectedItems1)
        print(selectedItems2)

        orangeCurves = []
        greenCurves = []
        purpleCurves = []
        yellowCurves = []
        redCurves = []
        match numberOfCurves:
            case 2:
                if len(selectedItems1) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems1[0].text():
                            orangeCurves.append(curve)
                if len(selectedItems2) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems2[0].text():
                            greenCurves.append(curve)
            case 3:
                if len(selectedItems1) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems1[0].text():
                            orangeCurves.append(curve)
                if len(selectedItems2) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems2[0].text():
                            greenCurves.append(curve)

                if len(selectedItems3) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems3[0].text():
                            purpleCurves.append(curve)
            case 4:
                if len(selectedItems1) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems1[0].text():
                            orangeCurves.append(curve)
                if len(selectedItems2) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems2[0].text():
                            greenCurves.append(curve)

                if len(selectedItems3) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems3[0].text():
                            purpleCurves.append(curve)

                if len(selectedItems4):
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems4[0].text():
                            yellowCurves.append(curve)
            case 5:
                if len(selectedItems1) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems1[0].text():
                            orangeCurves.append(curve)
                if len(selectedItems2) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems2[0].text():
                            greenCurves.append(curve)

                if len(selectedItems3) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems3[0].text():
                            purpleCurves.append(curve)

                if len(selectedItems4):
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems4[0].text():
                            yellowCurves.append(curve)

                if len(selectedItems5) != 0:
                    for curve in self.featureTree.curves:
                        if curve.name == selectedItems5[0].text():
                            redCurves.append(curve)

        blueCurves = list(set(self.featureTree.curves) - set(orangeCurves) - set(greenCurves) - set(purpleCurves) - set(yellowCurves) - set(redCurves))
            
        for curve in orangeCurves:
            curve.color = 'orange'

        for curve in greenCurves:
            curve.color = 'green'

        for curve in purpleCurves:
            curve.color = 'purple'

        for curve in yellowCurves:
            curve.color = 'yellow'

        for curve in redCurves:
            curve.color = 'red'

        for curve in blueCurves:
            curve.color = 'blue'

        self.setup_3d_plot()


    def sweptCalled(self, layout, curveLabel1: wdg.QLabel, curveList1, curveLabel2: wdg.QLabel, curveList2):
        curveLabel1.setText("Select First Curve")

        curveLabel2.setText("Select Path Curve")

        names = [curve.name for curve in self.featureTree.curves]

        curveList1.addItems(names)
        curveList2.addItems(names)

        layout.addWidget(curveLabel1, 1, 0, 1, 4)
        layout.addWidget(curveList1, 2, 0, 1, 4)

        layout.addWidget(curveLabel2, 3, 0, 1, 4)
        layout.addWidget(curveList2, 4, 0, 1, 4)

        curveList1.itemPressed.connect(lambda: self.swept_curves_highlighted(curveList1.selectedItems(), curveList2.selectedItems()))
        curveList2.itemPressed.connect(lambda: self.swept_curves_highlighted(curveList1.selectedItems(), curveList2.selectedItems()))

        self.surface_type = 'swept'

    
    def swept_curves_highlighted(self, selectedItems1, selectedItems2):
        if len(selectedItems1) == 0 and len(selectedItems2):
            return
        
        orangeCurves = []
        for curve in self.featureTree.curves:
            for item in selectedItems1:
                if curve.name == item.text():
                    orangeCurves.append(curve)

        greenCurves = []
        for curve in self.featureTree.curves:
            for item in selectedItems2:
                if curve.name == item.text():
                    greenCurves.append(curve)

        blueCurves = list(set(self.featureTree.curves) - set(orangeCurves) - set(greenCurves))
            
        for curve in orangeCurves:
            curve.color = 'orange'

        for curve in greenCurves:
            curve.color = 'green'

        for curve in blueCurves:
            curve.color = 'blue'

        self.setup_3d_plot()


    def sketch_dialogue(self):
        if self.sketch_dialogue_displayed == True: 
            return

        self.color_all_sketchplanes_blue()

        self.color_all_curves_blue()

        self.color_all_surfaces_green()

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
        deleteButton = wdg.QPushButton("Delete Plane")

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
        self.surface_dialogue_displayed = False


    def curve_highlighted(self, selectedItems):
        if len(selectedItems) == 0:
            return
        
        for item in selectedItems:
            for curve in self.featureTree.curves:
                if curve.name == item.text():
                    curve.color = 'orange'

                else:
                    curve.color = 'blue'


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

        print(selectedSketchPlane.name)

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
        closedUBSplineButton = wdg.QPushButton("Closed Uniform B-Spline")

        layout.addWidget(straightLineButton, 0, 0)
        layout.addWidget(splineButton, 0, 1)
        layout.addWidget(bezierButton, 0, 2)
        layout.addWidget(closedUBSplineButton, 1, 0)

        # button callbacks
        straightLineButton.clicked.connect(lambda: self.draw_straight_line(selectedSketchPlane))
        splineButton.clicked.connect(lambda: self.draw_spline(selectedSketchPlane))
        bezierButton.clicked.connect(lambda: self.draw_bezier(selectedSketchPlane))
        closedUBSplineButton.clicked.connect(lambda: self.draw_CUBSpline(selectedSketchPlane))

        # end
        self.optionLayout.addWidget(self.sketchContainer)

        # state flags
        self.sketch_displayed = True
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False
        self.intersection_dialogue_displayed = False


    def draw_CUBSpline(self, selectedSketchPlane : SketchPlane):
        self.clear_option_layout
        self.sketchContainer.deleteLater()

        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        controlPointsLabel = wdg.QLabel("# Control Points: ")
        controlPointsDropdown = wdg.QComboBox()
        controlPointsDropdown.addItems(['3', '4', '5', '6', '7', '8', '9'])
        acceptControlPointsButton = wdg.QPushButton("Accept")

        layout.addWidget(controlPointsLabel, 0, 0)
        layout.addWidget(controlPointsDropdown, 0, 1)
        layout.addWidget(acceptControlPointsButton, 0, 2)

        acceptControlPointsButton.clicked.connect(lambda: self.draw_CUBSpline_control_points(selectedSketchPlane, controlPointsDropdown))
        
        self.optionLayout.addWidget(self.sketchContainer)

    
    def draw_CUBSpline_control_points(self, selectedSketchPlane : SketchPlane, controlPointsDropdown : wdg.QComboBox):
        self.clear_option_layout()
        self.sketchContainer.deleteLater()

        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        numberOfControlPoints = int(controlPointsDropdown.currentText())

        labels = []
        xFields = []
        yFields = []
        zFields = []
        for i in range(numberOfControlPoints):
            match selectedSketchPlane.initial_orientation:
                case 'xy':
                    xlabel = wdg.QLabel(f"P{i}x: ")
                    ylabel = wdg.QLabel(f"P{i}y: ")

                    xField = wdg.QLineEdit()
                    yField = wdg.QLineEdit()

                    labels.append(xlabel)
                    labels.append(ylabel)

                    xFields.append(xField)
                    yFields.append(yField)

                    layout.addWidget(xlabel, i, 0)
                    layout.addWidget(xField, i, 1)
                    layout.addWidget(ylabel, i, 2)
                    layout.addWidget(yField, i, 3)

                case 'yz':
                    ylabel = wdg.QLabel(f"P{i}y: ")
                    zlabel = wdg.QLabel(f"P{i}z: ")

                    yField = wdg.QLineEdit()
                    zField = wdg.QLineEdit()

                    labels.append(ylabel)
                    labels.append(zlabel)

                    yFields.append(yField)
                    zFields.append(zField)

                    layout.addWidget(ylabel, i, 0)
                    layout.addWidget(yField, i, 1)
                    layout.addWidget(zlabel, i, 2)
                    layout.addWidget(zField, i, 3)
                case 'xz':
                    xlabel = wdg.QLabel(f"P{i}x: ")
                    zlabel = wdg.QLabel(f"P{i}z: ")

                    xField = wdg.QLineEdit()
                    zField = wdg.QLineEdit()

                    labels.append(xlabel)
                    labels.append(zlabel)

                    xFields.append(xField)
                    zFields.append(zField)

                    layout.addWidget(xlabel, i, 0)
                    layout.addWidget(xField, i, 1)
                    layout.addWidget(zlabel, i, 2)
                    layout.addWidget(zField, i, 3)

        cancelButton = wdg.QPushButton("Cancel")
        previewButton = wdg.QPushButton("Preview")
        acceptButton = wdg.QPushButton("Accept")

        layout.addWidget(cancelButton, numberOfControlPoints, 0)
        layout.addWidget(previewButton, numberOfControlPoints, 2)
        layout.addWidget(acceptButton, numberOfControlPoints, 4)
        
        # control points
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        sp.pretty_print(controlPoints)

        # callbacks
        cancelButton.clicked.connect(lambda: self.escape_container(self.sketchContainer))
        previewButton.clicked.connect(lambda: self.preview_CUBSpline(selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields))
        acceptButton.clicked.connect(lambda: self.accept_CUBSpline(selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields))


        self.optionLayout.addWidget(self.sketchContainer)

    
    def preview_CUBSpline(self, selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields):
        # field values
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        for idx, field in enumerate(xFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 0] = float(field.text())

        for idx, field in enumerate(yFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 1] = float(field.text())

        for idx, field in enumerate(zFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 2] = float(field.text())

        sp.pretty_print(controlPoints)

        self.setup_2d_plot(selectedSketchPlane.initial_orientation)

        CUBSpline = ClosedUniformBSpline(f"curve{self.featureTree.curveCount}", 3, controlPoints, 40, selectedSketchPlane)

        line_traces = CUBSpline.generate_traces()

        match selectedSketchPlane.initial_orientation:
            case 'xy':
                for line_trace in line_traces:
                    self.sc.axes.plot(line_trace[:, 0], line_trace[:, 1], color=CUBSpline.color)
            case 'yz':
                for line_trace in line_traces:
                    self.sc.axes.plot(line_trace[:, 1], line_trace[:, 2], color=CUBSpline.color)
            case 'xz':
                for line_trace in line_traces:
                    self.sc.axes.plot(line_trace[:, 0], line_trace[:, 2], color=CUBSpline.color)

        return
    

    def accept_CUBSpline(self, selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields):
        # field values
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        for idx, field in enumerate(xFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 0] = float(field.text())

        for idx, field in enumerate(yFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 1] = float(field.text())

        for idx, field in enumerate(zFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 2] = float(field.text())

        sp.pretty_print(controlPoints)

        CUBSpline = ClosedUniformBSpline(f"curve{self.featureTree.curveCount}", 3, controlPoints, 40, selectedSketchPlane)

        line_traces = CUBSpline.generate_traces()
        # match selectedSketchPlane.initial_orientation:
        #     case 'xy':
        #         for line_trace in line_traces:
        #             self.sc.axes.plot(line_trace[:, 0], line_trace[:, 1], color=CUBSpline.color)
        #     case 'yz':
        #         for line_trace in line_traces:
        #             self.sc.axes.plot(line_trace[:, 1], line_trace[:, 2], color=CUBSpline.color)
        #     case 'xz':
        #         for line_trace in line_traces:
        #             self.sc.axes.plot(line_trace[:, 0], line_trace[:, 2], color=CUBSpline.color)

        for curve in CUBSpline.curves:
            self.featureTree.add_curve(curve)

        self.clear_mpl_container()

        self.escape_container(self.sketchContainer)


    def draw_bezier(self, selectedSketchPlane : SketchPlane):
        self.clear_option_layout
        self.sketchContainer.deleteLater()

        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        controlPointsLabel = wdg.QLabel("# Control Points: ")
        controlPointsDropdown = wdg.QComboBox()
        controlPointsDropdown.addItems(['3', '4', '5'])
        acceptControlPointsButton = wdg.QPushButton("Accept")

        layout.addWidget(controlPointsLabel, 0, 0)
        layout.addWidget(controlPointsDropdown, 0, 1)
        layout.addWidget(acceptControlPointsButton, 0, 2)

        acceptControlPointsButton.clicked.connect(lambda: self.draw_bezier_control_points(selectedSketchPlane, controlPointsDropdown))
        
        self.optionLayout.addWidget(self.sketchContainer)


    def draw_bezier_control_points(self, selectedSketchPlane : SketchPlane, controlPointsDropdown : wdg.QComboBox):
        self.clear_option_layout()
        self.sketchContainer.deleteLater()

        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        numberOfControlPoints = int(controlPointsDropdown.currentText())

        labels = []
        xFields = []
        yFields = []
        zFields = []
        for i in range(numberOfControlPoints):
            match selectedSketchPlane.initial_orientation:
                case 'xy':
                    xlabel = wdg.QLabel(f"P{i}x: ")
                    ylabel = wdg.QLabel(f"P{i}y: ")

                    xField = wdg.QLineEdit()
                    yField = wdg.QLineEdit()

                    labels.append(xlabel)
                    labels.append(ylabel)

                    xFields.append(xField)
                    yFields.append(yField)

                    layout.addWidget(xlabel, i, 0)
                    layout.addWidget(xField, i, 1)
                    layout.addWidget(ylabel, i, 2)
                    layout.addWidget(yField, i, 3)

                case 'yz':
                    ylabel = wdg.QLabel(f"P{i}y: ")
                    zlabel = wdg.QLabel(f"P{i}z: ")

                    yField = wdg.QLineEdit()
                    zField = wdg.QLineEdit()

                    labels.append(ylabel)
                    labels.append(zlabel)

                    yFields.append(yField)
                    zFields.append(zField)

                    layout.addWidget(ylabel, i, 0)
                    layout.addWidget(yField, i, 1)
                    layout.addWidget(zlabel, i, 2)
                    layout.addWidget(zField, i, 3)
                case 'xz':
                    xlabel = wdg.QLabel(f"P{i}x: ")
                    zlabel = wdg.QLabel(f"P{i}z: ")

                    xField = wdg.QLineEdit()
                    zField = wdg.QLineEdit()

                    labels.append(xlabel)
                    labels.append(zlabel)

                    xFields.append(xField)
                    zFields.append(zField)

                    layout.addWidget(xlabel, i, 0)
                    layout.addWidget(xField, i, 1)
                    layout.addWidget(zlabel, i, 2)
                    layout.addWidget(zField, i, 3)

        cancelButton = wdg.QPushButton("Cancel")
        previewButton = wdg.QPushButton("Preview")
        acceptButton = wdg.QPushButton("Accept")

        layout.addWidget(cancelButton, numberOfControlPoints, 0)
        layout.addWidget(previewButton, numberOfControlPoints, 2)
        layout.addWidget(acceptButton, numberOfControlPoints, 4)
        
        # control points
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        sp.pretty_print(controlPoints)

        # callbacks
        cancelButton.clicked.connect(lambda: self.escape_container(self.sketchContainer))
        previewButton.clicked.connect(lambda: self.preview_bezier(selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields))
        acceptButton.clicked.connect(lambda: self.accept_bezier(selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields))


        self.optionLayout.addWidget(self.sketchContainer)

    
    def preview_bezier(self, selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields):
        # field values
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        for idx, field in enumerate(xFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 0] = float(field.text())

        for idx, field in enumerate(yFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 1] = float(field.text())

        for idx, field in enumerate(zFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 2] = float(field.text())

        sp.pretty_print(controlPoints)

        self.setup_2d_plot(selectedSketchPlane.initial_orientation)

        bezierCurve = BezierCurve(f"curve{self.featureTree.curveCount}", controlPoints, 40, selectedSketchPlane)

        line_trace = bezierCurve.generate_trace()

        match selectedSketchPlane.initial_orientation:
            case 'xy':
                self.sc.axes.plot(line_trace[:, 0], line_trace[:, 1])
            case 'yz':
                self.sc.axes.plot(line_trace[:, 1], line_trace[:, 2])
            case 'xz':
                self.sc.axes.plot(line_trace[:, 0], line_trace[:, 2])

        return
    

    def accept_bezier(self, selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields):
        # field values
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        for idx, field in enumerate(xFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 0] = float(field.text())

        for idx, field in enumerate(yFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 1] = float(field.text())

        for idx, field in enumerate(zFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 2] = float(field.text())

        sp.pretty_print(controlPoints)

        bezierCurve = BezierCurve(f"curve{self.featureTree.curveCount}", controlPoints, 40, selectedSketchPlane)

        # line_trace = bezierCurve.generate_trace()
        # match selectedSketchPlane.initial_orientation:
        #     case 'xy':
        #         self.sc.axes.plot(line_trace[:, 0], line_trace[:, 1])
        #     case 'yz':
        #         self.sc.axes.plot(line_trace[:, 1], line_trace[:, 2])
        #     case 'xz':
        #         self.sc.axes.plot(line_trace[:, 0], line_trace[:, 2])

        # bezierCurve.translate(selectedSketchPlane.offset)

        # bezierCurve.rotate(selectedSketchPlane.alpha, selectedSketchPlane.beta, selectedSketchPlane.gamma)

        self.featureTree.add_curve(bezierCurve)

        self.clear_mpl_container()

        self.escape_container(self.sketchContainer)


    def draw_spline(self, selectedSketchPlane : SketchPlane):
        self.clear_option_layout
        self.sketchContainer.deleteLater()

        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        controlPointsLabel = wdg.QLabel("# Control Points: ")
        controlPointsDropdown = wdg.QComboBox()
        controlPointsDropdown.addItems(['3', '4', '5'])
        acceptControlPointsButton = wdg.QPushButton("Accept")

        layout.addWidget(controlPointsLabel, 0, 0)
        layout.addWidget(controlPointsDropdown, 0, 1)
        layout.addWidget(acceptControlPointsButton, 0, 2)

        acceptControlPointsButton.clicked.connect(lambda: self.draw_spline_control_points(selectedSketchPlane, controlPointsDropdown))
        
        self.optionLayout.addWidget(self.sketchContainer)


    def draw_spline_control_points(self, selectedSketchPlane : SketchPlane, controlPointsDropdown : wdg.QComboBox):
        self.clear_option_layout()
        self.sketchContainer.deleteLater()

        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        numberOfControlPoints = int(controlPointsDropdown.currentText())

        labels = []
        xFields = []
        yFields = []
        zFields = []
        for i in range(numberOfControlPoints):
            match selectedSketchPlane.initial_orientation:
                case 'xy':
                    xlabel = wdg.QLabel(f"P{i}x: ")
                    ylabel = wdg.QLabel(f"P{i}y: ")

                    xField = wdg.QLineEdit()
                    yField = wdg.QLineEdit()

                    labels.append(xlabel)
                    labels.append(ylabel)

                    xFields.append(xField)
                    yFields.append(yField)

                    layout.addWidget(xlabel, i, 0)
                    layout.addWidget(xField, i, 1)
                    layout.addWidget(ylabel, i, 2)
                    layout.addWidget(yField, i, 3)

                case 'yz':
                    ylabel = wdg.QLabel(f"P{i}y: ")
                    zlabel = wdg.QLabel(f"P{i}z: ")

                    yField = wdg.QLineEdit()
                    zField = wdg.QLineEdit()

                    labels.append(ylabel)
                    labels.append(zlabel)

                    yFields.append(yField)
                    zFields.append(zField)

                    layout.addWidget(ylabel, i, 0)
                    layout.addWidget(yField, i, 1)
                    layout.addWidget(zlabel, i, 2)
                    layout.addWidget(zField, i, 3)
                case 'xz':
                    xlabel = wdg.QLabel(f"P{i}x: ")
                    zlabel = wdg.QLabel(f"P{i}z: ")

                    xField = wdg.QLineEdit()
                    zField = wdg.QLineEdit()

                    labels.append(xlabel)
                    labels.append(zlabel)

                    xFields.append(xField)
                    zFields.append(zField)

                    layout.addWidget(xlabel, i, 0)
                    layout.addWidget(xField, i, 1)
                    layout.addWidget(zlabel, i, 2)
                    layout.addWidget(zField, i, 3)

        cancelButton = wdg.QPushButton("Cancel")
        previewButton = wdg.QPushButton("Preview")
        acceptButton = wdg.QPushButton("Accept")

        layout.addWidget(cancelButton, numberOfControlPoints, 0)
        layout.addWidget(previewButton, numberOfControlPoints, 2)
        layout.addWidget(acceptButton, numberOfControlPoints, 4)
        
        # control points
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        sp.pretty_print(controlPoints)

        # callbacks
        cancelButton.clicked.connect(lambda: self.escape_container(self.sketchContainer))
        previewButton.clicked.connect(lambda: self.preview_spline(selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields))
        acceptButton.clicked.connect(lambda: self.accept_spline(selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields))


        self.optionLayout.addWidget(self.sketchContainer)


    def preview_spline(self, selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields):
        # field values
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        for idx, field in enumerate(xFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 0] = float(field.text())

        for idx, field in enumerate(yFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 1] = float(field.text())

        for idx, field in enumerate(zFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 2] = float(field.text())

        sp.pretty_print(controlPoints)

        self.setup_2d_plot(selectedSketchPlane.initial_orientation)

        spline = Spline(f"curve{self.featureTree.curveCount}", controlPoints, 40, selectedSketchPlane)

        line_trace = spline.generate_trace()
        match selectedSketchPlane.initial_orientation:
            case 'xy':
                self.sc.axes.plot(line_trace[:, 0], line_trace[:, 1])
            case 'yz':
                self.sc.axes.plot(line_trace[:, 1], line_trace[:, 2])
            case 'xz':
                self.sc.axes.plot(line_trace[:, 0], line_trace[:, 2])

        return
    

    def accept_spline(self, selectedSketchPlane, numberOfControlPoints, xFields, yFields, zFields):
        # field values
        controlPoints = sp.zeros(numberOfControlPoints, 3)

        for idx, field in enumerate(xFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 0] = float(field.text())

        for idx, field in enumerate(yFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 1] = float(field.text())

        for idx, field in enumerate(zFields):
            if field is not None and field.text() != '':
                controlPoints[idx, 2] = float(field.text())

        sp.pretty_print(controlPoints)

        spline = Spline(f"curve{self.featureTree.curveCount}", controlPoints, 40, selectedSketchPlane)

        # line_trace = spline.generate_trace()
        # match selectedSketchPlane.initial_orientation:
        #     case 'xy':
        #         self.sc.axes.plot(line_trace[:, 0], line_trace[:, 1])
        #     case 'yz':
        #         self.sc.axes.plot(line_trace[:, 1], line_trace[:, 2])
        #     case 'xz':
        #         self.sc.axes.plot(line_trace[:, 0], line_trace[:, 2])

        # spline.translate(selectedSketchPlane.offset)

        # spline.rotate(selectedSketchPlane.alpha, selectedSketchPlane.beta, selectedSketchPlane.gamma)

        self.featureTree.add_curve(spline)

        self.clear_mpl_container()

        self.escape_container(self.sketchContainer)


    def draw_straight_line(self, selectedSketchPlane : SketchPlane):
        print(f"draw straight line, selected sketch plane: {selectedSketchPlane.offset.x}, {selectedSketchPlane.offset.y}, {selectedSketchPlane.offset.z}")
        self.clear_option_layout()
        self.sketchContainer.deleteLater()

        self.slp0xField = None
        self.slp0yField = None
        self.slp0zField = None
        self.slp1xField = None
        self.slp1yField = None
        self.slp1zField = None

        self.sketchContainer = wdg.QWidget()
        layout = wdg.QGridLayout(self.sketchContainer)

        p0Label = wdg.QLabel("p0: ")
        p1Label = wdg.QLabel("p1: ")

        layout.addWidget(p0Label, 0, 0)
        layout.addWidget(p1Label, 1, 0)

        match selectedSketchPlane.initial_orientation:
            case 'xy':
                p0xLabel = wdg.QLabel("X: ")
                p0yLabel = wdg.QLabel("Y: ")
                self.slp0xField = wdg.QLineEdit()
                self.slp0yField = wdg.QLineEdit()

                layout.addWidget(p0xLabel, 0, 1)
                layout.addWidget(self.slp0xField, 0, 2)
                layout.addWidget(p0yLabel, 0, 3)
                layout.addWidget(self.slp0yField, 0, 4)

                p1xLabel = wdg.QLabel("X: ")
                p1yLabel = wdg.QLabel("Y: ")
                self.slp1xField = wdg.QLineEdit()
                self.slp1yField = wdg.QLineEdit()

                layout.addWidget(p1xLabel, 1, 1)
                layout.addWidget(self.slp1xField, 1, 2)
                layout.addWidget(p1yLabel, 1, 3)
                layout.addWidget(self.slp1yField, 1, 4)

            case 'yz':
                p0yLabel = wdg.QLabel("Y: ")
                p0zLabel = wdg.QLabel("Z: ")
                self.slp0yField = wdg.QLineEdit()
                self.slp0zField = wdg.QLineEdit()

                layout.addWidget(p0yLabel, 0, 1)
                layout.addWidget(self.slp0yField, 0, 2)
                layout.addWidget(p0zLabel, 0, 3)
                layout.addWidget(self.slp0zField, 0, 4)

                p1yLabel = wdg.QLabel("Y: ")
                p1zLabel = wdg.QLabel("Z: ")
                self.slp1yField = wdg.QLineEdit()
                self.slp1zField = wdg.QLineEdit()

                layout.addWidget(p1yLabel, 1, 1)
                layout.addWidget(self.slp1yField, 1, 2)
                layout.addWidget(p1zLabel, 1, 3)
                layout.addWidget(self.slp1zField, 1, 4)

            case 'xz':
                p0xLabel = wdg.QLabel("X: ")
                p0zLabel = wdg.QLabel("Z: ")
                self.slp0xField = wdg.QLineEdit()
                self.slp0zField = wdg.QLineEdit()

                layout.addWidget(p0xLabel, 0, 1)
                layout.addWidget(self.slp0xField, 0, 2)
                layout.addWidget(p0zLabel, 0, 3)
                layout.addWidget(self.slp0zField, 0, 4)

                p1xLabel = wdg.QLabel("X: ")
                p1zLabel = wdg.QLabel("Z: ")
                self.slp1xField = wdg.QLineEdit()
                self.slp1zField = wdg.QLineEdit()

                layout.addWidget(p1xLabel, 1, 1)
                layout.addWidget(self.slp1xField, 1, 2)
                layout.addWidget(p1zLabel, 1, 3)
                layout.addWidget(self.slp1zField, 1, 4)

        cancelButton = wdg.QPushButton("Cancel")
        previewButton = wdg.QPushButton("Preview")
        acceptButton = wdg.QPushButton("Accept")

        layout.addWidget(cancelButton, 3, 0)
        layout.addWidget(previewButton, 3, 2)
        layout.addWidget(acceptButton, 3, 4)
        
        # callbacks
        cancelButton.clicked.connect(lambda: self.escape_container(self.sketchContainer))
        previewButton.clicked.connect(lambda: self.preview_straight_line(selectedSketchPlane))
        acceptButton.clicked.connect(lambda: self.accept_straight_line(selectedSketchPlane))

        self.optionLayout.addWidget(self.sketchContainer)


    def accept_straight_line(self, selectedSketchPlane:SketchPlane):
        print(f"{selectedSketchPlane.offset.x}, {selectedSketchPlane.offset.y}, {selectedSketchPlane.offset.z}")

        # field values
        p0 = sp.Matrix([[0, 0, 0]])
        p1 = sp.Matrix([[0, 0, 0]])

        if self.slp0xField is not None and self.slp0xField.text() != '':
            p0[0, 0] = float(self.slp0xField.text())
        
        if self.slp0yField is not None and self.slp0yField.text() != '': 
            p0[0, 1]= float(self.slp0yField.text())

        if self.slp0zField is not None and self.slp0zField.text() != '':
            p0[0, 2]= float(self.slp0zField.text())

        if self.slp1xField is not None and self.slp1xField.text() != '':
            p1[0, 0] = float(self.slp1xField.text())

        if self.slp1yField is not None and self.slp1yField.text() != '':
            p1[0, 1] = float(self.slp1yField.text())

        if self.slp1zField is not None and self.slp1zField.text() != '': 
            p1[0, 2] = float(self.slp1zField.text())

        line = StraightLine(f"curve{self.featureTree.curveCount}", p0, p1, 40, selectedSketchPlane)

        # line.translate(selectedSketchPlane.offset)

        # line.rotate(selectedSketchPlane.alpha, selectedSketchPlane.beta, selectedSketchPlane.gamma)

        print(f"in accept straight line: {line.offset.x}, {line.offset.y}, {line.offset.z}")

        self.featureTree.add_curve(line)

        self.clear_mpl_container()

        self.escape_container(self.sketchContainer)


    def preview_straight_line(self, selectedSketchPlane:SketchPlane):
        print(f"in preview straight line")

        print(f"{selectedSketchPlane.offset.x}, {selectedSketchPlane.offset.y}, {selectedSketchPlane.offset.z}")
        # field values
        p0 = sp.Matrix([[0, 0, 0]])
        p1 = sp.Matrix([[0, 0, 0]])

        if self.slp0xField is not None and self.slp0xField.text() != '':
            p0[0, 0] = float(self.slp0xField.text())
        
        if self.slp0yField is not None and self.slp0yField.text() != '': 
            p0[0, 1]= float(self.slp0yField.text())

        if self.slp0zField is not None and self.slp0zField.text() != '':
            p0[0, 2]= float(self.slp0zField.text())

        if self.slp1xField is not None and self.slp1xField.text() != '':
            p1[0, 0] = float(self.slp1xField.text())

        if self.slp1yField is not None and self.slp1yField.text() != '':
            p1[0, 1] = float(self.slp1yField.text())

        if self.slp1zField is not None and self.slp1zField.text() != '': 
            p1[0, 2] = float(self.slp1zField.text())

        self.setup_2d_plot(selectedSketchPlane.initial_orientation)

        line = StraightLine(f"curve{self.featureTree.curveCount}", p0, p1, 40, selectedSketchPlane)

        print(f"in preview straight line: {line.offset.x}, {line.offset.y}, {line.offset.z}")

        line_trace = line.generate_trace()
        match selectedSketchPlane.initial_orientation:
            case 'xy':
                self.sc.axes.plot(line_trace[:, 0], line_trace[:, 1])
            case 'yz':
                self.sc.axes.plot(line_trace[:, 1], line_trace[:, 2])
            case 'xz':
                self.sc.axes.plot(line_trace[:, 0], line_trace[:, 2])

        return


    def deleteSketchPlane(self, sketchPlaneList, items):
        names = [item.text() for item in items]

        updatedSketchPlanes = [sketchPlane for sketchPlane in self.featureTree.sketchPlanes if sketchPlane.name not in names]
        
        self.featureTree.sketchPlanes = updatedSketchPlanes

        for item in items:
            sketchPlaneList.takeItem(sketchPlaneList.row(item))

        self.draw_features()

        # ui flags
        self.sketch_displayed = True
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False
        self.intersection_dialogue_displayed = False


    def sketch_plane_dialogue(self):
        if self.sketch_plane_dialogue_displayed == True: 
            return
        
        self.color_all_sketchplanes_blue()

        self.color_all_sketchplanes_blue()

        self.color_all_surfaces_green()
        
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
        sketchPlaneEscapeButton.clicked.connect(lambda: self.escape_container(self.sketchPlaneContainer))
        sketchPlanePlotButton.clicked.connect(self.preview_sketch_plane)
        sketchPlaneAcceptButton.clicked.connect(self.accept_sketch_plane)
        
        self.clear_option_layout()

        self.optionLayout.addWidget(self.sketchPlaneContainer)

        self.sketch_plane_dialogue_displayed = True
        self.sketch_dialogue_displayed = False
        self.sketch_displayed = False
        self.surface_dialogue_displayed = False


    def escape_container(self, container):
        container.deleteLater()
        self.sketch_plane_dialogue_displayed = False
        self.sketch_dialogue_displayed = False
        self.sketch_displayed = False
        self.surface_dialogue_displayed = False
        self.intersection_dialogue_displayed = False

        # wipe canvas
        self.color_all_sketchplanes_blue()

        self.color_all_sketchplanes_blue()

        self.color_all_curves_blue()

        self.color_all_surfaces_green()

        self.clear_mpl_container()

        self.setup_3d_plot()


    def accept_sketch_plane(self):
        if self.tempSketchPlane is None:
            return
        
        self.sketchPlaneContainer.deleteLater()
        self.sketch_plane_dialogue_displayed = False

        # TODO: WIPE CANVAS AND REDRAW ACTUAL FEATURES ONLY
        self.sc.axes.cla()
        self.set_labels_3d()
        self.set_limits_3d()

        self.featureTree.add_sketch_plane(self.tempSketchPlane)
        self.tempSketchPlane = None

        self.draw_features()


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
        
        sketchPlane = SketchPlane(f"Plane{self.featureTree.sketchPlanesCount}", initial_orientation, 10, p0, p1, q0, q1, color=color)

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
        
        sketchPlane = SketchPlane(f"Plane{self.featureTree.sketchPlanesCount}", initial_orientation, 10, p0, p1, q0, q1, color=color)

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
    

    def draw_features(self):
        print('draw features')
        self.sc.axes.cla()

        print(self.featureTree.sketchPlanes)

        for sketchPlane in self.featureTree.sketchPlanes:
            sketchPlaneTraces = sketchPlane.generate_traces()

            sp.pretty_print(sketchPlane.S_u_w)

            sketchPlane.offset.print()

            for trace in sketchPlaneTraces:
                self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=sketchPlane.color, alpha=0.3)

        for curve in self.featureTree.curves:
            print(curve.P_u)
            curveTrace = curve.generate_trace()

            self.sc.axes.plot(curveTrace[:, 0], curveTrace[:, 1], curveTrace[:, 2], color=curve.color)

        for surface in self.featureTree.surfaces:
            surfaceTraces = surface.generate_traces()

            for trace in surfaceTraces:
                self.sc.axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=surface.color)


        self.set_labels_3d()
        self.set_limits_3d()
        self.sc.figure.canvas.draw()

    
    def color_all_sketchplanes_blue(self):
        for sketchPlane in self.featureTree.sketchPlanes:
            sketchPlane.color = 'blue'


    def color_all_curves_blue(self):
        for curve in self.featureTree.curves:
            curve.color = 'blue'

    def color_all_surfaces_green(self):
        for surface in self.featureTree.surfaces:
            surface.color = 'green'


if __name__ == "__main__":
    app = wdg.QApplication(sys.argv)
    app.setStyle('windowsvista')
    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec())