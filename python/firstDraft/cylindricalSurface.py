import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

from sketchPlane import SketchPlane

from straightLine import StraightLine
from spline import Spline
from bezierCurve import BezierCurve

from CADUtils import Offset

class CylindricalSurface:
    def __init__(self, name, curve, density=40, color='green'):
        print('init surface')

        self.name = name

        self.curve = curve

        self.color = color

        self.offset = self.curve.offset

        self.normal_vector = curve.normal_vector

        self.u_eval = np.linspace(0, 1, density)

        self.w_eval = np.linspace(0, 1, density)

        self.u = sp.symbols('u')

        self.w = sp.symbols('w')

        self.P_u = self.curve.P_u - sp.Matrix([[self.offset.x, self.offset.y, self.offset.z]])

        self.Q_w = self.curve.normal_vector.subs(self.u, self.w)


        print('p_u')
        sp.pretty_print(self.P_u)
        print('q_w')
        sp.pretty_print(self.Q_w)

        self.S_u_w = self.P_u + self.Q_w

        sp.pretty_print(self.S_u_w)

        self.S_u_w_callable = sp.lambdify([self.u, self.w], self.S_u_w)

        self.S_u_w_lines = []


    def scale_q(self, scaler):
        print("scale_q")
        print(f"offset: {self.curve.offset.x}, {self.curve.offset.y}, {self.curve.offset.z}")

        sp.pretty_print(self.S_u_w)

        self.rotate_q(-1 * self.curve.alpha, -1 * self.curve.beta, -1 * self.curve.gamma)

        self.translate_q(Offset(-1 * self.curve.offset.x, -1 * self.curve.offset.y, -1 * self.curve.offset.z))

        sp.pretty_print(self.S_u_w)

        # print("scaling")
        # translation matrices

        self.scale = sp.Matrix([[scaler, 0, 0, 0],
                        [0, scaler, 0, 0],
                        [0, 0, scaler, 0],
                        [0, 0, 0, 1]])

        # Q_w vector

        Q_w_h = self.Q_w.T.row_insert(self.Q_w.T.rows, sp.Matrix([1]))

        Q_w_h_transformed = self.scale * Q_w_h

        self.Q_w = Q_w_h_transformed[:-1, :].T

        # surface

        self.rotate_q(self.curve.alpha, self.curve.beta, self.curve.gamma)

        self.translate_q(Offset(self.curve.offset.x, self.curve.offset.y, self.curve.offset.z))

        self.S_u_w = self.P_u + self.Q_w

        # sp.pretty_print(self.S_u_w)


    def translate(self, offset=Offset(0, 0, 0)):
        offset.subtract(self.offset)
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
        
        S_u_w_h = self.S_u_w.T.row_insert(self.S_u_w.T.rows, sp.Matrix([1]))

        S_u_w_h_transformed = self.Tx * self.Ty * self.Tz * S_u_w_h

        self.S_u_w = S_u_w_h_transformed[:-1, :].T

        normal_vector_h = self.normal_vector.T.row_insert(self.normal_vector.T.rows, sp.Matrix([1]))

        normal_vector_h_transformed = self.Tx * self.Ty * self.Tz * normal_vector_h

        self.normal_vector = normal_vector_h_transformed[:-1, :].T

        self.offset.add(offset)


    def translate_q(self, offset=Offset(0, 0, 0)):
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
        
        Q_w_h = self.Q_w.T.row_insert(self.Q_w.T.rows, sp.Matrix([1]))

        Q_w_h_transformed = self.Tx * self.Ty * self.Tz * Q_w_h

        self.Q_w = Q_w_h_transformed[:-1, :].T

        self.S_u_w = self.P_u + self.Q_w

    
    def rotate_q(self, alpha, beta, gamma):
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
        
        Q_w_h = self.Q_w.T.row_insert(self.Q_w.T.rows, sp.Matrix([1]))

        Q_w_h_transformed = self.Trx * self.Try * self.Trz * Q_w_h

        self.Q_w = Q_w_h_transformed[:-1, :].T

        self.S_u_w = self.P_u + self.Q_w


    def rotate(self, alpha, beta, gamma):
        alpha = alpha - self.alpha
        beta = beta - self.beta
        gamma = gamma - self.gamma

        self.alpha += alpha
        self.beta += beta
        self.gamma += gamma

        # rotation matrices
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
        
        S_u_w_h = self.S_u_w.T.row_insert(self.S_u_w.T.rows, sp.Matrix([1]))

        S_u_w_h_transformed = self.Trz * self.Try * self.Trx * S_u_w_h
        
        self.S_u_w = S_u_w_h_transformed[:-1, :].T

        # normal vector

        normal_vector_h = self.normal_vector.T.row_insert(self.normal_vector.T.rows, sp.Matrix([1]))

        normal_vector_h_transformed = self.Trz * self.Try * self.Trx * normal_vector_h

        self.normal_vector = normal_vector_h_transformed[:-1, :].T

    
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

    p0 = sp.Matrix([[0, 0, 0]])

    p1 = sp.Matrix([[10, 0, 0]])

    # p0 = sp.Matrix([[-100, -100, 0]])
    # p1 = sp.Matrix([[-100, 100, 0]])

    # q0 = sp.Matrix([[100, -100, 0]])
    # q1 = sp.Matrix([[100, 100, 0]])

    p0 = sp.Matrix([[-100, 0, -100]])
    p1 = sp.Matrix([[-100, 0, 100]])

    q0 = sp.Matrix([[100, 0, -100]])
    q1 = sp.Matrix([[100, 0, 100]])

    myPlane = SketchPlane('plane', 'xz', 40, p0, p1, q0, q1)

    myPlane.translate(Offset(0, 10, 0))
    
    myPlane.rotate(30, 0, 0)

    cps = sp.Matrix([[-20, 0, -30], [0, 0, 30], [20, 0, 0], [50, 0, 30], [60, 0, -20]])

    myCurve = BezierCurve("bezier", cps, 40, myPlane)

    print(f"my curve")
    sp.pretty_print(myCurve.P_u)
    sp.pretty_print(myCurve.normal_vector)

    mySurface = CylindricalSurface('surface', myCurve)

    print(mySurface.curve.normal_vector)

    mySurface.scale_q(100)

    plane_eval = myPlane.generate_traces()

    curve_eval = myCurve.generate_trace()

    curve_eval_from_surface = mySurface.curve.generate_trace()

    surface_eval = mySurface.generate_traces()

    figure = plt.figure()

    axes = figure.add_subplot(projection='3d')

    axes.plot(curve_eval_from_surface[:, 0], curve_eval_from_surface[:, 1], curve_eval_from_surface[:, 2], color=myCurve.color)

    for line in plane_eval:
        axes.plot(line[:, 0], line[:, 1], line[:, 2], color=myPlane.color, alpha=0.1)

    for line in surface_eval:
        axes.plot(line[:, 0], line[:, 1], line[:, 2], color=mySurface.color)

    axes.set_xlim((-100, 100))
    axes.set_ylim((-100, 100))
    axes.set_zlim((-100, 100))

    axes.set_xlabel("X")
    axes.set_ylabel("Y")
    axes.set_zlabel("Z")

    plt.show()





