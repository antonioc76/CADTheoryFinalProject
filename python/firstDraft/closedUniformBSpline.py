import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

from CADUtils import Offset

from sketchPlane import SketchPlane

class SubCurve:
    def __init__(self, name, u, P_u, density, sketchPlane : SketchPlane):
        self.name = name
        self.u = u
        self.P_u = P_u
        self.density = density

        self.sketch_plane = sketchPlane

        self.offset = self.sketch_plane.offset

        self.alpha = self.sketch_plane.alpha

        self.beta = self.sketch_plane.beta

        self.gamma = self.sketch_plane.gamma

        self.normal_vector = sketchPlane.normal_vector

    
    def generate_trace(self):
        P = sp.lambdify(self.u, self.P_u)

        u_eval = np.linspace(0, 1, self.density)
        P_eval = np.empty((0, 3))

        for i in range(len(u_eval)):
            point = P(u_eval[i])
            P_eval = np.append(P_eval, point, axis=0)

        return P_eval



class ClosedUniformBSpline:
    def __init__(self, name, order, controlPoints, density, sketchPlane : SketchPlane, color='blue'):
            self.name = name

            self.color = color

            self.density = density

            self.sketch_plane = sketchPlane

            self.normal_vector = sketchPlane.normal_vector

            self.alpha = sketchPlane.alpha

            self.beta = sketchPlane.beta

            self.gamma = sketchPlane.gamma

            self.offset = sketchPlane.offset

            self.u = sp.symbols('u')

            num = controlPoints.rows

            match order:
                case 2:
                    self.U = sp.Matrix([[self.u**2, self.u, 1]])
                    self.M = 1/2 * sp.Matrix([[1, -2, 1], [-2, 2, 0], [1, 1, 0]])

                case 3:
                    self.U = sp.Matrix([[self.u**3, self.u ** 2, self.u, 1]])
                    self.M = 1/6 * sp.Matrix([[-1, 3, -3, 1],
                            [3, -6, 3, 0],
                            [-3, 0, 3, 0],
                            [1, 4, 1, 0]])
                case 4:
                    self.U = sp.Matrix([[self.u**4, self.u**3, self.u**2, self.u, 1]])
                    self.M = 1/24 * sp.Matrix([[1, -4, 6, -4, 1], [-4, 12, -12, 4, 0], [6, -12, 6, 0, 0], [-4, 4, 0, 0, 0], [1, 0, 0, 0, 0]])

            G = controlPoints

            n = G.rows - 1
            
            self.curves = []
            idxs = []

            for i in range(1, n+2): # exclusive end, increment 1 from formula
                idxs = []
                for j in range(order+1):
                    idx = (i-1 + j) % (n+1)
                    print(idx)
                    idxs.append(idx)

                Gsub = sp.zeros(order+1, 3)
                for j, idx in enumerate(idxs):
                    p = G[idx, :]
                    Gsub[j, :] = p

                sp.pretty_print(Gsub)

                P_u = self.U * self.M * Gsub
                curve = SubCurve(f"{self.name} sub-curve{i}", self.u, P_u, self.density, sketchPlane=self.sketch_plane)
                self.curves.append(curve)

            self.translate(self.offset)

            self.rotate(self.alpha, self.beta, self.gamma)

            
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
        
        for i, curve in enumerate(self.curves):
            P_u_h = curve.P_u.T.row_insert(curve.P_u.T.rows, sp.Matrix([1]))

            P_u_h_transformed = self.Tx * self.Ty * self.Tz * P_u_h

            self.curves[i].P_u = P_u_h_transformed[:-1, :].T


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

        for i, curve in enumerate(self.curves):
            P_u_h = curve.P_u.T.row_insert(curve.P_u.T.rows, sp.Matrix([1]))

            P_u_h_transformed = self.Trz * self.Try * self.Trx * P_u_h
            
            self.curves[i].P_u = P_u_h_transformed[:-1, :].T

    
    def generate_traces(self):
        traces = []
        for curve in self.curves:
            print(type(curve))
            P = sp.lambdify(self.u, curve.P_u)

            u_eval = np.linspace(0, 1, self.density)
            trace = np.empty((0, 3))

            for i in range(len(u_eval)):
                point = P(u_eval[i])
                trace = np.append(trace, point, axis=0)

            traces.append(trace)
        
        return traces


if __name__ == "__main__":
    p0 = sp.Matrix([[-100, -100, 0]])
    p1 = sp.Matrix([[-100, 100, 0]])

    q0 = sp.Matrix([[100, -100, 0]])
    q1 = sp.Matrix([[100, 100, 0]])

    myPlane = SketchPlane('plane', 'xz', 40, p0, p1, q0, q1)

    myPlane.translate(Offset(0, 0, 10))

    myPlane.rotate(30, 0, 0)

    controlPoints = sp.Matrix([[-100, 100, 0],
                                [-100, 300, 0],
                                [0, 400, 0],
                                [100, 300, 0],
                                [100, 100, 0],
                                [0, 0, 0]])
    
    myCUBSpline = ClosedUniformBSpline("CUBSpline1", 3, controlPoints, 10, myPlane)

    traces = myCUBSpline.generate_traces()

    figure = plt.figure()

    axes = figure.add_subplot(projection='3d')

    for trace in traces:
        axes.plot(trace[:, 0], trace[:, 1], trace[:, 2], color=myCUBSpline.color)

    axes.set_xlim((-100, 100))

    axes.set_ylim((-100, 100))

    axes.set_zlim((-100, 100))

    plt.show()
        
    