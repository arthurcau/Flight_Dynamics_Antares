import sys

with open("source/antares_fd/simulation/monte_carlo_failure.py", "r") as f:
    content = f.read()

content = content.replace("y_full = np.concatenate((flt_nom.y[:idx_200+1, 1], flt_fail.y[:, 1]))", "y_full = np.concatenate((flt_nom.y[:idx_200+1, 1], flt_fail.y[:, 1]))\n            z_full = np.concatenate((flt_nom.z[:idx_200+1, 1], flt_fail.z[:, 1]))")

with open("source/antares_fd/simulation/monte_carlo_failure.py", "w") as f:
    f.write(content)
