import numpy as np
thrust_data = np.loadtxt('projects/neblina_1/motors/Yaripo_teste_est_2_2.eng', skiprows=2)
print("Contains NaNs:", np.isnan(thrust_data).any())
print("Contains Infs:", np.isinf(thrust_data).any())
print(thrust_data)
