import numpy as np
thrust_data = np.loadtxt('projects/neblina_1/motors/Yaripo_teste_est_2_2.eng', skiprows=2)
diff = np.diff(thrust_data[:, 0])
print(diff.min())
if diff.min() <= 0:
    idx = np.argmin(diff)
    print("Zero or negative diff at index:", idx, "values:", thrust_data[idx:idx+2, 0])
