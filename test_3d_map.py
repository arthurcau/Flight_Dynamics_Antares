import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# create a dummy image (e.g. 10x10)
img = np.random.rand(10, 10, 3)

# define the X, Y plane bounds
x = np.linspace(-100, 100, 10)
y = np.linspace(-100, 100, 10)
X, Y = np.meshgrid(x, y)
Z = np.zeros_like(X)

# You can't easily plot an image natively as a surface in matplotlib without doing facecolors
ax.plot_surface(X, Y, Z, facecolors=img, rstride=1, cstride=1)
ax.plot([0, 10, 50], [0, 10, 50], [0, 500, 0])
plt.savefig("test_map.pdf")
