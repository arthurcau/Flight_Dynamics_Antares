with open("projects/neblina_1/motors/Yaripo_teste_est_2_2.eng", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('Yaripo'):
        # update burn time in header
        parts = line.strip().split()
        parts[5] = "6.586"
        new_lines.append(" ".join(parts) + "\n")
    elif line.startswith(';'):
        new_lines.append(line)
    else:
        parts = line.strip().split()
        if len(parts) == 2:
            t = float(parts[0])
            T = float(parts[1])
            if t >= 1.691:
                new_t = t - 1.691
                new_lines.append(f"{new_t:.3f} {T:.2f}\n")

with open("projects/neblina_1/motors/Yaripo_teste_est_2_2.eng", "w") as f:
    f.writelines(new_lines)
