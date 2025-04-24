import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

from CADUtils import Offset

class SketchPlane:
    def __init__(self, name, initial_orientation, density, p0:sp.Matrix, p1:sp.Matrix, q0:sp.Matrix, q1:sp.Matrix, alpha=0, beta=0, gamma=0, offset=Offset(0, 0, 0), color='blue'):
        self.name = name
        self.initial_orientation = initial_orientation
        self.density = density
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        self.offset = offset

        self.color = color

        self.u = sp.symbols('u')
        self.w = sp.symbols('w')

        U = sp.Matrix([[self.u, 1]])
        W = sp.Matrix([[self.w, 1]])

        self.u_eval = np.linspace(0, 1, self.density)
        self.w_eval = np.linspace(0, 1, self.density)
        
        match self.initial_orientation:
            case 'xy':
                normal_vector_endpoint = sp.Matrix([[0, 0, 1]])
            case 'yz':
                normal_vector_endpoint = sp.Matrix([[1, 0, 0]])
            case 'xz':
                normal_vector_endpoint = sp.Matrix([[0, 1, 0]])
        
        self.Nsl = sp.Matrix([[0, 1],
                         [1, 1]]) ** -1
        
        self.Gsl_normal_vector = sp.Matrix([[0, 0, 0],
                                            normal_vector_endpoint])
        
        self.normal_vector = U * self.Nsl * self.Gsl_normal_vector

        sp.pretty_print(self.normal_vector)
        
        self.Gsl1 = sp.Matrix([p0, p1])

        self.Gsl2 = sp.Matrix([q0, q1])

        self.P_u = U * self.Nsl * self.Gsl1
        self.Q_u = U * self.Nsl * self.Gsl2

        self.P_u_callable = sp.lambdify(self.u, self.P_u)
        self.P_eval = self.evaluate(self.P_u_callable)

        self.Q_u_callable = sp.lambdify(self.u, self.Q_u)
        self.Q_eval = self.evaluate(self.Q_u_callable)

        self.S_u_w = (1 - self.w) * self.P_u + self.w * self.Q_u

        self.translate(self.offset)
        self.rotate(self.alpha, self.beta, self.gamma)
         
        self.S_u_w_callable = sp.lambdify([self.u, self.w], self.S_u_w)

        self.S_u_w_lines = []
    

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
    

    def generate_normal_vector_trace(self, magnitude):
        Psl_normal_vector_callable = sp.lambdify(self.u, self.normal_vector)
        
        Psl_normal_vector_eval = self.evaluate(Psl_normal_vector_callable)

        return(Psl_normal_vector_eval)
    

    def evaluate(self, P):
        u_eval = np.linspace(0, 1, self.density)
        P_eval = np.empty((0, 3))

        for i in range(len(u_eval)):
            point = P(u_eval[i])
            P_eval = np.append(P_eval, point, axis=0)

        return P_eval
    

    def translate(self, offset=Offset(0, 0, 0)):
        offset = offset.subtract(self.offset)
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

        self.offset = self.offset.add(offset)


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

    
if __name__ == "__main__":
    figure = plt.figure()
    axes = figure.add_subplot(projection='3d')

    p0 = sp.Matrix([[0, 0, 0]])
    p1 = sp.Matrix([[0, 100, 0]])

    q0 = sp.Matrix([[100, 0, 0]])
    q1 = sp.Matrix([[100, 100, 0]])

    myPlane = SketchPlane("myPlane", "xy", 40, p0, p1, q0, q1, 0, 0, 0, offset=Offset(0, 0, 0), color='red')

    myPlane2 = SketchPlane("myPlane", "xy", 40, p0, p1, q0, q1, 0, 0, 0, offset=Offset(0, 0, 0), color='red')

    myPlane.translate(offset=Offset(0, 10, 0))

    myPlane.translate(offset=Offset(0, 0, 10))

    myPlane2.translate(offset=Offset(0, 0, 50))

    myPlane.offset.print()
    
    myPlane2.offset.print()

    myPlane.rotate(-30, 0, 0)

    lines = myPlane.generate_traces()

    lines2 = myPlane2.generate_traces()

    for line in lines:
        axes.plot(line[:, 0], line[:, 1], line[:, 2], color=myPlane.color)

    for line in lines2:
        axes.plot(line[:, 0], line[:, 1], line[:, 2], color=myPlane.color)

    normal_vector_trace = myPlane.generate_normal_vector_trace(10)

    axes.plot(normal_vector_trace[:, 0], normal_vector_trace[:, 1], normal_vector_trace[:, 2])

    axes.set_xlim((0, 100))
    axes.set_ylim((0, 100))
    axes.set_zlim((0, 100))

    axes.set_xlabel("X")
    axes.set_ylabel("Y")
    axes.set_zlabel("Z")

    plt.show()


        

