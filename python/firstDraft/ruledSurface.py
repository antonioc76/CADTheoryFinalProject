import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

class RuledSurface:
    def __init__(self, density, p0, p1, q0, q1):
        u = sp.symbols('u')
        w = sp.symbols('w')

        U = sp.Matrix([[u, 1]])
        W = sp.Matrix([w, 1])

        self.u_eval = np.linspace(0, 1, density)
        self.w_eval = np.linspace(0, 1, density)

        self.Nsl = sp.Matrix([[0, 1],
                         [1, 1]]) ** -1
        
        self.Gsl1 = sp.Matrix([p0, p1, 0])

        self.Gsl2 = sp.Matrix([q0, q1, 10])

        self.P_u = U * self.Nsl * self.Gsl1
        self.Q_u = W * self.Nsl * self.Gsl2

        self.S_u_w = (1 - w) * self.P_u + w * self.Q_u 
        self.S_u_w_callable = sp.lambdify([u, w], self.S_u_w)

        self.S_u_w_lines = []

    def generate_traces(self):
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

    myPlane = RuledSurface(40, 0, 10, 20, 30)

    lines = myPlane.generate_traces()

    for line in lines:
        axes.plot(line[:, 0], line[:, 1], line[:, 2], color='blue')

    axes.show()


        

