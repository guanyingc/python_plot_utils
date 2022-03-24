import numpy as np

x = np.linspace(0, 2, 20)
linear = x
quadratic = x**2
cubic = x**3
np.savetxt('data/linear.txt', np.stack([x, linear]).T, fmt='%0.6f')
np.savetxt('data/quadratic.txt', np.stack([x, quadratic]).T, fmt='%0.6f')
np.savetxt('data/cubic.txt', np.stack([x, cubic]).T, fmt='%0.6f')
