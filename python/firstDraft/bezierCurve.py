import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

from CADUtils import Offset

from sketchPlane import SketchPlane

class BezierCurve:
    def __init__(self, name, controlPoints, density, sketchPlane : SketchPlane, color='blue'):
        self.name = name

        self.color = color

        self.density = density

        self.sketch_plane = sketchPlane

        self.normal_vector = sketchPlane.normal_vector

        self.alpha = sketchPlane.alpha

        self.beta = sketchPlane.beta

        self.gamma = sketchPlane.gamma

        self.offset = sketchPlane.offset

        print(f"offset in bezier curve {self.name}")

        self.offset.print()

        self.u = sp.symbols('u')

        num = controlPoints.rows
        match num:
            case 3:
                self.U = sp.Matrix([[self.u**2, self.u, 1]])
                self.Nspl = sp.Matrix([[1, -2, 1], [-2, 2, 0], [1, 0, 0]])
            case 4:
                self.U = sp.Matrix([[self.u**3, self.u ** 2, self.u, 1]])
                self.Nspl = sp.Matrix([[-1, 3, -3, 1], [3, -6, 3, 0], [-3, 3, 0, 0], [1, 0, 0, 0]])
            case 5:
                self.U = sp.Matrix([[self.u**4, self.u**3, self.u**2, self.u, 1]])
                self.Nspl = sp.Matrix([[1, -4, 6, -4, 1], [-4, 12, -12, 4, 0], [6, -12, 6, 0, 0], [-4, 4, 0, 0, 0], [1, 0, 0, 0, 0]])

        self.Gsl = controlPoints

        self.P_u = self.U * self.Nspl * self.Gsl

        self.translate(self.offset)

        self.rotate(self.alpha, self.beta, self.gamma)


    def generate_trace(self):
        P = sp.lambdify(self.u, self.P_u)

        u_eval = np.linspace(0, 1, self.density)
        P_eval = np.empty((0, 3))

        for i in range(len(u_eval)):
            point = P(u_eval[i])
            P_eval = np.append(P_eval, point, axis=0)

        return P_eval
    

    def translate(self, offset=Offset(0, 0, 0)):
        print("translating line")
        print(f"offset: {offset.x}, {offset.y}, {offset.z}")

        # offset.subtract(self.offset)
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
        
        P_u_h = self.P_u.T.row_insert(self.P_u.T.rows, sp.Matrix([1]))

        P_u_h_transformed = self.Tx * self.Ty * self.Tz * P_u_h

        self.P_u = P_u_h_transformed[:-1, :].T

        # self.offset.add(offset)

        # normal vector

        # normal_vector_h = self.normal_vector.T.row_insert(self.normal_vector.T.rows, sp.Matrix([1]))

        # normal_vector_h_transformed = self.Tx * self.Ty * self.Tz * normal_vector_h

        # self.normal_vector = normal_vector_h_transformed[:-1, :].T


    def rotate(self, alpha, beta, gamma):
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

        P_u_h = self.P_u.T.row_insert(self.P_u.T.rows, sp.Matrix([1]))

        P_u_h_transformed = self.Trz * self.Try * self.Trx * P_u_h
        
        self.P_u = P_u_h_transformed[:-1, :].T

        # normal vector

        # normal_vector_h = self.normal_vector.T.row_insert(self.normal_vector.T.rows, sp.Matrix([1]))

        # normal_vector_h_transformed = self.Trz * self.Try * self.Trx * normal_vector_h

        # self.normal_vector = normal_vector_h_transformed[:-1, :].T


if __name__ == "__main__":
    cps = sp.Matrix([[-20, 0, -30], [0, 0, 30], [20, 0, 0], [50, 0, 30], [60, 0, -20]])

    sp.pretty_print(cps)

    myBezierCurve = BezierCurve("bezier 1", cps, 40)

    # mySpline.rotate(0, 0, 180)

    # mySpline.translate(Offset(3, 2, 0))

    trace = myBezierCurve.generate_trace()

    figure = plt.figure()

    axes = figure.add_subplot()

    axes.plot(trace[:, 0], trace[:, 2])

    axes.plot(cps[:, 0], cps[:, 2], color='red', linestyle='--')

    axes.scatter(cps[:, 0], cps[:, 2], color='red')

    axes.set_xlim((-100, 100))

    axes.set_ylim((-100, 100))

    plt.show()