import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

from sketchPlane import SketchPlane

from straightLine import StraightLine
from spline import Spline
from bezierCurve import BezierCurve

from CADUtils import Offset

class RuledSurface:
    def __init__(self, name, curve1, curve2, density=40, color='green'):
        self.u = sp.symbols('u')

        self.w = sp.symbols('w')

        self.u_eval = np.linspace(0, 1, density)

        self.w_eval = np.linspace(0, 1, density)

        print(self.w_eval)

        self.name = name

        self.curve1 = curve1

        self.curve2 = curve2

        self.W = sp.Matrix([[self.w, 1]])

        self.color = color

        self.S_u_w = (1 - self.w) * self.curve1.P_u + self.w * self.curve2.P_u

    
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

    plane2 = SketchPlane('plane2', 'xz', 10, p0, p1, q0, q1)

    cps = sp.Matrix([[-20, 0, -30], [0, 0, 30], [20, 0, 0], [50, 0, 30], [60, 0, -20]])

    curve1 = BezierCurve("bezier", cps, 40, plane1)

    cps = sp.Matrix([[-10, 0, -50], [0, 0, 50], [30, 0, 0], [80, 0, 64], [-30, 0, -80]])

    plane2.translate(Offset(0, 5, 0))

    curve2 = BezierCurve("bezier", cps, 40, plane2)

    p1traces = plane1.generate_traces()
    p2traces = plane2.generate_traces()

    curve1_trace = curve1.generate_trace()

    curve2_trace = curve2.generate_trace()

    figure = plt.figure()

    axes = figure.add_subplot(projection='3d')

    axes.plot(curve1_trace[:, 0], curve1_trace[:, 1], curve1_trace[:, 2])

    axes.plot(curve2_trace[:, 0], curve2_trace[:, 1], curve2_trace[:, 2])

    for trace in p1traces:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=plane1.color)

    for trace in p2traces:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=plane2.color)

    myRSurface = RuledSurface('surf1', curve1, curve2, 40)

    surf_traces = myRSurface.generate_traces()

    for trace in surf_traces:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=myRSurface.color)

    plt.show()