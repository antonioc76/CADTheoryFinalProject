import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

from sketchPlane import SketchPlane

from straightLine import StraightLine
from spline import Spline
from bezierCurve import BezierCurve

from CADUtils import Offset

class SweptSurface:
    def __init__(self, name, curve, path_curve, axes, flipped, density=40, color='green'):
        self.u = sp.symbols('u')

        self.w = sp.symbols('w')

        self.u_eval = np.linspace(0, 1, density)

        self.w_eval = np.linspace(0, 1, density)

        self.name = name

        self.color = color

        self.flipped = flipped

        self.curve = curve

        self.path_curve = path_curve

        old_curve_offset = Offset(self.curve.offset.x, self.curve.offset.y, self.curve.offset.z)

        old_path_offset = Offset(self.path_curve.offset.x, self.path_curve.offset.y, self.path_curve.offset.z)

        self.curve.P_u = self.translate(self.curve.P_u, Offset(-1 * self.curve.offset.x, -1 * self.curve.offset.y, -1 * self.curve.offset.z))

        self.path_curve.P_u = self.translate(self.path_curve.P_u, Offset(-1 * self.path_curve.offset.x, -1 * self.path_curve.offset.y, -1 * self.path_curve.offset.z))

        # after translating to origin

        curve_at_0 = self.curve.generate_trace()

        path_at_0 = self.path_curve.generate_trace()

        axes.plot(curve_at_0[:, 0], curve_at_0[:, 1], curve_at_0[:, 2], color='purple', label='curve at 0')

        axes.plot(path_at_0[:, 0], path_at_0[:, 1], path_at_0[:, 2], color='red', label='path at 0')

        self.S_u_w = self.sweep(self.curve.P_u, self.path_curve.P_u, self.flipped)

        self.S_u_w = self.translate(self.S_u_w, old_path_offset)

        self.curve.P_u = self.translate(self.curve.P_u, old_curve_offset)

        self.path_curve.P_u = self.translate(self.path_curve.P_u, old_path_offset)


    def sweep(self, curve, path, flipped):
        path = path.subs(self.u, self.w)

        t_mag = sp.sqrt(sp.diff(path)[0]**2 + sp.diff(path)[1]**2 + sp.diff(path)[2]**2)
        t_w = sp.diff(path) / t_mag

        Theta_w = sp.acos((sp.Matrix([[0, 1, 0]]) * t_w.T)[0])

        if flipped:
            T_theta = sp.Matrix([[sp.cos(Theta_w), -sp.sin(Theta_w), 0],
                        [sp.sin(Theta_w), sp.cos(Theta_w), 0],
                        [0, 1, 1]])
        else:
            T_theta = sp.Matrix([[sp.cos(Theta_w), sp.sin(Theta_w), 0],
                        [-sp.sin(Theta_w), sp.cos(Theta_w), 0],
                        [0, 1, 1]])

        S_u_w = sp.Matrix([T_theta * curve.T]).T + path

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

    p0 = sp.Matrix([[-100, -100, 0]])
    p1 = sp.Matrix([[-100, 100, 0]])

    q0 = sp.Matrix([[100, -100, 0]])
    q1 = sp.Matrix([[100, 100, 0]])

    pathPlane = SketchPlane('plane', 'xy', 40, p0, p1, q0, q1)

    pathPlane.translate(Offset(0, 0, 10))

    myPath = BezierCurve("axis", sp.Matrix([[0, 0, 0], [1, 3, 0], [2, 0.5, 0], [3, 2, 0]]), 40, pathPlane)

    p0 = sp.Matrix([[-100, 0, -100]])
    p1 = sp.Matrix([[-100, 0, 100]])

    q0 = sp.Matrix([[100, 0, -100]])
    q1 = sp.Matrix([[100, 0, 100]])

    curvePlane = SketchPlane('plane', 'xz', 40, p0, p1, q0, q1)

    curvePlane.translate(Offset(0, -3, 0))

    myCurve = BezierCurve("bezier", sp.Matrix([[0, 0, 0,], [-1, 0, 3], [-2, 0, 0.5], [-3, 0, 2]]), 40, curvePlane)

    mySweptSurface = SweptSurface("surface 1", myCurve, myPath, axes, flipped=True)

    sweptSurfaceEval = mySweptSurface.generate_traces()

    curveFromSurf = mySweptSurface.curve.generate_trace()

    pathFromSurf = mySweptSurface.path_curve.generate_trace()

    for trace in sweptSurfaceEval:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=mySweptSurface.color)

    axes.plot(curveFromSurf[:, 0], curveFromSurf[:, 1], curveFromSurf[:, 2], label='curve')

    axes.plot(pathFromSurf[:, 0], pathFromSurf[:, 1], pathFromSurf[:, 2], label='path')

    axes.set_xlabel('X')

    axes.set_ylabel('Y')

    axes.set_zlabel('Z')

    plt.legend()

    plt.show()