import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

from sketchPlane import SketchPlane

from straightLine import StraightLine
from spline import Spline
from bezierCurve import BezierCurve

from CADUtils import Offset

class RevolvedSurface:
    def __init__(self, name, curve, axis, rotation_degrees, axes, density=40, color='green'):
        self.u = sp.symbols('u')

        self.w = sp.symbols('w')

        self.u_eval = np.linspace(0, 1, density)

        self.w_eval = np.linspace(0, rotation_degrees/60, density)

        print(self.w_eval)

        self.name = name

        self.curve = curve

        self.color = color

        self.offset = self.curve.offset

        self.normal_vector = curve.normal_vector

        self.u = sp.symbols('u')

        self.w = sp.symbols('w')

        self.P_u = self.curve.P_u - sp.Matrix([[self.offset.x, self.offset.y, self.offset.z]])

        self.axis = axis

        old_axis_offset = Offset(self.axis.offset.x, self.axis.offset.y, self.axis.offset.z)

        old_axis_offset.print()

        old_P_u_offset = Offset(self.curve.offset.x, self.curve.offset.y, self.curve.offset.z)

        old_P_u_offset.print()

        sp.pretty_print(self.axis.Gsl)

        p_u_debug_trace1 = self.curve.generate_trace()

        axes.plot(p_u_debug_trace1[:, 0], p_u_debug_trace1[:, 1], p_u_debug_trace1[:, 2], label='p_u debug trace 1')

        self.axis.P_u = self.translate(self.axis.P_u, Offset(-1 * self.axis.offset.x, -1 * self.axis.offset.y, -1 * self.axis.offset.z))

        self.axis.P_u = self.translate(self.axis.P_u, Offset(-1 * self.axis.Gsl[0, 0], -1 * self.axis.Gsl[0, 1], -1 * self.axis.Gsl[0, 2]))

        self.curve.P_u = self.translate(self.curve.P_u, Offset(-1 * self.curve.offset.x, -1 * self.curve.offset.y, -1 * self.axis.offset.z))

        self.curve.P_u = self.translate(self.curve.P_u, Offset(-1 * self.curve.Gsl[0, 0], -1 * self.curve.Gsl[0, 1], -1 * self.curve.Gsl[0, 2]))

        sp.pretty_print(self.axis.Gsl)

        axis_debug_trace2 = self.axis.generate_trace()

        p_u_debug_trace2 = self.curve.generate_trace()

        axes.plot(axis_debug_trace2[:, 0], axis_debug_trace2[:, 1], axis_debug_trace2[:, 2], label='axis debug trace 2')

        axes.plot(p_u_debug_trace2[:, 0], p_u_debug_trace2[:, 1], p_u_debug_trace2[:, 2], label='p_u debug trace 2')

        self.S_u_w = self.revolve(self.curve.P_u, self.axis.P_u)

        self.axis.P_u = self.translate(self.axis.P_u, Offset(self.axis.Gsl[0, 0], self.axis.Gsl[0, 1], self.axis.Gsl[0, 2]))
    
        self.axis.P_u = self.translate(self.axis.P_u, old_axis_offset)
    
        sp.pretty_print(self.axis.Gsl)

        self.curve.P_u = self.translate(self.curve.P_u, old_P_u_offset)

        self.curve.P_u = self.translate(self.curve.P_u, Offset(self.curve.Gsl[0, 0], self.curve.Gsl[0, 1], self.curve.Gsl[0, 2]))

        axis_debug_trace3 = self.axis.generate_trace()

        p_u_debug_trace3 = self.curve.generate_trace()

        # axes.plot(axis_debug_trace3[:, 0], axis_debug_trace3[:, 1], axis_debug_trace3[:, 2], label='debug trace 3')

        axes.plot(p_u_debug_trace3[:, 0], p_u_debug_trace3[:, 1], p_u_debug_trace3[:, 2], label='p_u debug trace 3')

        # self.S_u_w = self.translate(self.S_u_w, old_P_u_offset)


    def revolve(self, P_u, axis):
        W_rotation = sp.Matrix([[sp.cos(self.w), sp.sin(self.w), 0],
                                [0, 0, 0],
                                [0, 0, 1]])
        
        S_u_w = P_u * W_rotation

        sp.pretty_print(S_u_w)

        return S_u_w
    

    def translate(self, curve, offset=Offset(0, 0, 0)):
        # translation matrices

        self.Tx = sp.Matrix([[1, 0, 0, offset.x],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
        
        self.Ty = sp.Matrix([[1, 0, 0, 0],
                        [0, 1, 0, offset.y],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
        
        self.Tz = sp.Matrix([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, offset.z],
                        [0, 0, 0, 1]])
        
        curve_h = curve.T.row_insert(curve.T.rows, sp.Matrix([1]))

        curve_h_transformed = self.Tx * self.Ty * self.Tz * curve_h

        curve_transformed = curve_h_transformed[:-1, :].T

        return curve_transformed
    

    def rotate(self, curve, alpha, beta, gamma):
        self.Trx = sp.Matrix([[1, 0, 0, 0],
                        [0, np.cos(np.radians(alpha)), -np.sin(np.radians(alpha)), 0],
                        [0, np.sin(np.radians(alpha)), np.cos(np.radians(alpha)), 0],
                        [0, 0, 0, 1]])
        
        self.Try = sp.Matrix([[np.cos(np.radians(beta)), 0, -np.sin(np.radians(beta)), 0],
                              [0, 1, 0, 0],
                              [np.sin(np.radians(beta)), 0, np.cos(np.radians(beta)), 0],
                              [0, 0, 0, 1]])

        self.Trz = sp.Matrix([[np.cos(np.radians(gamma)), -np.sin(np.radians(gamma)), 0, 0],
                         [np.sin(np.radians(gamma)), np.cos(np.radians(gamma)), 0, 0],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]])
        
        curve_h = curve.P_u.T.row_insert(curve.P_u.T.rows, sp.Matrix([1]))

        curve_h_transformed = self.Trx * self.Try * self.Trz * curve_h

        curve_transformed = curve_h_transformed[:-1, :].T

        return curve_transformed
    

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
    figure = plt.figure()

    axes = figure.add_subplot(projection='3d')

    p0 = sp.Matrix([[-100, 0, -100]])
    p1 = sp.Matrix([[-100, 0, 100]])

    q0 = sp.Matrix([[100, 0, -100]])
    q1 = sp.Matrix([[100, 0, 100]])

    myPlane = SketchPlane('plane', 'xz', 40, p0, p1, q0, q1)

    myPlane.translate(Offset(0, 0, 10))

    myAxis = StraightLine("axis", sp.Matrix([[0, 0, 0]]), sp.Matrix([[0, 0, 10]]), 40, myPlane)

    myLine = StraightLine("line", sp.Matrix([[0, 0, 1]]), sp.Matrix([[1, 0, 0]]), 40, myPlane)

    myRevolvedSurface = RevolvedSurface("surface 1", myLine, myAxis, 180, axes, 40)

    revolvedSurfaceEval = myRevolvedSurface.generate_traces()

    curveFromSurf = myRevolvedSurface.curve.generate_trace()

    for trace in revolvedSurfaceEval:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=myRevolvedSurface.color)

    axes.plot(curveFromSurf[:, 0], curveFromSurf[:, 1], curveFromSurf[:, 2])

    axes.set_xlabel('X')

    axes.set_ylabel('Y')

    axes.set_zlabel('Z')

    plt.legend()

    plt.show()



