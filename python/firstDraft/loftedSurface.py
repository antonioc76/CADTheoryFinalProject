import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

from sketchPlane import SketchPlane

from straightLine import StraightLine
from spline import Spline
from bezierCurve import BezierCurve

from CADUtils import Offset

class LoftedSurface:

    def __init__(self, name, curves, density=40, color='green'):
        self.u = sp.symbols('u')

        self.w = sp.symbols('w')

        self.u_eval = np.linspace(0, 1, density)

        self.w_eval = np.linspace(0, 1, density)

        self.name = name

        self.color = color

        self.curves = [curve.P_u for curve in curves]

        self.curve_count = len(curves)

        print(self.curve_count)

        match self.curve_count:
            case 2:
                self.W = sp.Matrix([[self.w, 1]])
                self.Nspl = sp.Matrix([[0, 1], [1, 1]]) ** -1
            case 3:
                self.W = sp.Matrix([[self.w**2, self.w, 1]])
                self.Nspl = sp.Matrix([[2, -4, 2], [-3, 4, -1], [1, 0, 0]])
            case 4:
                self.W = sp.Matrix([[self.w**3, self.w ** 2, self.w, 1]])
                self.Nspl = sp.Matrix([[-9/2, 27/2, -27/2, 9/2], [9, -45/2, 18, -9/2], [-11/2, 9, -9/2, 1], [1, 0, 0, 0]])
            case 5:
                self.W = sp.Matrix([[self.w**4, self.w**3, self.w**2, self.w, 1]])
                self.Nspl = sp.Matrix([[0, 0, 0, 0, 1], [(1/4)**4, (1/4)**3, (1/4)**2, 1/4, 1], [(2/4)**4, (2/4)**3, (2/4)**2, 2/4, 1], [(3/4)**4, (3/4)**3, (3/4)**2, 3/4, 1], [1, 1, 1, 1, 1]]) ** -1

        Gsur = sp.Matrix([curve for curve in self.curves])

        sp.pretty_print(self.W)

        sp.pretty_print(self.Nspl)

        sp.pretty_print(Gsur)

        for curve in self.curves:
            sp.pretty_print(curve)

        self.S_u_w = self.W * self.Nspl * Gsur


    def generate_traces(self):
        self.S_u_w_lines = []
        self.S_u_w_callable = sp.lambdify([self.u, self.w], self.S_u_w)
        # traces along u lines
        for i in range(len(self.w_eval)):
            S_u_w_line = np.empty((0, 3))
            for j in range(len(self.u_eval)):
                point = self.S_u_w_callable(self.w_eval[i], self.u_eval[j])

                S_u_w_line = np.append(S_u_w_line, point, axis=0)
            self.S_u_w_lines.append(S_u_w_line)

        # traces along w
        for i in range(len(self.u_eval)):
            S_u_w_line = np.empty((0, 3))
            for j in range(len(self.w_eval)):
                point = self.S_u_w_callable(self.w_eval[j], self.u_eval[i])

                S_u_w_line = np.append(S_u_w_line, point, axis=0)
            self.S_u_w_lines.append(S_u_w_line)

        return self.S_u_w_lines
    

if __name__ == "__main__":
    p0 = sp.Matrix([[-100, 0, -100]])
    p1 = sp.Matrix([[-100, 0, 100]])

    q0 = sp.Matrix([[100, 0, -100]])
    q1 = sp.Matrix([[100, 0, 100]])

    plane1 = SketchPlane('plane', 'xz', 10, p0, p1, q0, q1)

    p0 = sp.Matrix([[-100, 0, -100]])
    p1 = sp.Matrix([[-100, 0, 100]])

    q0 = sp.Matrix([[100, 0, -100]])
    q1 = sp.Matrix([[100, 0, 100]])

    curve1 = StraightLine('sl1', sp.Matrix([[0, 0, 3]]), sp.Matrix([[3, 0, 1]]), 40, plane1)

    plane2 = SketchPlane('plane2', 'xz', 10, p0, p1, q0, q1)

    plane2.translate(Offset(0, 5, 0))

    curve2 = Spline("bezier2", sp.Matrix([[0, 0, 0], [1, 0, 3], [3, 0, 2]]), 40, plane2)

    p0 = sp.Matrix([[-100, 0, -100]])
    p1 = sp.Matrix([[-100, 0, 100]])

    q0 = sp.Matrix([[100, 0, -100]])
    q1 = sp.Matrix([[100, 0, 100]])

    plane3 = SketchPlane('plane2', 'xz', 10, p0, p1, q0, q1)

    plane3.translate(Offset(0, 10, 0))

    curve3 = BezierCurve("sl1", sp.Matrix([[0, 0, 1], [2, 0, 2], [2.5, 0, 0.5]]), 40, plane3)

    plane4 = SketchPlane('plane2', 'xz', 10, p0, p1, q0, q1)

    plane4.translate(Offset(0, 15, 0))

    curve4 = StraightLine('spline', sp.Matrix([[0, 0, 3]]),sp.Matrix([[3, 0, 1]]), 40, plane4)

    plane5 = SketchPlane('plane2', 'xz', 10, p0, p1, q0, q1)

    plane5.translate(Offset(0, 20, 0))

    cps = sp.Matrix([[-2, 0, -3], [0, 0, 3], [2, 0, 0], [5, 0, 3], [6, 0, -2]])

    curve5 = BezierCurve("bezier", cps, 40, plane5)

    curve1_eval = curve1.generate_trace()

    curve2_eval = curve2.generate_trace()

    curve3_eval = curve3.generate_trace()

    curve4_eval = curve4.generate_trace()

    curve5_eval = curve5.generate_trace()

    figure = plt.figure()

    axes = figure.add_subplot(projection='3d')

    axes.plot(curve1_eval[:, 0], curve1_eval[:, 1], curve1_eval[:, 2])

    axes.plot(curve2_eval[:, 0], curve2_eval[:, 1], curve2_eval[:, 2])

    axes.plot(curve3_eval[:, 0], curve3_eval[:, 1], curve3_eval[:, 2])

    axes.plot(curve4_eval[:, 0], curve4_eval[:, 1], curve4_eval[:, 2])

    axes.plot(curve5_eval[:, 0], curve5_eval[:, 1], curve5_eval[:, 2])

    curves = [curve1, curve2, curve3, curve4, curve5]

    loftedSurf = LoftedSurface('my surface', curves, 40)

    loftedSurfTraces = loftedSurf.generate_traces()

    for trace in loftedSurfTraces:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=loftedSurf.color)

    plt.show()