import matplotlib.pyplot as plt
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


class IntersectionCurve():
    def __init__(self, name, surface1, surface2, density, tolerance, sketchPlane: SketchPlane):
        self.name = name

        self.u = sp.symbols('u')

        self.w = sp.symbols('w')

        self.u_eval = np.linspace(0, 1, density)

        self.w_eval = np.linspace(0, 1, density)

        self.surface1 = surface1
        self.surface2 = surface2

        self.density = density
        self.tolerance = tolerance

        self.intersection_points = self.get_intersection_points(tolerance)

        if self.intersection_points.shape[0] < 4:
            return None

        G_intersection = sp.Matrix([self.intersection_points[0], self.intersection_points[self.intersection_points.shape[0] // 3], self.intersection_points[(self.intersection_points.shape[0]-1) * 2 // 3], self.intersection_points[self.intersection_points.shape[0]-1]])

        sp.pretty_print(G_intersection)

        self.curve_itself = Spline(self.name, G_intersection, 40, sketchPlane)


    def get_intersection_points(self, tolerance):
        # precompute all surface1 points
        surface1_points = []
        for u in self.u_eval:
            for w in self.w_eval:
                p = self.surface1.S_u_w.subs({self.u: u, self.w: w}).evalf()
                surface1_points.append([float(p[idx]) for idx in range(3)])
        surface1_points = np.array(surface1_points)  # shape: (n1, 3)

        # precompute all surface2 points
        surface2_points = []
        for u in self.u_eval:
            for w in self.w_eval:
                p = self.surface2.S_u_w.subs({self.u: u, self.w: w}).evalf()
                surface2_points.append([float(p[idx]) for idx in range(3)])
        surface2_points = np.array(surface2_points)  # shape: (n2, 3)

        # find intersections
        intersection_points = []

        for i, p1 in enumerate(surface1_points):
            diffs = np.abs(surface2_points - p1)  # vectorized subtraction
            close = np.all(diffs < tolerance, axis=1)
            matches = surface2_points[close]
            for match in matches:
                intersection_points.append(match.tolist())

        return np.array(intersection_points)
    

if __name__ == "__main__":
    figure = plt.figure()

    axes = figure.add_subplot(projection='3d')

    p0 = sp.Matrix([[-100, -100, 0]])
    p1 = sp.Matrix([[-100, 100, 0]])

    q0 = sp.Matrix([[100, -100, 0]])
    q1 = sp.Matrix([[100, 100, 0]])

    plane1 = SketchPlane('plane', 'xy', 40, p0, p1, q0, q1)

    curve1 = BezierCurve("bezier1", sp.Matrix([[-10, -35, 0], [0, 0, 10], [2, 62, 10], [3, 52, 10]]), 100, plane1)

    surface1 = CylindricalSurface('surface 1', curve1, 10)

    surface1.scale_q(100)

    p0 = sp.Matrix([[-100, 0, -100]])
    p1 = sp.Matrix([[-100, 0, 100]])

    q0 = sp.Matrix([[100, 0, -100]])
    q1 = sp.Matrix([[100, 0, 100]])

    plane2 = SketchPlane('plane', 'xz', 40, p0, p1, q0, q1)

    curve2 = BezierCurve("bezier", sp.Matrix([[0, 0, -10], [-1, 0, 30], [-2, 0, 50], [-3, 0, 20]]), 100, plane2)

    surface2 = CylindricalSurface('surface 2', curve2, 10)

    surface2.scale_q(100)

    surf1t = surface1.generate_traces()

    surf2t = surface2.generate_traces()

    for trace in surf1t:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=surface1.color)

    for trace in surf2t:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=surface2.color)

    myIntersection = IntersectionCurve("intersection curve", surface1, surface2, 100, 0.25, plane1)

    # axes.plot(myIntersection.intersection_points[:, 0], myIntersection.intersection_points[:, 1], myIntersection.intersection_points[:, 2])

    myIntersectionCurveTrace = myIntersection.curve_itself.generate_trace()

    axes.plot(myIntersectionCurveTrace[:, 0], myIntersectionCurveTrace[:, 1], myIntersectionCurveTrace[:, 2])

    plt.show()


