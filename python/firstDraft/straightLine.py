import sympy as sp
import matplotlib.pyplot as plt
import numpy as np
from CADUtils import Offset

from sketchPlane import SketchPlane

class StraightLine:
    def __init__(self, name, p0, p1, density, sketchPlane : SketchPlane, color='blue'):
        self.name = name

        self.color = color

        self.sketch_plane = sketchPlane

        self.alpha = sketchPlane.alpha

        self.beta = sketchPlane.beta
        
        self.gamma = sketchPlane.gamma

        self.offset = sketchPlane.offset

        self.density = density

        self.normal_vector = sketchPlane.normal_vector

        self.u = sp.symbols('u')

        self.U = sp.Matrix([[self.u, 1]])

        self.Nsl = sp.Matrix([[0, 1], [1, 1]]) ** -1

        self.Gsl = sp.Matrix([p0, p1])

        self.P_u = self.U * self.Nsl * self.Gsl

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
    p0 = sp.Matrix([[0, 0, 0]])

    p1 = sp.Matrix([[10, 0, 0]])

    p0 = sp.Matrix([[-100, -100, 0]])
    p1 = sp.Matrix([[-100, 100, 0]])

    q0 = sp.Matrix([[100, -100, 0]])
    q1 = sp.Matrix([[100, 100, 0]])

    myPlane = SketchPlane('plane', 'xy', 40, p0, p1, q0, q1)

    myLine = StraightLine('my line', myPlane, p0, p1, 40)

    myLine.rotate(0, 0, 0)

    myLine.translate(Offset(4, 0, 0))

    myLine_eval = myLine.generate_trace()

    figure = plt.figure()

    axes = figure.add_subplot()

    axes.plot(myLine_eval[:, 0], myLine_eval[:, 1])

    axes.set_xlim((-10, 10))

    axes.set_ylim((-10, 10))

    plt.show()
